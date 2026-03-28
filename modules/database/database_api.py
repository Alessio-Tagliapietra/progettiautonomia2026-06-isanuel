"""
database_api.py
REST API server per il database.

Avvio:
    uvicorn modules.database.database_api:app --host 0.0.0.0 --port 8001 --reload
Docs: http://localhost:8001/docs
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

import modules.database.config as config
from modules.database.database import DatabaseManager

app = FastAPI(title="Gate Database API", version="2.0.0")
db  = DatabaseManager()


# ── Modelli Pydantic ──────────────────────────────────────────────────────────

class PlateCreate(BaseModel):
    """Crea una targa legandola ad una persona esistente tramite person_id,
    oppure crea automaticamente la persona con first_name/last_name/role."""
    plate_number: str
    person_id: Optional[int] = None          # priorità se fornito
    first_name: Optional[str] = None         # usato solo se person_id è None
    last_name: Optional[str] = None
    role: Optional[str] = None
    expiration_date: str = ""
    notes: str = ""

class PlateUpdate(BaseModel):
    """Solo i campi propri della targa. new_plate_number permette di rinominare la targa."""
    expiration_date: str = ""
    notes: str = ""
    new_plate_number: Optional[str] = None

class CheckPlateRequest(BaseModel):
    plate: str

class LogAccessRequest(BaseModel):
    plate: str
    status: str
    event: str = "entrata"

class DeleteLogsRequest(BaseModel):
    log_ids: List[int]

class PersonCreate(BaseModel):
    first_name: str
    last_name: str
    role: str
    notes: str = ""

class PersonUpdate(BaseModel):
    first_name: str
    last_name: str
    role: str
    notes: str = ""

class PlateToPersonCreate(BaseModel):
    plate_number: str
    expiration_date: str = ""
    notes: str = ""


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Plates ────────────────────────────────────────────────────────────────────

@app.get("/plates", summary="Tutte le targhe (con dati persona via JOIN)")
def get_all_plates():
    return db.get_all_plates()


@app.post("/plates", status_code=201)
def add_plate(data: PlateCreate):
    if data.person_id:
        ok = db.add_plate_to_person(data.person_id, data.plate_number,
                                     data.expiration_date, data.notes)
    else:
        if not data.first_name or not data.last_name or not data.role:
            raise HTTPException(400, "Fornire person_id oppure first_name/last_name/role")
        ok = db.add_authorized_plate(data.plate_number, data.first_name,
                                      data.last_name, data.role,
                                      data.expiration_date, data.notes)
    if not ok:
        raise HTTPException(409, "Targa già esistente o persona non trovata")
    return {"ok": True}


@app.post("/plates/check", summary="Verifica autorizzazione targa")
def check_plate(body: CheckPlateRequest):
    plate = body.plate.upper().strip()
    if not plate:
        raise HTTPException(400, "plate mancante")
    is_auth, info = db.is_plate_authorized(plate)
    if is_auth:
        status = "authorized"
    elif info and info.get("status") == "expired":
        status = "expired"
    else:
        status = "not_authorized"
    if config.VERBOSE:
        print(f"   🔍 check_plate: {plate} → {status}")
    return {"status": status, "plate": plate, "plate_info": info or {}}


@app.get("/plates/{plate_number}")
def get_plate(plate_number: str):
    plate = db.get_plate(plate_number.upper())
    if not plate:
        raise HTTPException(404, "Targa non trovata")
    return plate


@app.put("/plates/{plate_number}", summary="Aggiorna scadenza, note e/o numero targa")
def update_plate(plate_number: str, data: PlateUpdate):
    try:
        db.update_plate(plate_number.upper(), data.expiration_date,
                        data.notes, data.new_plate_number)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"ok": True}


@app.delete("/plates/{plate_number}")
def delete_plate(plate_number: str):
    if not db.remove_plate(plate_number.upper()):
        raise HTTPException(404, "Targa non trovata")
    return {"ok": True}


# ── Access logs ───────────────────────────────────────────────────────────────

@app.post("/access/log", status_code=201)
def log_access(data: LogAccessRequest):
    db.log_access(plate_number=data.plate.upper().strip(), status=data.status, event=data.event)
    if config.VERBOSE:
        print(f"   📝 log_access: {data.plate} | {data.status} | {data.event}")
    return {"ok": True}


@app.get("/access/logs")
def get_access_history(
    plate_number: Optional[str] = None,
    limit: int = Query(default=10_000_000, ge=0),
    date: Optional[str] = None,
    status: Optional[str] = None,
):
    return db.get_access_history(plate_number=plate_number, limit=limit, date=date, status=status)


@app.get("/access/logs/advanced")
def get_access_history_advanced(
    plate_number: Optional[str] = None, first_name: Optional[str] = None,
    last_name: Optional[str] = None, role: Optional[str] = None,
    status: Optional[str] = None, date_single: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    limit: int = Query(default=100, ge=0),
):
    return db.get_access_history_advanced(
        plate_number=plate_number, first_name=first_name, last_name=last_name,
        role=role, status=status, date_single=date_single,
        date_from=date_from, date_to=date_to, limit=limit,
    )


@app.delete("/access/logs")
def delete_logs(data: DeleteLogsRequest):
    return {"deleted": db.delete_logs_by_ids(data.log_ids)}


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.get("/analytics/per-giorno")
def accessi_per_giorno(start_date: str, end_date: str):
    return db.get_accessi_per_giorno(start_date, end_date)

@app.get("/analytics/per-stato")
def accessi_per_stato(start_date: str, end_date: str):
    return db.get_accessi_per_stato(start_date, end_date)

@app.get("/analytics/per-ora")
def accessi_per_ora(start_date: str, end_date: str):
    return db.get_accessi_per_ora(start_date, end_date)

@app.get("/analytics/top-targhe")
def top_targhe(start_date: str, end_date: str, limit: int = 10):
    return db.get_top_targhe(start_date, end_date, limit)

@app.get("/analytics/trend")
def trend_per_stato(start_date: str, end_date: str):
    return db.get_trend_per_stato(start_date, end_date)

@app.get("/analytics/kpi-entrate-uscite")
def kpi_entrate_uscite(start_date: str, end_date: str):
    return db.get_kpi_entrate_uscite(start_date, end_date)

@app.get("/analytics/distribuzione-ev")
def distribuzione_ev(start_date: str, end_date: str):
    return db.get_distribuzione_entrate_uscite(start_date, end_date)

@app.get("/analytics/flusso-orario")
def flusso_orario(start_date: str, end_date: str):
    return db.get_flusso_orario_entrate_uscite(start_date, end_date)

@app.get("/analytics/saldo-giornaliero")
def saldo_giornaliero(start_date: str, end_date: str):
    return db.get_saldo_giornaliero(start_date, end_date)


# ── Persons ───────────────────────────────────────────────────────────────────

@app.get("/persons")
def get_all_persons(q: Optional[str] = None):
    return db.search_persons(q.strip()) if q and q.strip() else db.get_all_persons()

@app.post("/persons", status_code=201)
def add_person(data: PersonCreate):
    pid = db.add_person(data.first_name, data.last_name, data.role, data.notes)
    if pid < 0:
        raise HTTPException(500, "Errore aggiunta persona")
    return {"ok": True, "person_id": pid}

@app.get("/persons/{person_id}")
def get_person(person_id: int):
    p = db.get_person(person_id)
    if not p:
        raise HTTPException(404, "Persona non trovata")
    return p

@app.put("/persons/{person_id}")
def update_person(person_id: int, data: PersonUpdate):
    if not db.update_person(person_id, data.first_name, data.last_name, data.role, data.notes):
        raise HTTPException(404, "Persona non trovata")
    return {"ok": True}

@app.delete("/persons/{person_id}")
def delete_person(person_id: int):
    if not db.delete_person(person_id):
        raise HTTPException(404, "Persona non trovata")
    return {"ok": True}

@app.post("/persons/{person_id}/plates", status_code=201)
def add_plate_to_person(person_id: int, data: PlateToPersonCreate):
    if not db.add_plate_to_person(person_id, data.plate_number, data.expiration_date, data.notes):
        raise HTTPException(409, "Targa già esistente o persona non trovata")
    return {"ok": True}