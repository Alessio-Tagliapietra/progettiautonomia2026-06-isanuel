"""
Modulo per la gestione del database delle targhe autorizzate
Supporta SQLite per semplicità e portabilità
"""

try:
    import sqlite3
    from datetime import datetime, date
    from typing import List, Dict, Optional, Tuple
    import server.config as config
    import os

except ImportError as e:
    print(f"Errore nel caricamento dei moduli in database.py: {e}")


class DatabaseManager:
    """Gestisce tutte le operazioni sul database delle targhe"""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        """
        Inizializza il database manager

        Args:
            db_path: percorso del file database SQLite
        """

        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        """Crea il database e le tabelle se non esistono"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Per accesso dict-like

        cursor = self.connection.cursor()

        # ===== Tabella principale autorizzazioni =====
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS authorized_plates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL UNIQUE,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT NOT NULL,
                expiration_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """
        )

        # ===== Tabella log accessi =====
        cursor.execute(
            #mette in automatico il timestamp attuale (CURRENT_TIMESTAMP)
            """
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                status TEXT NOT NULL,
                event TEXT NOT NULL
            )
        """
        )

        # Indici per performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_plate_number 
            ON authorized_plates(plate_number)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_expiration 
            ON authorized_plates(expiration_date)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_access_timestamp 
            ON access_log(timestamp)
        """
        )

        self.connection.commit()
        print(f"✅ Database inizializzato: {self.db_path}")

    # ========================================================================
    # GESTIONE AUTORIZZAZIONI
    # ========================================================================

    def add_authorized_plate(
        self,
        plate_number: str,
        first_name: str,
        last_name: str,
        role: str,
        expiration_date: str,
        notes: str = "",
    ) -> bool:
        """
        Aggiunge una targa autorizzata al database

        Args:
            plate_number: numero targa (es. "AB123CD")
            first_name: nome proprietario
            last_name: cognome proprietario
            role: ruolo (es. "Docente", "Studente", "Personale ATA")
            expiration_date: data scadenza formato "YYYY-MM-DD"
            notes: note opzionali

        Returns:
            True se aggiunto con successo, False altrimenti
        """
        try:
            plate_number = plate_number.upper().strip()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO authorized_plates 
                (plate_number, first_name, last_name, role, expiration_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (plate_number, first_name, last_name, role, expiration_date, notes),
            )

            self.connection.commit()
            print(f"✅ Targa aggiunta: {plate_number} - {first_name} {last_name}")
            return True

        except sqlite3.IntegrityError:
            print(f"⚠️ Targa {plate_number} già presente nel database")
            return False
        except Exception as e:
            print(f"❌ Errore aggiunta targa: {e}")
            return False

    def remove_plate(self, plate_number: str) -> bool:
        """Rimuove una targa dal database"""
        try:
            plate_number = plate_number.upper().strip()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM authorized_plates WHERE plate_number = ?
            """,
                (plate_number,),
            )

            self.connection.commit()

            if cursor.rowcount > 0:
                print(f"✅ Targa rimossa: {plate_number}")
                return True
            else:
                print(f"⚠️ Targa non trovata: {plate_number}")
                return False

        except Exception as e:
            print(f"❌ Errore rimozione targa: {e}")
            return False

    def update_authorized_plate(self, plate_number: str, **kwargs) -> bool:
        """
        Aggiorna i dati di una targa autorizzata

        Args:
            plate_number: targa da aggiornare
            **kwargs: campi da aggiornare (first_name, last_name, role,
                     expiration_date, notes)
        """
        try:
            plate_number = plate_number.upper().strip()

            # Costruisci query dinamica
            fields = []
            values = []

            for key, value in kwargs.items():
                if key in [
                    "first_name",
                    "last_name",
                    "role",
                    "expiration_date",
                    "notes",
                ]:
                    fields.append(f"{key} = ?")
                    values.append(value)

            if not fields:
                print("⚠️ Nessun campo da aggiornare")
                return False

            # Aggiungi updated_at
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(plate_number)

            query = f"""
                UPDATE authorized_plates 
                SET {', '.join(fields)}
                WHERE plate_number = ?
            """

            cursor = self.connection.cursor()
            cursor.execute(query, values)
            self.connection.commit()

            if cursor.rowcount > 0:
                print(f"✅ Targa aggiornata: {plate_number}")
                return True
            else:
                print(f"⚠️ Targa non trovata: {plate_number}")
                return False

        except Exception as e:
            print(f"❌ Errore aggiornamento targa: {e}")
            return False

    # ========================================================================
    # VERIFICA AUTORIZZAZIONI
    # ========================================================================

    def is_plate_authorized(self, plate_number: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verifica se una targa è autorizzata e non scaduta

        Args:
            plate_number: targa da verificare

        Returns:
            (is_authorized, plate_info_dict)
            - is_authorized: True se autorizzata e valida
            - plate_info_dict: dizionario con info targa o None
        """

        print("====== entrato in is_plate_authorized ======")
        try:
            plate_number = plate_number.upper().strip()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM authorized_plates 
                WHERE plate_number = ?
            """,
                (plate_number,),
            )

            row = cursor.fetchone()

            if not row:
                return False, None

            # Converti in dizionario
            plate_info = dict(row)

            # Verifica scadenza
            expiration_date_str = plate_info["expiration_date"]
            print(f"====== expiration_date_str: {expiration_date_str} ======")

            if expiration_date_str or expiration_date_str.strip() != "":

                expiration_date = datetime.strptime(
                    expiration_date_str, "%Y-%m-%d"
                ).date()
                today = date.today()

                if expiration_date < today:
                    print(
                        f"⚠️ Targa {plate_number} SCADUTA (scadenza: {expiration_date})"
                    )
                    plate_info["status"] = "expired"
                    return False, plate_info

            print("====== targa valida ======")
            plate_info["status"] = "valid"
            return True, plate_info

        except Exception as e:
            print(f"❌ Errore verifica targa: {e}")
            return False, None

    def get_all_valid_plates(self) -> List[str]:
        """
        Ritorna lista di tutte le targhe autorizzate e NON scadute

        Returns:
            Lista di stringhe (numeri targa)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT plate_number FROM authorized_plates
                WHERE expiration_date = "" OR expiration_date >= date('now')

                ORDER BY plate_number
            """
            )

            plates = [row["plate_number"] for row in cursor.fetchall()]
            return plates

        except Exception as e:
            print(f"❌ Errore recupero targhe: {e}")
            return []

    def get_all_plates(self) -> List[str]:
        """
        Ritorna lista di tutte le targhe autorizzate

        Returns:
            Lista di stringhe (numeri targa)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM authorized_plates order by plate_number")
            plates = [dict(row) for row in cursor.fetchall()]
            print(f"✅ Recupero targhe completato, targhe trovate: {len(plates)}")
            return plates
        except Exception as e:
            print(f"❌ Errore recupero targhe: {e}")
            return []

    def get_expiring_soon(self, days: int = 30) -> List[Dict]:
        """
        Ritorna targhe in scadenza entro N giorni

        Args:
            days: numero giorni di preavviso

        Returns:
            Lista di dizionari con info targhe
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM authorized_plates
                WHERE expiration_date >= date('now')
                AND expiration_date <= date('now', '+' || ? || ' days')
                ORDER BY expiration_date
            """,
                (days,),
            )

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"❌ Errore ricerca scadenze: {e}")
            return []

    # ========================================================================
    # LOG ACCESSI
    # ========================================================================

    def log_access(
        self,
        plate_number: str,
        status: str,
        event: str
    ):
        """
        Registra un accesso nel log

        Args:
            plate_number: targa rilevata
            frame_number: numero frame
            confidence: confidenza OCR
            status: "authorized", "not_authorized", "expired"
            track_id: ID tracking veicolo
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO access_log 
                (plate_number, status, event)
                VALUES (?, ?, ?)
            """,
                (plate_number, status, event),
            )

            self.connection.commit()

        except Exception as e:
            print(f"❌ Errore log accesso: {e}")

    def get_access_history(
    self, plate_number: str = None, limit: int = 100
) -> List[Dict]:
        """
        Recupera storico accessi con informazioni proprietario se presente
        """

        try:
            cursor = self.connection.cursor()

            base_query = """
                SELECT 
                    access_log.*,
                    authorized_plates.first_name,
                    authorized_plates.last_name,
                    authorized_plates.role
                FROM access_log
                LEFT JOIN authorized_plates 
                    ON access_log.plate_number = authorized_plates.plate_number
            """

            if plate_number:
                plate_number = plate_number.upper().strip()
                query = base_query + """
                    WHERE access_log.plate_number = ?
                    ORDER BY access_log.timestamp DESC
                    LIMIT ?
                """
                cursor.execute(query, (plate_number, limit))
            else:
                query = base_query + """
                    ORDER BY access_log.timestamp DESC
                    LIMIT ?
                """
                cursor.execute(query, (limit,))

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"❌ Errore recupero storico: {e}")
            return []

    def get_today_accesses(self) -> List[Dict]:
        """Ritorna tutti gli accessi di oggi"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM access_log
                WHERE date(timestamp) = date('now')
                ORDER BY timestamp DESC
            """
            )

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"❌ Errore recupero accessi odierni: {e}")
            return []

    # ========================================================================
    # STATISTICHE
    # ========================================================================

    def get_statistics(self) -> Dict:
        """Ritorna statistiche generali"""
        try:
            cursor = self.connection.cursor()

            # Totale autorizzati
            cursor.execute("SELECT COUNT(*) as count FROM authorized_plates")
            total_plates = cursor.fetchone()["count"]

            # Valide
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM authorized_plates
                WHERE (expiration_date is NULL OR expiration_date == "" OR expiration_date >= date('now') )
            """
            )
            valid_plates = cursor.fetchone()["count"]

            # Scadute
            expired_plates = total_plates - valid_plates

            # Accessi oggi
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM access_log
                WHERE date(timestamp) = date('now')
            """
            )
            today_accesses = cursor.fetchone()["count"]

            # Accessi settimana
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM access_log
                WHERE timestamp >= date('now', '-7 days')
            """
            )
            week_accesses = cursor.fetchone()["count"]

            return {
                "total_plates": total_plates,
                "valid_plates": valid_plates,
                "expired_plates": expired_plates,
                "today_accesses": today_accesses,
                "week_accesses": week_accesses,
            }

        except Exception as e:
            print(f"❌ Errore calcolo statistiche: {e}")
            return {}

    # ========================================================================
    # ALTRI METODI PER SITO
    # ========================================================================

    def get_all_logs(self):
        """Ritorna tutti i log di accesso"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM access_log ORDER BY timestamp DESC")
        return cursor.fetchall()

    def get_plate(self, plate_number):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM authorized_plates WHERE plate_number=?", (plate_number,)
        )
        return cursor.fetchone()

    def update_plate(self, plate_number, first_name, last_name, role, expiration_date):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE authorized_plates 
            SET first_name=?, last_name=?, role=?, expiration_date=? 
            WHERE plate_number=?
        """,
            (first_name, last_name, role, expiration_date, plate_number),
        )
        self.connection.commit()

    def get_plate_by_number(self, plate_number: str) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM authorized_plates WHERE plate_number = ?",
            (plate_number.upper().strip(),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ========================================================================
    # IMPORT/EXPORT
    # ========================================================================

    def import_from_txt(
        self,
        filepath: str,
        default_role: str = "Non specificato",
        default_expiration: str = "2025-12-31",
    ) -> int:
        """
        Importa targhe da file TXT (una per riga)

        Args:
            filepath: percorso file TXT
            default_role: ruolo di default
            default_expiration: scadenza di default

        Returns:
            Numero targhe importate
        """
        try:
            if not os.path.exists(filepath):
                print(f"❌ File non trovato: {filepath}")
                return 0

            count = 0
            with open(filepath, "r") as f:
                for line in f:
                    plate = line.strip().upper()
                    if plate and len(plate) >= 6:
                        # Usa nome generico
                        if self.add_authorized_plate(
                            plate_number=plate,
                            first_name="Importato",
                            last_name="da TXT",
                            role=default_role,
                            expiration_date=default_expiration,
                            notes=f"Importato da {filepath}",
                        ):
                            count += 1

            print(f"✅ Importate {count} targhe da {filepath}")
            return count

        except Exception as e:
            print(f"❌ Errore import: {e}")
            return 0

    def export_logs_to_csv(self, output_path: str = "access_logs_export.csv") -> bool:
        """
        Esporta tutti i log di accesso in formato CSV

        Args:
            output_path: percorso file CSV di output

        Returns:
            True se esportati con successo, False altrimenti
        """
        try:
            import csv

            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM access_log 
                ORDER BY timestamp DESC
            """
            )

            rows = cursor.fetchall()

            if not rows:
                print("⚠️ Nessun log da esportare")
                return False

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(
                    [
                        "ID",
                        "Targa",
                        "Data e Ora",
                        "Stato",
                        "Evento"
                    ]
                )

                # Dati
                for row in rows:
                    writer.writerow(
                        [
                            row["id"],
                            row["plate_number"],
                            row["timestamp"],
                            row["status"],
                            row["event"] if row["event"] else "",
                        ]
                    )

            print(f"✅ Esportati {len(rows)} log in {output_path}")
            return True

        except Exception as e:
            print(f"❌ Errore export log: {e}")
            return False

    def clear_access_log(self) -> bool:
        """
        Elimina tutti i log di accesso dal database

        Returns:
            True se eliminati con successo, False altrimenti
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM access_log")
            self.connection.commit()

            deleted_count = cursor.rowcount
            print(f"✅ Eliminati {deleted_count} log di accesso")
            return True

        except Exception as e:
            print(f"❌ Errore eliminazione log: {e}")
            return False

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def close(self):
        """Chiude la connessione al database"""
        if self.connection:
            self.connection.close()
            print("✅ Database chiuso")

    def __del__(self):
        """Destructor per chiudere connessione"""
        self.close()
