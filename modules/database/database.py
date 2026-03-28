"""
Modulo per la gestione del database delle targhe autorizzate
"""

try:
    import sqlite3
    from datetime import datetime, date
    from typing import List, Dict, Optional, Tuple
    import modules.database.config as config
    import os
except ImportError as e:
    print(f"Errore nel caricamento dei moduli in database.py: {e}")


class DatabaseManager:

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = config.DATABASE_PATH
        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

        cursor = self.connection.cursor()

        # ── Tabella persone ──────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name  TEXT NOT NULL,
                role       TEXT NOT NULL,
                notes      TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Tabella targhe (solo dati specifici della targa) ─────────────────
        # Non duplica nome/cognome/ruolo: quelli stanno in persons.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorized_plates (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number    TEXT NOT NULL UNIQUE,
                person_id       INTEGER NOT NULL,
                expiration_date DATE DEFAULT '',
                notes           TEXT DEFAULT '',
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
            )
        """)

        # ── Tabella log accessi ───────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status       TEXT NOT NULL,
                event        TEXT NOT NULL
            )
        """)

        # Indici
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plate_number ON authorized_plates(plate_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expiration    ON authorized_plates(expiration_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_ts     ON access_log(timestamp)")

        self.connection.commit()
        print(f"✅ Database inizializzato: {self.db_path}")

    # ── Vista comoda: targa + dati persona ────────────────────────────────────

    def _plate_with_person(self, where: str = "", params: tuple = ()) -> str:
        """Query base che restituisce la targa arricchita con i dati della persona."""
        return f"""
            SELECT
                ap.id,
                ap.plate_number,
                ap.person_id,
                ap.expiration_date,
                ap.notes,
                ap.created_at,
                ap.updated_at,
                p.first_name,
                p.last_name,
                p.role
            FROM authorized_plates ap
            JOIN persons p ON ap.person_id = p.id
            {where}
        """

    # ========================================================================
    # GESTIONE TARGHE
    # ========================================================================

    def get_all_plates(self) -> List[Dict]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(self._plate_with_person() + " ORDER BY ap.plate_number")
            plates = [dict(row) for row in cursor.fetchall()]
            print(f"✅ Targhe trovate: {len(plates)}")
            return plates
        except Exception as e:
            print(f"❌ Errore recupero targhe: {e}")
            return []

    def get_plate(self, plate_number: str) -> Optional[Dict]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                self._plate_with_person("WHERE ap.plate_number = ?"),
                (plate_number.upper().strip(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"❌ Errore recupero targa: {e}")
            return None

    def get_plate_by_number(self, plate_number: str) -> Optional[Dict]:
        return self.get_plate(plate_number)

    def add_authorized_plate(
        self,
        plate_number: str,
        first_name: str,
        last_name: str,
        role: str,
        expiration_date: str = "",
        notes: str = "",
    ) -> bool:
        """
        Compatibilità con il vecchio schema: crea automaticamente la persona
        se non esiste, poi aggiunge la targa.
        """
        try:
            plate_number = plate_number.upper().strip()
            # Cerca persona esistente o creane una nuova
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id FROM persons WHERE first_name=? AND last_name=? AND role=?",
                (first_name.strip(), last_name.strip(), role.strip())
            )
            row = cursor.fetchone()
            if row:
                person_id = row["id"]
            else:
                person_id = self.add_person(first_name, last_name, role)
                if person_id < 0:
                    return False

            cursor.execute(
                """
                INSERT INTO authorized_plates (plate_number, person_id, expiration_date, notes)
                VALUES (?, ?, ?, ?)
                """,
                (plate_number, person_id, expiration_date, notes),
            )
            self.connection.commit()
            print(f"✅ Targa aggiunta: {plate_number}")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Targa {plate_number} già presente")
            return False
        except Exception as e:
            print(f"❌ Errore aggiunta targa: {e}")
            return False

    def update_plate(self, plate_number: str, expiration_date: str = "",
                     notes: str = "", new_plate_number: str = None):
        """Aggiorna scadenza e note. Se new_plate_number è fornito, rinomina anche la targa."""
        plate_number = plate_number.upper().strip()
        cursor = self.connection.cursor()

        if new_plate_number:
            new_plate_number = new_plate_number.upper().strip()
            if new_plate_number != plate_number:
                try:
                    cursor.execute(
                        """
                        UPDATE authorized_plates
                        SET plate_number=?, expiration_date=?, notes=?, updated_at=CURRENT_TIMESTAMP
                        WHERE plate_number=?
                        """,
                        (new_plate_number, expiration_date, notes, plate_number),
                    )
                    self.connection.commit()
                    return
                except sqlite3.IntegrityError:
                    raise ValueError(f"La targa {new_plate_number} esiste già nel database.")

        cursor.execute(
            """
            UPDATE authorized_plates
            SET expiration_date=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE plate_number=?
            """,
            (expiration_date, notes, plate_number),
        )
        self.connection.commit()

    def remove_plate(self, plate_number: str) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM authorized_plates WHERE plate_number = ?",
                (plate_number.upper().strip(),)
            )
            self.connection.commit()
            if cursor.rowcount > 0:
                print(f"✅ Targa rimossa: {plate_number}")
                return True
            print(f"⚠️ Targa non trovata: {plate_number}")
            return False
        except Exception as e:
            print(f"❌ Errore rimozione targa: {e}")
            return False

    def get_all_valid_plates(self) -> List[str]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT plate_number FROM authorized_plates
                WHERE expiration_date = '' OR expiration_date >= date('now')
                ORDER BY plate_number
            """)
            return [row["plate_number"] for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Errore recupero targhe valide: {e}")
            return []

    # ========================================================================
    # VERIFICA AUTORIZZAZIONI
    # ========================================================================

    def is_plate_authorized(self, plate_number: str) -> Tuple[bool, Optional[Dict]]:
        try:
            plate_number = plate_number.upper().strip()
            plate_info = self.get_plate(plate_number)

            if not plate_info:
                return False, None

            exp = plate_info.get("expiration_date", "")
            if exp and exp.strip():
                try:
                    exp_date = datetime.strptime(exp.strip(), "%Y-%m-%d").date()
                    if exp_date < date.today():
                        print(f"⚠️ Targa {plate_number} SCADUTA")
                        plate_info["status"] = "expired"
                        return False, plate_info
                except ValueError:
                    pass  # data malformata → considera valida

            plate_info["status"] = "valid"
            return True, plate_info

        except Exception as e:
            print(f"❌ Errore verifica targa: {e}")
            return False, None

    # ========================================================================
    # GESTIONE PERSONE
    # ========================================================================

    def add_person(self, first_name: str, last_name: str, role: str, notes: str = "") -> int:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO persons (first_name, last_name, role, notes) VALUES (?, ?, ?, ?)",
                (first_name.strip(), last_name.strip(), role.strip(), notes.strip()),
            )
            self.connection.commit()
            pid = cursor.lastrowid
            print(f"✅ Persona aggiunta: {first_name} {last_name} (id={pid})")
            return pid
        except Exception as e:
            print(f"❌ Errore aggiunta persona: {e}")
            return -1

    def get_all_persons(self) -> List[Dict]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM persons ORDER BY last_name, first_name")
            persons = [dict(row) for row in cursor.fetchall()]
            for person in persons:
                cursor.execute(
                    """
                    SELECT id, plate_number, expiration_date, notes, created_at, updated_at
                    FROM authorized_plates WHERE person_id = ? ORDER BY plate_number
                    """,
                    (person["id"],),
                )
                person["plates"] = [dict(r) for r in cursor.fetchall()]
            return persons
        except Exception as e:
            print(f"❌ Errore recupero persone: {e}")
            return []

    def get_person(self, person_id: int) -> Optional[Dict]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
            row = cursor.fetchone()
            if not row:
                return None
            person = dict(row)
            cursor.execute(
                """
                SELECT id, plate_number, expiration_date, notes, created_at, updated_at
                FROM authorized_plates WHERE person_id = ? ORDER BY plate_number
                """,
                (person_id,),
            )
            person["plates"] = [dict(r) for r in cursor.fetchall()]
            return person
        except Exception as e:
            print(f"❌ Errore recupero persona: {e}")
            return None

    def update_person(self, person_id: int, first_name: str, last_name: str, role: str, notes: str = "") -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE persons SET first_name=?, last_name=?, role=?, notes=? WHERE id=?",
                (first_name.strip(), last_name.strip(), role.strip(), notes.strip(), person_id),
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Errore aggiornamento persona: {e}")
            return False

    def delete_person(self, person_id: int) -> bool:
        """Elimina la persona; le targhe collegate vengono rimosse per CASCADE."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM persons WHERE id = ?", (person_id,))
            self.connection.commit()
            ok = cursor.rowcount > 0
            if ok:
                print(f"✅ Persona {person_id} eliminata (CASCADE sulle targhe)")
            return ok
        except Exception as e:
            print(f"❌ Errore eliminazione persona: {e}")
            return False

    def add_plate_to_person(self, person_id: int, plate_number: str, expiration_date: str = "", notes: str = "") -> bool:
        try:
            if not self.get_person(person_id):
                return False
            plate_number = plate_number.upper().strip()
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO authorized_plates (plate_number, person_id, expiration_date, notes)
                VALUES (?, ?, ?, ?)
                """,
                (plate_number, person_id, expiration_date, notes),
            )
            self.connection.commit()
            print(f"✅ Targa {plate_number} aggiunta a persona {person_id}")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Targa {plate_number} già presente")
            return False
        except Exception as e:
            print(f"❌ Errore aggiunta targa a persona: {e}")
            return False

    def search_persons(self, query: str) -> List[Dict]:
        try:
            cursor = self.connection.cursor()
            q = f"%{query.strip()}%"
            cursor.execute(
                "SELECT * FROM persons WHERE first_name LIKE ? OR last_name LIKE ? ORDER BY last_name, first_name",
                (q, q),
            )
            persons = [dict(row) for row in cursor.fetchall()]
            for person in persons:
                cursor.execute(
                    """
                    SELECT id, plate_number, expiration_date, notes, created_at, updated_at
                    FROM authorized_plates WHERE person_id = ? ORDER BY plate_number
                    """,
                    (person["id"],),
                )
                person["plates"] = [dict(r) for r in cursor.fetchall()]
            return persons
        except Exception as e:
            print(f"❌ Errore ricerca persone: {e}")
            return []

    # ========================================================================
    # LOG ACCESSI
    # ========================================================================

    def log_access(self, plate_number: str, status: str, event: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO access_log (plate_number, status, event) VALUES (?, ?, ?)",
                (plate_number, status, event),
            )
            self.connection.commit()
        except Exception as e:
            print(f"❌ Errore log accesso: {e}")

    def get_access_history(
        self, plate_number: str = None, limit: int = 10_000_000,
        date: str = None, status: str = None
    ) -> List[Dict]:
        try:
            cursor = self.connection.cursor()
            base = """
                SELECT al.*, p.first_name, p.last_name, p.role
                FROM access_log al
                LEFT JOIN authorized_plates ap ON al.plate_number = ap.plate_number
                LEFT JOIN persons p ON ap.person_id = p.id
            """
            conds, params = [], []
            if plate_number and plate_number.strip():
                conds.append("al.plate_number = ?"); params.append(plate_number.upper().strip())
            if date and date.strip():
                conds.append("date(al.timestamp) = ?"); params.append(date)
            if status and status.strip():
                conds.append("al.status = ?"); params.append(status)
            if conds:
                base += " WHERE " + " AND ".join(conds)
            base += " ORDER BY al.timestamp DESC LIMIT ?"
            params.append(limit)
            cursor.execute(base, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Errore recupero storico: {e}")
            return []

    def get_access_history_advanced(
        self,
        plate_number: str = None, first_name: str = None, last_name: str = None,
        role: str = None, status: str = None, date_single: str = None,
        date_from: str = None, date_to: str = None, limit: int = 100,
    ) -> list:
        try:
            cursor = self.connection.cursor()
            base = """
                SELECT al.*, p.first_name, p.last_name, p.role
                FROM access_log al
                LEFT JOIN authorized_plates ap ON al.plate_number = ap.plate_number
                LEFT JOIN persons p ON ap.person_id = p.id
            """
            conds, params = [], []
            if plate_number and plate_number.strip():
                conds.append("al.plate_number = ?"); params.append(plate_number.upper().strip())
            if status and status.strip():
                conds.append("al.status = ?"); params.append(status.strip())
            if date_single and date_single.strip():
                conds.append("date(al.timestamp) = ?"); params.append(date_single.strip())
            else:
                if date_from and date_from.strip():
                    conds.append("date(al.timestamp) >= ?"); params.append(date_from.strip())
                if date_to and date_to.strip():
                    conds.append("date(al.timestamp) <= ?"); params.append(date_to.strip())
            if first_name and first_name.strip():
                conds.append("p.first_name LIKE ?"); params.append(f"%{first_name.strip()}%")
            if last_name and last_name.strip():
                conds.append("p.last_name LIKE ?"); params.append(f"%{last_name.strip()}%")
            if role and role.strip():
                conds.append("p.role LIKE ?"); params.append(f"%{role.strip()}%")
            if conds:
                base += " WHERE " + " AND ".join(conds)
            base += " ORDER BY al.timestamp DESC"
            if limit and limit > 0:
                base += " LIMIT ?"; params.append(limit)
            cursor.execute(base, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Errore storico avanzato: {e}")
            return []

    def delete_logs_by_ids(self, log_ids: list) -> int:
        try:
            if not log_ids:
                return 0
            placeholders = ",".join("?" * len(log_ids))
            cursor = self.connection.cursor()
            cursor.execute(f"DELETE FROM access_log WHERE id IN ({placeholders})", log_ids)
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"❌ Errore eliminazione log: {e}")
            return 0

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def get_accessi_per_giorno(self, start_date: str, end_date: str) -> list:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT date(timestamp) AS giorno, COUNT(*) AS count
                FROM access_log WHERE date(timestamp) BETWEEN ? AND ?
                GROUP BY giorno ORDER BY giorno
            """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ {e}"); return []

    def get_accessi_per_stato(self, start_date: str, end_date: str) -> dict:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) AS count FROM access_log
                WHERE date(timestamp) BETWEEN ? AND ? GROUP BY status
            """, (start_date, end_date))
            result = {"authorized": 0, "not_authorized": 0, "expired": 0}
            for row in cursor.fetchall():
                if row["status"] in result:
                    result[row["status"]] = row["count"]
            return result
        except Exception as e:
            print(f"❌ {e}"); return {"authorized": 0, "not_authorized": 0, "expired": 0}

    def get_accessi_per_ora(self, start_date: str, end_date: str) -> list:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS ora, COUNT(*) AS count
                FROM access_log WHERE date(timestamp) BETWEEN ? AND ?
                GROUP BY ora ORDER BY ora
            """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ {e}"); return []

    def get_top_targhe(self, start_date: str, end_date: str, limit: int = 10) -> list:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT plate_number, COUNT(*) AS count FROM access_log
                WHERE date(timestamp) BETWEEN ? AND ?
                GROUP BY plate_number ORDER BY count DESC LIMIT ?
            """, (start_date, end_date, limit))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ {e}"); return []

    def get_trend_per_stato(self, start_date: str, end_date: str) -> dict:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT date(timestamp) AS giorno, status, COUNT(*) AS count
                FROM access_log WHERE date(timestamp) BETWEEN ? AND ?
                AND status IN ('authorized','not_authorized')
                GROUP BY giorno, status ORDER BY giorno
            """, (start_date, end_date))
            result = {"authorized": [], "not_authorized": []}
            for row in cursor.fetchall():
                if row["status"] in result:
                    result[row["status"]].append({"giorno": row["giorno"], "count": row["count"]})
            return result
        except Exception as e:
            print(f"❌ {e}"); return {"authorized": [], "not_authorized": []}

    def get_kpi_entrate_uscite(self, start_date: str, end_date: str) -> dict:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN LOWER(event)='entrata' THEN 1 ELSE 0 END) AS entrate,
                    SUM(CASE WHEN LOWER(event)='uscita'  THEN 1 ELSE 0 END) AS uscite
                FROM access_log
                WHERE (status='authorized' OR status='exit')
                AND date(timestamp) BETWEEN ? AND ?
            """, (start_date, end_date))
            row = dict(cursor.fetchone())
            e, u = row.get("entrate") or 0, row.get("uscite") or 0
            return {"entrate": e, "uscite": u, "presenti": max(0, e - u)}
        except Exception as e:
            print(f"❌ {e}"); return {"entrate": 0, "uscite": 0, "presenti": 0}

    def get_distribuzione_entrate_uscite(self, start_date: str, end_date: str) -> dict:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN LOWER(event)='entrata' THEN 1 ELSE 0 END) AS entrate,
                    SUM(CASE WHEN LOWER(event)='uscita'  THEN 1 ELSE 0 END) AS uscite
                FROM access_log
                WHERE (status='authorized' OR status='exit')
                AND date(timestamp) BETWEEN ? AND ?
            """, (start_date, end_date))
            row = dict(cursor.fetchone())
            return {"entrate": row.get("entrate") or 0, "uscite": row.get("uscite") or 0}
        except Exception as e:
            print(f"❌ {e}"); return {"entrate": 0, "uscite": 0}

    def get_flusso_orario_entrate_uscite(self, start_date: str, end_date: str) -> list:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    CAST(strftime('%H', timestamp) AS INTEGER) AS ora,
                    SUM(CASE WHEN LOWER(event)='entrata' THEN 1 ELSE 0 END) AS entrate,
                    SUM(CASE WHEN LOWER(event)='uscita'  THEN 1 ELSE 0 END) AS uscite
                FROM access_log
                WHERE (status='authorized' OR status='exit')
                AND date(timestamp) BETWEEN ? AND ?
                GROUP BY ora ORDER BY ora
            """, (start_date, end_date))
            rows = {row["ora"]: dict(row) for row in cursor.fetchall()}
            return [{"ora": h, "entrate": rows.get(h,{}).get("entrate") or 0,
                     "uscite": rows.get(h,{}).get("uscite") or 0} for h in range(24)]
        except Exception as e:
            print(f"❌ {e}"); return [{"ora": h, "entrate": 0, "uscite": 0} for h in range(24)]

    def get_saldo_giornaliero(self, start_date: str, end_date: str) -> list:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    date(timestamp) AS giorno,
                    SUM(CASE WHEN LOWER(event)='entrata' THEN 1 ELSE 0 END) AS entrate,
                    SUM(CASE WHEN LOWER(event)='uscita'  THEN 1 ELSE 0 END) AS uscite
                FROM access_log
                WHERE (status='authorized' OR status='exit')
                AND date(timestamp) BETWEEN ? AND ?
                GROUP BY giorno ORDER BY giorno
            """, (start_date, end_date))
            result = []
            for row in cursor.fetchall():
                e, u = row["entrate"] or 0, row["uscite"] or 0
                result.append({"giorno": row["giorno"], "entrate": e, "uscite": u, "saldo": e - u})
            return result
        except Exception as e:
            print(f"❌ {e}"); return []

    def get_statistics(self) -> Dict:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM authorized_plates"); total = cursor.fetchone()["count"]
            cursor.execute("""
                SELECT COUNT(*) as count FROM authorized_plates
                WHERE expiration_date='' OR expiration_date IS NULL OR expiration_date >= date('now')
            """); valid = cursor.fetchone()["count"]
            cursor.execute("SELECT COUNT(*) as count FROM access_log WHERE date(timestamp)=date('now')"); today_acc = cursor.fetchone()["count"]
            cursor.execute("SELECT COUNT(*) as count FROM access_log WHERE timestamp >= date('now','-7 days')"); week_acc = cursor.fetchone()["count"]
            return {"total_plates": total, "valid_plates": valid, "expired_plates": total - valid,
                    "today_accesses": today_acc, "week_accesses": week_acc}
        except Exception as e:
            print(f"❌ {e}"); return {}

    def get_all_logs(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM access_log ORDER BY timestamp DESC")
        return cursor.fetchall()

    def clear_access_log(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM access_log")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ {e}"); return False

    def close(self):
        if self.connection:
            self.connection.close()
            print("✅ Database chiuso")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass