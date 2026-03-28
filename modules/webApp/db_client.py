"""
db_client.py — Client HTTP per la REST API del database.
Drop-in replacement per DatabaseManager.
"""

import json as _json
from typing import Optional, List, Dict, Tuple
import httpx


class DbClient:

    def __init__(self, base_url: str = "http://localhost:8001", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ── Helper privati ────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict = None):
        resp = self._client.get(path, params={k: v for k, v in (params or {}).items() if v is not None})
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: dict = None):
        resp = self._client.post(path, json=json or {})
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, json: dict = None):
        resp = self._client.put(path, json=json or {})
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str, json: dict = None):
        # httpx.Client.delete() non accetta json= in tutte le versioni;
        # usiamo request() che funziona sempre.
        resp = self._client.request(
            "DELETE", path,
            content=_json.dumps(json or {}).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Plates ────────────────────────────────────────────────────────────────

    def get_all_plates(self) -> List[Dict]:
        return self._get("/plates")

    def get_plate(self, plate_number: str) -> Optional[Dict]:
        try:
            return self._get(f"/plates/{plate_number.upper()}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def add_authorized_plate(self, plate_number: str, first_name: str, last_name: str,
                              role: str, expiration_date: str = "", notes: str = "") -> bool:
        try:
            self._post("/plates", json={
                "plate_number": plate_number, "first_name": first_name,
                "last_name": last_name, "role": role,
                "expiration_date": expiration_date, "notes": notes,
            })
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return False
            raise

    def update_plate(self, plate_number: str, expiration_date: str = "",
                     notes: str = "", new_plate_number: str = None):
        payload = {"expiration_date": expiration_date, "notes": notes}
        if new_plate_number:
            payload["new_plate_number"] = new_plate_number.upper().strip()
        try:
            self._put(f"/plates/{plate_number.upper()}", json=payload)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                raise ValueError(e.response.json().get("detail", "Targa già esistente"))
            raise

    def remove_plate(self, plate_number: str) -> bool:
        try:
            self._delete(f"/plates/{plate_number.upper()}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    def is_plate_authorized(self, plate_number: str) -> Tuple[bool, Optional[Dict]]:
        data = self._post("/plates/check", json={"plate": plate_number})
        status = data.get("status")
        plate_info = data.get("plate_info") or None
        return status == "authorized", plate_info

    # ── Access logs ───────────────────────────────────────────────────────────

    def log_access(self, plate_number: str, status: str, event: str = "entrata"):
        self._post("/access/log", json={"plate": plate_number, "status": status, "event": event})

    def get_access_history(self, plate_number: str = None, limit: int = 10_000_000,
                            date: str = None, status: str = None) -> List[Dict]:
        return self._get("/access/logs", params={
            "plate_number": plate_number, "limit": limit, "date": date, "status": status,
        })

    def get_access_history_advanced(self, plate_number: str = None, first_name: str = None,
                                     last_name: str = None, role: str = None, status: str = None,
                                     date_single: str = None, date_from: str = None,
                                     date_to: str = None, limit: int = 100) -> List[Dict]:
        return self._get("/access/logs/advanced", params={
            "plate_number": plate_number, "first_name": first_name, "last_name": last_name,
            "role": role, "status": status, "date_single": date_single,
            "date_from": date_from, "date_to": date_to, "limit": limit,
        })

    def delete_logs_by_ids(self, log_ids: List[int]) -> int:
        data = self._delete("/access/logs", json={"log_ids": log_ids})
        return data.get("deleted", 0)

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_accessi_per_giorno(self, s, e): return self._get("/analytics/per-giorno", {"start_date": s, "end_date": e})
    def get_accessi_per_stato(self, s, e):  return self._get("/analytics/per-stato",  {"start_date": s, "end_date": e})
    def get_accessi_per_ora(self, s, e):    return self._get("/analytics/per-ora",    {"start_date": s, "end_date": e})
    def get_top_targhe(self, s, e, limit=10): return self._get("/analytics/top-targhe", {"start_date": s, "end_date": e, "limit": limit})
    def get_trend_per_stato(self, s, e):    return self._get("/analytics/trend",      {"start_date": s, "end_date": e})
    def get_kpi_entrate_uscite(self, s, e): return self._get("/analytics/kpi-entrate-uscite", {"start_date": s, "end_date": e})
    def get_distribuzione_entrate_uscite(self, s, e): return self._get("/analytics/distribuzione-ev", {"start_date": s, "end_date": e})
    def get_flusso_orario_entrate_uscite(self, s, e): return self._get("/analytics/flusso-orario",    {"start_date": s, "end_date": e})
    def get_saldo_giornaliero(self, s, e):  return self._get("/analytics/saldo-giornaliero", {"start_date": s, "end_date": e})

    # ── Persons ───────────────────────────────────────────────────────────────

    def get_all_persons(self) -> List[Dict]:
        return self._get("/persons")

    def search_persons(self, query: str) -> List[Dict]:
        return self._get("/persons", params={"q": query})

    def get_person(self, person_id: int) -> Optional[Dict]:
        try:
            return self._get(f"/persons/{person_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def add_person(self, first_name: str, last_name: str, role: str, notes: str = "") -> int:
        try:
            data = self._post("/persons", json={"first_name": first_name, "last_name": last_name,
                                                 "role": role, "notes": notes})
            return data.get("person_id", -1)
        except Exception:
            return -1

    def update_person(self, person_id: int, first_name: str, last_name: str, role: str, notes: str = "") -> bool:
        try:
            self._put(f"/persons/{person_id}", json={"first_name": first_name, "last_name": last_name,
                                                      "role": role, "notes": notes})
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    def delete_person(self, person_id: int) -> bool:
        try:
            self._delete(f"/persons/{person_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    def add_plate_to_person(self, person_id: int, plate_number: str,
                             expiration_date: str = "", notes: str = "") -> bool:
        try:
            self._post(f"/persons/{person_id}/plates", json={
                "plate_number": plate_number, "expiration_date": expiration_date, "notes": notes,
            })
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return False
            raise

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self):
        self._client.close()

    def __del__(self):
        try:
            self._client.close()
        except Exception:
            pass