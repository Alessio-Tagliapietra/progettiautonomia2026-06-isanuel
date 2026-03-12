import sqlite3
from datetime import datetime


class UsersDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS authorized_users (
                    email      TEXT PRIMARY KEY,
                    note       TEXT DEFAULT '',
                    added_at   TEXT NOT NULL
                )
            """)
            conn.commit()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM authorized_users ORDER BY added_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def is_authorized(self, email: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM authorized_users WHERE email = ?", (email,)
            ).fetchone()
        return row is not None

    def add(self, email: str, note: str = "") -> bool:
        """Ritorna True se aggiunto, False se già esistente."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO authorized_users (email, note, added_at) VALUES (?, ?, ?)",
                    (email.lower().strip(), note.strip(), datetime.now().isoformat()),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove(self, email: str) -> bool:
        """Ritorna True se rimosso, False se non trovato."""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM authorized_users WHERE email = ?", (email.lower().strip(),)
            )
            conn.commit()
        return cur.rowcount > 0

    def update_note(self, email: str, note: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE authorized_users SET note = ? WHERE email = ?",
                (note.strip(), email.lower().strip()),
            )
            conn.commit()

    def seed(self, emails: list[str]):
        """Inserisce le email iniziali se il DB è vuoto."""
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM authorized_users").fetchone()[0]
        if count == 0:
            for email in emails:
                self.add(email, note="Utente iniziale")