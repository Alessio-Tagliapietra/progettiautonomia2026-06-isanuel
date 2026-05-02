"""
service_controller.py

Gestisce lo stato attivo/disattivo del servizio.

Priorità:
  1. manual_override (True/False) → forza lo stato
  2. Google Calendar → legge gli eventi del giorno
  3. weekly_template → fallback se GCal non è raggiungibile
  4. default_active  → fallback finale

Il polling di GCal avviene ogni GCAL_POLL_INTERVAL secondi in un thread
dedicato. L'ultimo risultato viene cachato in _gcal_cache per evitare
chiamate API su ogni chiamata a is_active().
"""

import threading
import json
import os
from datetime import datetime, time as dtime, date as ddate
from typing import Optional, List, Dict

WEEKDAY_NAMES = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "data", "service_config.json")

# Intervallo polling Google Calendar (secondi)
GCAL_POLL_INTERVAL = 60

_DEFAULT_WEEKLY: Dict[str, List] = {
    "0": [{"start": "07:50", "end": "08:10"}, {"start": "12:00", "end": "12:30"}],
    "1": [{"start": "07:50", "end": "08:10"}, {"start": "12:00", "end": "12:30"}],
    "2": [{"start": "07:50", "end": "08:10"}, {"start": "12:00", "end": "12:30"}],
    "3": [{"start": "07:50", "end": "08:10"}, {"start": "12:00", "end": "12:30"}],
    "4": [{"start": "07:50", "end": "08:10"}, {"start": "12:00", "end": "12:30"}],
    "5": [],
    "6": [],
}

_DEFAULT_CONFIG = {
    "manual_override": None,
    "weekly_template": _DEFAULT_WEEKLY,
    "day_overrides":   {},
    "default_active":  False,
}


def _parse_time(s: str) -> Optional[dtime]:
    try:
        return dtime.fromisoformat(s)
    except Exception:
        return None


def _slots_active_now(slots: List[Dict]) -> bool:
    now_t = datetime.now().time().replace(second=0, microsecond=0)
    for slot in slots:
        start = _parse_time(slot.get("start", ""))
        end   = _parse_time(slot.get("end", ""))
        if start and end and start <= now_t <= end:
            return True
    return False


class ServiceController:

    def __init__(self):
        self._lock   = threading.RLock()  # RLock: rientrante, evita deadlock
        self._config: Dict = {}
        self._load_config()

        # Cache Google Calendar
        # {"active": bool, "slots": [...], "date": "YYYY-MM-DD", "ok": bool}
        self._gcal_cache: Dict = {"ok": False, "active": False, "slots": [], "date": ""}

        # Thread scheduler (stato + gcal polling)
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

    # ── Google Calendar polling ───────────────────────────────────────────────

    def _poll_gcal(self):
        """
        Interroga Google Calendar e aggiorna _gcal_cache.
        Chiamato dal thread scheduler ogni GCAL_POLL_INTERVAL secondi.
        """
        try:
            from modules.webApp.gcal_client import is_available, get_events_for_date
            if not is_available():
                return

            today  = ddate.today()
            slots  = get_events_for_date(today)
            active = _slots_active_now(slots)

            with self._lock:
                self._gcal_cache = {
                    "ok":     True,
                    "active": active,
                    "slots":  slots,
                    "date":   today.isoformat(),
                }
            print(f"🗓️  GCal sync: {len(slots)} eventi oggi, attivo={active}")

        except Exception as e:
            print(f"⚠️  GCal polling error: {e}")
            with self._lock:
                self._gcal_cache["ok"] = False

    # ── Logica stato ─────────────────────────────────────────────────────────

    def is_active(self) -> bool:
        """
        Priorità:
          1. manual_override
          2. Google Calendar (cache)
          3. weekly_template / day_overrides
          4. default_active
        """
        with self._lock:
            override = self._config.get("manual_override")
            if override is not None:
                return bool(override)

            # GCal disponibile e cache aggiornata per oggi
            cache = self._gcal_cache
            if cache.get("ok") and cache.get("date") == ddate.today().isoformat():
                return bool(cache.get("active", False))

            # Fallback: weekly_template / day_overrides
            return self._is_in_template()

    def _is_in_template(self) -> bool:
        """Fallback: controlla weekly_template e day_overrides."""
        today_str = ddate.today().isoformat()
        weekday   = str(datetime.now().weekday())

        overrides = self._config.get("day_overrides", {})
        if today_str in overrides:
            return _slots_active_now(overrides[today_str])

        tpl   = self._config.get("weekly_template", {})
        slots = tpl.get(weekday, [])
        if slots:
            return _slots_active_now(slots)

        return bool(self._config.get("default_active", False))

    def _get_slots_for_date(self, d: ddate) -> List[Dict]:
        """Fasce per una data: gcal cache (se oggi) → day_overrides → template."""
        cache = self._gcal_cache
        if cache.get("ok") and cache.get("date") == d.isoformat():
            return cache.get("slots", [])

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
            cache       = self._gcal_cache
            gcal_ok     = cache.get("ok", False) and cache.get("date") == ddate.today().isoformat()
            in_schedule = self._is_in_template()
            active      = self.is_active()
            return {
                "active":           active,
                "manual_override":  override,
                "in_schedule":      in_schedule,
                "gcal_ok":          gcal_ok,
                "gcal_slots_today": cache.get("slots", []) if gcal_ok else [],
                "weekly_template":  self._config.get("weekly_template", {}),
                "day_overrides":    self._config.get("day_overrides", {}),
                "default_active":   self._config.get("default_active", False),
            }

    def set_manual_override(self, value: Optional[bool]):
        with self._lock:
            self._config["manual_override"] = value
            self._save_config()

    def set_weekly_day(self, weekday: int, slots: List[Dict]):
        with self._lock:
            self._config.setdefault("weekly_template", {})[str(weekday)] = slots
            self._save_config()

    def get_weekly_template(self) -> Dict[str, List]:
        with self._lock:
            return dict(self._config.get("weekly_template", {}))

    def set_day_override(self, date_str: str, slots: List[Dict]):
        with self._lock:
            self._config.setdefault("day_overrides", {})[date_str] = slots
            self._save_config()

    def remove_day_override(self, date_str: str):
        with self._lock:
            self._config.get("day_overrides", {}).pop(date_str, None)
            self._save_config()

    def get_day_overrides(self) -> Dict[str, List]:
        with self._lock:
            return dict(self._config.get("day_overrides", {}))

    def get_calendar_month(self, year: int, month: int) -> List[Dict]:
        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        result = []
        for day in range(1, days_in_month + 1):
            d        = ddate(year, month, day)
            date_str = d.isoformat()
            has_override = date_str in self._config.get("day_overrides", {})
            slots    = self._get_slots_for_date(d)
            # Segnala se i dati vengono da GCal
            from_gcal = (
                self._gcal_cache.get("ok", False) and
                self._gcal_cache.get("date") == date_str
            )
            result.append({
                "date":         date_str,
                "weekday":      d.weekday(),
                "weekday_name": WEEKDAY_NAMES[d.weekday()],
                "slots":        slots,
                "has_override": has_override,
                "from_gcal":    from_gcal,
            })
        return result

    def set_default_active(self, value: bool):
        with self._lock:
            self._config["default_active"] = value
            self._save_config()

    # ── Scheduler loop ────────────────────────────────────────────────────────

    def _scheduler_loop(self):
        import time
        last_state   = None
        poll_counter = 0

        # Prima sincronizzazione immediata
        self._poll_gcal()

        while True:
            try:
                current = self.is_active()
                if current != last_state:
                    emoji = "✅" if current else "⏸️"
                    print(f"{emoji} ServiceController: servizio "
                          f"{'ATTIVO' if current else 'DISATTIVO'} "
                          f"({datetime.now().strftime('%H:%M')})")
                    last_state = current

                poll_counter += 1
                if poll_counter >= (GCAL_POLL_INTERVAL // 30):
                    self._poll_gcal()
                    poll_counter = 0

            except Exception as e:
                print(f"⚠️  ServiceController scheduler error: {e}")

            time.sleep(30)


# Singleton globale
service = ServiceController()