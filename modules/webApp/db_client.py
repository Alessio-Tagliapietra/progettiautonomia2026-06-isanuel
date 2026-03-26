"""
db_client.py
Client HTTP per la REST API del database.

Espone la stessa interfaccia di DatabaseManager in modo che i moduli
(webapp, auth) possano sostituire l'accesso diretto al DB con una
singola riga di cambio nell'inizializzazione:

    # Prima
    db = DatabaseManager(config.DATABASE_PATH)

    # Dopo
    db = DbClient(config.DB_API_URL)

Dipendenza:
    pip install httpx
"""

from typing import Optional, List, Dict, Tuple
import httpx


class DbClient:
    """
    Drop-in replacement per DatabaseManager.
    Tutte le operazioni vengono inoltrate alla REST API via HTTP.
    """

    def __init__(self, base_url: str = "http://localhost:8001", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ── Helper privato ────────────────────────────────────────────────────────

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
        resp = self._client.delete(path, json=json or {})
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

    def add_authorized_plate(
        self,
        plate_number: str,
        first_name: str,
        last_name: str,
        role: str,
        expiration_date: str = "",
        notes: str = "",
    ) -> bool:
        try:
            self._post("/plates", json={
                "plate_number": plate_number,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "expiration_date": expiration_date,
                "notes": notes,
            })
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return False  # già esistente
            raise

    def update_plate(
        self,
        plate_number: str,
        first_name: str,
        last_name: str,
        role: str,
        expiration_date: str = "",
    ):
        self._put(f"/plates/{plate_number.upper()}", json={
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "expiration_date": expiration_date,
        })

    def remove_plate(self, plate_number: str) -> bool:
        try:
            self._delete(f"/plates/{plate_number.upper()}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    def is_plate_authorized(self, plate_number: str) -> Tuple[bool, Optional[Dict]]:
        """
        Ritorna (is_authorized, plate_info) — stessa firma di DatabaseManager.
        """
        data = self._post("/plates/check", json={"plate": plate_number})
        status = data.get("status")
        plate_info = data.get("plate_info") or None
        return status == "authorized", plate_info

    # ── Access logs ───────────────────────────────────────────────────────────

    def log_access(self, plate_number: str, status: str, event: str = "entrata"):
        self._post("/access/log", json={
            "plate": plate_number,
            "status": status,
            "event": event,
        })

    def get_access_history(
        self,
        plate_number: str = None,
        limit: int = 10_000_000,
        date: str = None,
        status: str = None,
    ) -> List[Dict]:
        return self._get("/access/logs", params={
            "plate_number": plate_number,
            "limit": limit,
            "date": date,
            "status": status,
        })

    def get_access_history_advanced(
        self,
        plate_number: str = None,
        first_name: str = None,
        last_name: str = None,
        role: str = None,
        status: str = None,
        date_single: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        return self._get("/access/logs/advanced", params={
            "plate_number": plate_number,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "status": status,
            "date_single": date_single,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
        })

    def delete_logs_by_ids(self, log_ids: List[int]) -> int:
        data = self._delete("/access/logs", json={"log_ids": log_ids})
        return data.get("deleted", 0)

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_accessi_per_giorno(self, start_date: str, end_date: str) -> List[Dict]:
        return self._get("/analytics/per-giorno", {"start_date": start_date, "end_date": end_date})

    def get_accessi_per_stato(self, start_date: str, end_date: str) -> Dict:
        return self._get("/analytics/per-stato", {"start_date": start_date, "end_date": end_date})

    def get_accessi_per_ora(self, start_date: str, end_date: str) -> List[Dict]:
        return self._get("/analytics/per-ora", {"start_date": start_date, "end_date": end_date})

    def get_top_targhe(self, start_date: str, end_date: str, limit: int = 10) -> List[Dict]:
        return self._get("/analytics/top-targhe", {"start_date": start_date, "end_date": end_date, "limit": limit})

    def get_trend_per_stato(self, start_date: str, end_date: str) -> Dict:
        return self._get("/analytics/trend", {"start_date": start_date, "end_date": end_date})

    def get_kpi_entrate_uscite(self, start_date: str, end_date: str) -> Dict:
        return self._get("/analytics/kpi-entrate-uscite", {"start_date": start_date, "end_date": end_date})

    def get_distribuzione_entrate_uscite(self, start_date: str, end_date: str) -> Dict:
        return self._get("/analytics/distribuzione-ev", {"start_date": start_date, "end_date": end_date})

    def get_flusso_orario_entrate_uscite(self, start_date: str, end_date: str) -> List[Dict]:
        return self._get("/analytics/flusso-orario", {"start_date": start_date, "end_date": end_date})

    def get_saldo_giornaliero(self, start_date: str, end_date: str) -> List[Dict]:
        return self._get("/analytics/saldo-giornaliero", {"start_date": start_date, "end_date": end_date})

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self):
        self._client.close()

    def __del__(self):
        try:
            self._client.close()
        except Exception:
            pass