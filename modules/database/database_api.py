"""
database_api.py
REST API server per il database delle targhe e dei log di accesso.
Sostituisce database_service.py (MQTT-based).

Avvio:
    uvicorn modules.database.database_api:app --host 0.0.0.0 --port 8001 --reload

Documentazione interattiva:
    http://localhost:8001/docs
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

import modules.database.config as config
from modules.database.database import DatabaseManager


app = FastAPI(
    title="Gate Database API",
    version="1.0.0",
    description="API REST per la gestione delle targhe autorizzate e dei log di accesso.",
)

db = DatabaseManager()


# ── Pydantic models ───────────────────────────────────────────────────────────

class PlateCreate(BaseModel):
    plate_number: str
    first_name: str
    last_name: str
    role: str
    expiration_date: str = ""
    notes: str = ""


class PlateUpdate(BaseModel):
    first_name: str
    last_name: str
    role: str
    expiration_date: str = ""


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


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Plates ────────────────────────────────────────────────────────────────────

@app.get("/plates", summary="Tutte le targhe autorizzate")
def get_all_plates():
    return db.get_all_plates()


@app.post("/plates", status_code=201, summary="Aggiungi targa")
def add_plate(data: PlateCreate):
    ok = db.add_authorized_plate(
        data.plate_number,
        data.first_name,
        data.last_name,
        data.role,
        data.expiration_date,
        data.notes,
    )
    if not ok:
        raise HTTPException(status_code=409, detail="Targa già esistente")
    return {"ok": True}


@app.post("/plates/check", summary="Verifica autorizzazione targa")
def check_plate(body: CheckPlateRequest):
    plate = body.plate.upper().strip()
    if not plate:
        raise HTTPException(status_code=400, detail="plate mancante")

    is_authorized, plate_info = db.is_plate_authorized(plate)

    if is_authorized:
        status = "authorized"
    elif plate_info and plate_info.get("status") == "expired":
        status = "expired"
    else:
        status = "not_authorized"

    if config.VERBOSE:
        print(f"   🔍 check_plate: {plate} → {status}")

    return {"status": status, "plate": plate, "plate_info": plate_info or {}}


@app.get("/plates/{plate_number}", summary="Dettaglio targa")
def get_plate(plate_number: str):
    plate = db.get_plate(plate_number.upper())
    if not plate:
        raise HTTPException(status_code=404, detail="Targa non trovata")
    return dict(plate)


@app.put("/plates/{plate_number}", summary="Aggiorna targa")
def update_plate(plate_number: str, data: PlateUpdate):
    db.update_plate(
        plate_number.upper(),
        data.first_name,
        data.last_name,
        data.role,
        data.expiration_date,
    )
    return {"ok": True}


@app.delete("/plates/{plate_number}", summary="Rimuovi targa")
def delete_plate(plate_number: str):
    ok = db.remove_plate(plate_number.upper())
    if not ok:
        raise HTTPException(status_code=404, detail="Targa non trovata")
    return {"ok": True}


# ── Access logs ───────────────────────────────────────────────────────────────

@app.post("/access/log", status_code=201, summary="Registra accesso")
def log_access(data: LogAccessRequest):
    db.log_access(
        plate_number=data.plate.upper().strip(),
        status=data.status,
        event=data.event,
    )
    if config.VERBOSE:
        print(f"   📝 log_access: {data.plate} | {data.status} | {data.event}")
    return {"ok": True}


@app.get("/access/logs", summary="Storico accessi (base)")
def get_access_history(
    plate_number: Optional[str] = None,
    limit: int = Query(default=10_000_000, ge=0),
    date: Optional[str] = None,
    status: Optional[str] = None,
):
    return db.get_access_history(
        plate_number=plate_number,
        limit=limit,
        date=date,
        status=status,
    )


@app.get("/access/logs/advanced", summary="Storico accessi (filtri avanzati)")
def get_access_history_advanced(
    plate_number: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    date_single: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=100, ge=0),
):
    return db.get_access_history_advanced(
        plate_number=plate_number,
        first_name=first_name,
        last_name=last_name,
        role=role,
        status=status,
        date_single=date_single,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@app.delete("/access/logs", summary="Elimina log per ID")
def delete_logs(data: DeleteLogsRequest):
    deleted = db.delete_logs_by_ids(data.log_ids)
    return {"deleted": deleted}


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

@app.get("/persons", summary="Tutte le persone con le loro targhe")
def get_all_persons(q: Optional[str] = None):
    if q and q.strip():
        return db.search_persons(q.strip())
    return db.get_all_persons()


@app.post("/persons", status_code=201, summary="Aggiungi persona")
def add_person(data: PersonCreate):
    person_id = db.add_person(data.first_name, data.last_name, data.role, data.notes)
    if person_id < 0:
        raise HTTPException(status_code=500, detail="Errore durante l'aggiunta della persona")
    return {"ok": True, "person_id": person_id}


@app.get("/persons/{person_id}", summary="Dettaglio persona")
def get_person(person_id: int):
    person = db.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    return person


@app.put("/persons/{person_id}", summary="Aggiorna persona")
def update_person(person_id: int, data: PersonUpdate):
    ok = db.update_person(person_id, data.first_name, data.last_name, data.role, data.notes)
    if not ok:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    return {"ok": True}


@app.delete("/persons/{person_id}", summary="Elimina persona e le sue targhe")
def delete_person(person_id: int):
    ok = db.delete_person(person_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    return {"ok": True}


@app.post("/persons/{person_id}/plates", status_code=201, summary="Aggiungi targa a persona")
def add_plate_to_person(person_id: int, data: PlateToPersonCreate):
    ok = db.add_plate_to_person(person_id, data.plate_number, data.expiration_date, data.notes)
    if not ok:
        raise HTTPException(status_code=409, detail="Targa già esistente o persona non trovata")
    return {"ok": True}