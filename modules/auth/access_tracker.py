"""
access_tracker.py

Modulo per il tracking temporale degli accessi in entrata/uscita.
Gestisce il controllo del tempo minimo tra rilevazioni successive.

NOTA: in caso di riavvio del server, il tracker ricarica lo stato
dal database per evitare di perdere le entrate non ancora uscite.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import server.config as config


class AccessTracker:
    """
    Gestisce il tracking temporale degli accessi dei veicoli.
    Memorizza l'ultima rilevazione per ogni targa per evitare duplicati.

    Fallback su DB: se una targa non è in memoria (es. dopo riavvio),
    can_process_exit interroga il database per trovare l'ultima entrata
    senza uscita corrispondente prima di rifiutare l'operazione.
    """

    def __init__(self, db=None):
        """
        Args:
            db: istanza opzionale di DatabaseManager.
                Se fornita, viene usata come fallback per le uscite
                quando la targa non è presente in memoria.
        """
        # Dizionario: plate_number -> {
        #   'last_entry': datetime,
        #   'last_exit': datetime,
        #   'gate_id': str
        # }
        self.access_history: Dict[str, Dict] = {}
        self._db = db  # riferimento al DatabaseManager, può essere None

    def set_db(self, db):
        """
        Collega un'istanza DatabaseManager dopo la costruzione.
        Utile per risolvere dipendenze circolari all'avvio.
        """
        self._db = db

    # ────────────────────────────────────────────────────────────────────────
    # METODI PRIVATI DI SUPPORTO
    # ────────────────────────────────────────────────────────────────────────

    def _load_from_db(self, plate_number: str) -> bool:
        """
        Tenta di ricostruire lo stato in memoria per una targa leggendo
        l'ultimo evento dal database.

        Logica:
        - Cerca l'ultimo log di 'entrata' e l'ultimo di 'uscita' per la targa.
        - Se l'ultima entrata è più recente dell'ultima uscita (o non c'è
          uscita), considera il veicolo come ancora dentro e carica lo stato.

        Returns:
            True se è stato trovato uno stato utile nel DB, False altrimenti.
        """
        if self._db is None:
            return False

        try:
            # Recupera gli ultimi eventi per questa targa
            # Usiamo get_access_history che già esiste nel DatabaseManager
            logs = self._db.get_access_history(
                plate_number=plate_number,
                limit=50  # ultimi 50 eventi sono più che sufficienti
            )

            if not logs:
                return False

            # Trova il timestamp più recente per entrata e uscita
            last_entry_ts: Optional[datetime] = None
            last_exit_ts:  Optional[datetime] = None

            for log in logs:
                event = (log.get("event") or "").lower().strip()
                ts_str = log.get("timestamp")
                if not ts_str:
                    continue

                try:
                    # Il timestamp nel DB può avere o no i decimali dei secondi
                    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                        try:
                            ts = datetime.strptime(ts_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                except Exception:
                    continue

                if event == "entrata":
                    if last_entry_ts is None or ts > last_entry_ts:
                        last_entry_ts = ts
                elif event == "uscita":
                    if last_exit_ts is None or ts > last_exit_ts:
                        last_exit_ts = ts

            # Carica in memoria solo se c'è un'entrata più recente dell'uscita
            # (veicolo presumibilmente ancora dentro)
            if last_entry_ts is None:
                return False

            # Se c'è un'uscita più recente dell'entrata → veicolo fuori,
            # non blocchiamo ma carichiamo comunque lo stato per i controlli
            # sull'intervallo minimo
            if plate_number not in self.access_history:
                self.access_history[plate_number] = {}

            self.access_history[plate_number]['last_entry'] = last_entry_ts
            if last_exit_ts:
                self.access_history[plate_number]['last_exit'] = last_exit_ts

            if config.VERBOSE:
                print(f"     🔄 Stato ripristinato da DB per {plate_number}: "
                      f"entry={last_entry_ts}, exit={last_exit_ts}")
            return True

        except Exception as e:
            print(f"❌ Errore _load_from_db per {plate_number}: {e}")
            return False

    def _is_vehicle_inside(self, plate_number: str) -> bool:
        """
        Verifica se un veicolo è considerato 'dentro' in base alla memoria.
        Un veicolo è dentro se ha un'entrata più recente dell'ultima uscita
        (o se non ha mai registrato un'uscita).
        """
        history = self.access_history.get(plate_number)
        if not history:
            return False

        last_entry = history.get('last_entry')
        last_exit  = history.get('last_exit')

        if last_entry is None:
            return False

        if last_exit is None:
            return True  # entrato, mai uscito

        return last_entry > last_exit  # entrato dopo l'ultima uscita

    # ────────────────────────────────────────────────────────────────────────
    # METODI PUBBLICI
    # ────────────────────────────────────────────────────────────────────────

    def can_process_entry(self, plate_number: str, gate_id: str) -> bool:
        """
        Verifica se un'entrata può essere processata.

        Args:
            plate_number: targa del veicolo
            gate_id: ID del gate

        Returns:
            bool: True se l'entrata può essere registrata
        """
        plate_number = plate_number.upper().strip()

        # Se non in memoria, tenta ripristino da DB
        if plate_number not in self.access_history:
            self._load_from_db(plate_number)

        if plate_number not in self.access_history:
            return True  # prima rilevazione assoluta

        history = self.access_history[plate_number]
        last_entry = history.get('last_entry')

        if last_entry is None:
            return True

        time_since_last = datetime.now() - last_entry
        min_interval = timedelta(seconds=config.MIN_ENTRY_INTERVAL_SECONDS)

        if time_since_last < min_interval:
            if config.VERBOSE:
                remaining = (min_interval - time_since_last).total_seconds()
                print(f"     ⏱️  Entrata troppo recente, attendi {remaining:.0f}s")
            return False

        return True

    def can_process_exit(self, plate_number: str, gate_id: str) -> bool:
        """
        Verifica se un'uscita può essere processata.

        Flusso:
        1. Cerca in memoria.
        2. Se non trovato (es. dopo riavvio), tenta ripristino dal DB.
        3. Se ancora non trovato → nega (nessuna entrata nota).
        4. Controlla che sia passato abbastanza tempo dall'ultima rilevazione.

        Args:
            plate_number: targa del veicolo
            gate_id: ID del gate

        Returns:
            bool: True se l'uscita può essere registrata
        """
        plate_number = plate_number.upper().strip()

        # ── Passo 1: controlla memoria ───────────────────────────────────────
        if plate_number not in self.access_history:
            # ── Passo 2: fallback su DB ──────────────────────────────────────
            loaded = self._load_from_db(plate_number)

            if not loaded:
                if config.VERBOSE:
                    print(f"     ⚠️  Nessuna entrata trovata per {plate_number} "
                          f"(né in memoria né nel DB)")
                return False

        # ── Passo 3: verifica che il veicolo risulti dentro ──────────────────
        if not self._is_vehicle_inside(plate_number):
            if config.VERBOSE:
                print(f"     ⚠️  {plate_number} non risulta dentro "
                      f"(ultima uscita > ultima entrata)")
            # Permettiamo comunque l'uscita: potrebbe essere un edge case
            # (es. uscita non registrata correttamente in precedenza).
            # Rimuoviamo il blocco hard e lasciamo passare, logghiamo solo.

        history = self.access_history[plate_number]
        last_entry = history.get('last_entry')
        last_exit  = history.get('last_exit')

        # Ultima rilevazione tra entry e exit
        last_detection = last_entry
        if last_exit and (not last_entry or last_exit > last_entry):
            last_detection = last_exit

        if last_detection is None:
            return False

        # ── Passo 4: controlla intervallo minimo ─────────────────────────────
        time_since_last = datetime.now() - last_detection
        min_interval = timedelta(seconds=config.MIN_EXIT_INTERVAL_SECONDS)

        if time_since_last < min_interval:
            if config.VERBOSE:
                remaining = (min_interval - time_since_last).total_seconds()
                print(f"     ⏱️  Uscita troppo recente, attendi {remaining:.0f}s")
            return False

        return True

    def register_entry(self, plate_number: str, gate_id: str):
        """Registra un'entrata."""
        plate_number = plate_number.upper().strip()

        if plate_number not in self.access_history:
            self.access_history[plate_number] = {}

        self.access_history[plate_number]['last_entry'] = datetime.now()
        self.access_history[plate_number]['gate_id'] = gate_id

        if config.VERBOSE:
            print(f"     ✅ Entrata registrata: {plate_number} @ {gate_id}")

    def register_exit(self, plate_number: str, gate_id: str):
        """Registra un'uscita."""
        plate_number = plate_number.upper().strip()

        if plate_number not in self.access_history:
            self.access_history[plate_number] = {}

        self.access_history[plate_number]['last_exit'] = datetime.now()
        self.access_history[plate_number]['gate_id'] = gate_id

        if config.VERBOSE:
            print(f"     ✅ Uscita registrata: {plate_number} @ {gate_id}")

    def get_last_access(self, plate_number: str) -> Optional[Dict]:
        """
        Ottiene l'ultima rilevazione per una targa.
        Tenta ripristino da DB se non presente in memoria.
        """
        plate_number = plate_number.upper().strip()

        if plate_number not in self.access_history:
            self._load_from_db(plate_number)

        return self.access_history.get(plate_number)

    def cleanup_old_entries(self, max_age_hours: int = 24):
        """
        Rimuove le entry più vecchie di max_age_hours dalla memoria.
        Non tocca il database.
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        plates_to_remove = []
        for plate, history in self.access_history.items():
            last_entry = history.get('last_entry')
            last_exit  = history.get('last_exit')

            last_time = last_entry
            if last_exit and (not last_entry or last_exit > last_entry):
                last_time = last_exit

            if last_time and last_time < cutoff_time:
                plates_to_remove.append(plate)

        for plate in plates_to_remove:
            del self.access_history[plate]

        if config.VERBOSE and plates_to_remove:
            print(f"🧹 Cleanup: rimossi {len(plates_to_remove)} record obsoleti dalla memoria")


# ── Istanza globale ───────────────────────────────────────────────────────────
# Il DB viene collegato dopo con set_db() per evitare import circolari.
access_tracker = AccessTracker()