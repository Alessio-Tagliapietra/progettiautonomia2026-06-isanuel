"""
service_controller.py

Modulo condiviso tra reader e webapp per il controllo del servizio.
Gestisce:
  - flag attivo/disattivo (manuale o automatico)
  - template settimanale con più fasce orarie per giorno
  - override per singolo giorno (data specifica)
  - scheduler che aggiorna lo stato in base agli orari

Struttura config:
{
  "manual_override": null | true | false,
  "weekly_template": {
    "0": [{"start": "07:40", "end": "08:00"}, {"start": "12:00", "end": "12:30"}],
    ...
    "6": []
  },
  "day_overrides": {
    "2026-04-15": [{"start": "08:00", "end": "13:00"}],
    "2026-04-16": []   # lista vuota = chiuso quel giorno
  },
  "default_active": false
}
"""

import threading
import json
import os
from datetime import datetime, time as dtime, date as ddate, timedelta
from typing import Optional, List, Dict

WEEKDAY_NAMES = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "data", "service_config.json")

_DEFAULT_WEEKLY: Dict[str, List] = {
    "0": [{"start": "07:40", "end": "08:10"}],
    "1": [{"start": "07:40", "end": "08:10"}],
    "2": [{"start": "07:40", "end": "08:10"}],
    "3": [{"start": "07:40", "end": "08:10"}],
    "4": [{"start": "07:40", "end": "08:10"}],
    "5": [],
    "6": [],
}

_DEFAULT_CONFIG = {
    "manual_override": None,
    "weekly_template": _DEFAULT_WEEKLY,
    "day_overrides": {},
    "default_active": False,
}


def _parse_time(s: str) -> Optional[dtime]:
    try:
        return dtime.fromisoformat(s)
    except Exception:
        return None


def _slots_active_now(slots: List[Dict]) -> bool:
    """Controlla se l'ora attuale rientra in una delle fasce."""
    now_t = datetime.now().time().replace(second=0, microsecond=0)
    for slot in slots:
        start = _parse_time(slot.get("start", ""))
        end   = _parse_time(slot.get("end", ""))
        if start and end and start <= now_t <= end:
            return True
    return False


class ServiceController:
    def __init__(self):
        self._lock = threading.Lock()
        self._config: Dict = {}
        self._load_config()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    # ── Persistenza ──────────────────────────────────────────────────────────

    def _load_config(self):
        try:
            os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
            if os.path.exists(_CONFIG_PATH):
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._config = {**_DEFAULT_CONFIG, **loaded}
                # Assicura che il template abbia tutti e 7 i giorni
                tpl = self._config.setdefault("weekly_template", {})
                for d in range(7):
                    tpl.setdefault(str(d), [])
            else:
                self._config = {k: v for k, v in _DEFAULT_CONFIG.items()}
                self._save_config()
        except Exception as e:
            print(f"⚠️  ServiceController: errore caricamento config: {e}")
            self._config = {k: v for k, v in _DEFAULT_CONFIG.items()}

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
            with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  ServiceController: errore salvataggio config: {e}")

    # ── Logica stato ─────────────────────────────────────────────────────────

    def is_active(self) -> bool:
        with self._lock:
            override = self._config.get("manual_override")
            if override is not None:
                return bool(override)
            return self._is_in_schedule()

    def _is_in_schedule(self) -> bool:
        today_str = ddate.today().isoformat()
        weekday   = str(datetime.now().weekday())

        # Override specifico per data ha priorità
        overrides = self._config.get("day_overrides", {})
        if today_str in overrides:
            return _slots_active_now(overrides[today_str])

        # Altrimenti usa il template settimanale
        tpl = self._config.get("weekly_template", {})
        slots = tpl.get(weekday, [])
        if slots:
            return _slots_active_now(slots)

        return bool(self._config.get("default_active", False))

    def _get_slots_for_date(self, d: ddate) -> Optional[List[Dict]]:
        """Ritorna le fasce per una data (override > template). None = usa default."""
        date_str = d.isoformat()
        overrides = self._config.get("day_overrides", {})
        if date_str in overrides:
            return overrides[date_str]
        tpl = self._config.get("weekly_template", {})
        return tpl.get(str(d.weekday()), [])

    # ── API pubblica ──────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        with self._lock:
            override    = self._config.get("manual_override")
            in_schedule = self._is_in_schedule()
            active      = override if override is not None else in_schedule
            return {
                "active":           bool(active),
                "manual_override":  override,
                "in_schedule":      in_schedule,
                "weekly_template":  self._config.get("weekly_template", {}),
                "day_overrides":    self._config.get("day_overrides", {}),
                "default_active":   self._config.get("default_active", False),
            }

    def set_manual_override(self, value: Optional[bool]):
        with self._lock:
            self._config["manual_override"] = value
            self._save_config()

    # ── Template settimanale ─────────────────────────────────────────────────

    def set_weekly_day(self, weekday: int, slots: List[Dict]):
        """Imposta le fasce orarie per un giorno della settimana (0=lun … 6=dom)."""
        with self._lock:
            self._config.setdefault("weekly_template", {})[str(weekday)] = slots
            self._save_config()

    def get_weekly_template(self) -> Dict[str, List]:
        with self._lock:
            return dict(self._config.get("weekly_template", {}))

    # ── Override per data ────────────────────────────────────────────────────

    def set_day_override(self, date_str: str, slots: List[Dict]):
        """
        Imposta un override per una data specifica (formato YYYY-MM-DD).
        slots=[] significa chiuso quel giorno.
        """
        with self._lock:
            self._config.setdefault("day_overrides", {})[date_str] = slots
            self._save_config()

    def remove_day_override(self, date_str: str):
        """Rimuove l'override per una data (torna al template settimanale)."""
        with self._lock:
            self._config.get("day_overrides", {}).pop(date_str, None)
            self._save_config()

    def get_day_overrides(self) -> Dict[str, List]:
        with self._lock:
            return dict(self._config.get("day_overrides", {}))

    # ── Dati calendario ──────────────────────────────────────────────────────

    def get_calendar_month(self, year: int, month: int) -> List[Dict]:
        """
        Ritorna la lista di tutti i giorni del mese con le loro fasce orarie.
        Ogni elemento: {date, weekday, slots, has_override}
        """
        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        result = []
        for day in range(1, days_in_month + 1):
            d = ddate(year, month, day)
            date_str  = d.isoformat()
            overrides = self._config.get("day_overrides", {})
            has_override = date_str in overrides
            slots = self._get_slots_for_date(d) or []
            result.append({
                "date":         date_str,
                "weekday":      d.weekday(),
                "weekday_name": WEEKDAY_NAMES[d.weekday()],
                "slots":        slots,
                "has_override": has_override,
            })
        return result

    def set_default_active(self, value: bool):
        with self._lock:
            self._config["default_active"] = value
            self._save_config()

    # ── Scheduler ────────────────────────────────────────────────────────────

    def _scheduler_loop(self):
        import time
        last_state = None
        while True:
            try:
                current = self.is_active()
                if current != last_state:
                    emoji = "✅" if current else "⏸️"
                    print(f"{emoji} ServiceController: servizio {'ATTIVO' if current else 'DISATTIVO'} "
                          f"({datetime.now().strftime('%H:%M')})")
                    last_state = current
            except Exception as e:
                print(f"⚠️  ServiceController scheduler error: {e}")
            time.sleep(30)


# Singleton globale
service = ServiceController()