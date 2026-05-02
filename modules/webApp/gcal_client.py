"""
gcal_client.py

Client per Google Calendar API.
Funzioni offerte:
  - get_events_for_date()   → legge gli eventi di un giorno
  - is_active_now()         → True se l'ora corrente è dentro un evento
  - add_editor()            → aggiunge un'email come editor del calendario
  - remove_editor()         → rimuove un'email dagli editor del calendario
  - list_editors()          → lista le email con accesso al calendario

Autenticazione: Service Account (file JSON scaricato da Google Cloud Console).
"""

import os
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Optional
import modules.webApp.config as config

# Lazy import — se le librerie non sono installate, gcal è semplicemente disabilitato
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    _GCAL_AVAILABLE = True
except ImportError:
    _GCAL_AVAILABLE = False

# ── Configurazione ────────────────────────────────────────────────────────────

CALENDAR_ID       = config.CALENDAR_ID
SCOPES            = ["https://www.googleapis.com/auth/calendar"]


# ── Client singleton ──────────────────────────────────────────────────────────

_service = None

def _get_service():
    """Ritorna il client Google Calendar costruito dalle credenziali in config."""
    global _service
    if _service is not None:
        return _service

    if not _GCAL_AVAILABLE:
        raise RuntimeError("google-api-python-client non installato.")

    import modules.webApp.config as config
    info = config.GCAL_SERVICE_ACCOUNT_INFO

    if not info.get("private_key") or not info.get("client_email"):
        raise RuntimeError("Credenziali Google Calendar non configurate nel file .env")

    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _service

def is_available() -> bool:
    """True se le librerie sono presenti e le credenziali configurate."""
    if not _GCAL_AVAILABLE:
        return False
    try:
        import modules.webApp.config as config
        info = config.GCAL_SERVICE_ACCOUNT_INFO
        return bool(info.get("private_key") and info.get("client_email"))
    except Exception:
        return False

# ── Lettura eventi ────────────────────────────────────────────────────────────

def get_events_for_date(target_date: date) -> List[Dict]:
    """
    Ritorna la lista degli eventi del calendario per una data.
    Ogni evento: {"start": "HH:MM", "end": "HH:MM", "title": str}
    """
    svc = _get_service()

    # Intervallo: l'intera giornata in UTC
    tz_local = datetime.now().astimezone().tzinfo
    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz_local)
    day_end   = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=tz_local)

    result = svc.events().list(
        calendarId=CALENDAR_ID,
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    slots = []
    for ev in result.get("items", []):
        start = ev["start"].get("dateTime")
        end   = ev["end"].get("dateTime")

        # Salta gli eventi tutto-il-giorno (non hanno dateTime)
        if not start or not end:
            continue

        # Converti in HH:MM locale
        start_local = datetime.fromisoformat(start).astimezone(tz_local)
        end_local   = datetime.fromisoformat(end).astimezone(tz_local)

        slots.append({
            "start": start_local.strftime("%H:%M"),
            "end":   end_local.strftime("%H:%M"),
            "title": ev.get("summary", ""),
        })

    return slots


def is_active_now() -> bool:
    """
    True se l'ora corrente rientra in un evento del calendario.
    Usato da ServiceController come fonte primaria.
    """
    now_t = datetime.now().strftime("%H:%M")
    slots = get_events_for_date(date.today())
    for slot in slots:
        if slot["start"] <= now_t <= slot["end"]:
            return True
    return False


# ── Gestione ACL (editor del calendario) ─────────────────────────────────────

def add_editor(email: str) -> bool:
    """
    Aggiunge email come editor del calendario.
    Ritorna True se aggiunto, False se già presente o errore.
    """
    try:
        if not is_available():
            print(f"❌ GCal add_editor: librerie non disponibili o credenziali mancanti")
            print(f"   GCAL_AVAILABLE={_GCAL_AVAILABLE}, credentials path={CREDENTIALS_PATH}")
            print(f"   File esiste: {os.path.exists(CREDENTIALS_PATH)}")
            return False
        svc = _get_service()
        rule = {
            "scope": {"type": "user", "value": email.lower().strip()},
            "role": "writer",
        }
        svc.acl().insert(calendarId=CALENDAR_ID, body=rule).execute()
        print(f"✅ GCal: {email} aggiunto come editor")
        return True
    except HttpError as e:
        if e.resp.status == 409:
            print(f"ℹ️  GCal: {email} è già editor")
            return False
        print(f"❌ GCal add_editor HttpError {e.resp.status}: {e.content}")
        return False
    except Exception as e:
        print(f"❌ GCal add_editor error ({type(e).__name__}): {e}")
        return False


def remove_editor(email: str) -> bool:
    """
    Rimuove email dagli editor del calendario.
    Ritorna True se rimosso, False se non trovato o errore.
    """
    try:
        svc  = _get_service()
        acls = svc.acl().list(calendarId=CALENDAR_ID).execute()

        rule_id = None
        for rule in acls.get("items", []):
            if rule.get("scope", {}).get("value", "").lower() == email.lower().strip():
                rule_id = rule["id"]
                break

        if not rule_id:
            print(f"ℹ️  GCal: {email} non trovato tra gli editor")
            return False

        svc.acl().delete(calendarId=CALENDAR_ID, ruleId=rule_id).execute()
        print(f"✅ GCal: {email} rimosso dagli editor")
        return True

    except Exception as e:
        print(f"❌ GCal remove_editor error: {e}")
        return False


def list_editors() -> List[str]:
    """Ritorna la lista delle email con accesso al calendario."""
    try:
        svc  = _get_service()
        acls = svc.acl().list(calendarId=CALENDAR_ID).execute()
        return [
            rule["scope"]["value"]
            for rule in acls.get("items", [])
            if rule.get("scope", {}).get("type") == "user"
            and rule.get("role") in ("writer", "owner")
        ]
    except Exception as e:
        print(f"❌ GCal list_editors error: {e}")
        return []