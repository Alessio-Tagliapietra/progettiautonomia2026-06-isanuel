"""
auth.py
Entry point del modulo auth.
Flusso: plates/detected → REST API DB → gate → log

Gestione entrata/uscita:
  Il gate_id pubblicato da ogni istanza del reader determina il tipo di evento.
  - ENTRY_GATE_IDS (config): logica di autorizzazione completa, apre solo se autorizzato.
  - EXIT_GATE_IDS  (config): uscita sempre consentita, serve per tracciare il veicolo.
"""
import csv
import os
import time
from datetime import datetime

import modules.auth.config as config
from modules.auth.mqtt_client import AuthMQTTClient
from modules.auth.gate_controller import open_gate, deny_gate
from modules.auth.access_tracker import access_tracker
from modules.auth.db_client import DbClient


# ── Client DB (REST) ───────────────────────────────────────────────────────────
db = DbClient(config.DB_API_URL)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _gate_event_type(gate_id: str) -> str:
    """
    Restituisce "entrata" o "uscita" in base al gate_id.
    Se il gate_id non è riconosciuto, si assume entrata (comportamento conservativo).
    """
    gid = gate_id.lower().strip()
    if gid in config.EXIT_GATE_IDS:
        return "uscita"
    return "entrata"


def log_to_csv(plate: str, status: str, gate_id: str, event: str):
    os.makedirs(os.path.dirname(config.OUTPUT_CSV), exist_ok=True)
    with open(config.OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), plate, status, gate_id, event])


# ── Logica principale ──────────────────────────────────────────────────────────

def handle_plate(payload: dict, mqtt: AuthMQTTClient):
    plate      = payload.get("plate", "")
    confidence = payload.get("confidence", 0.0)
    gate_id    = payload.get("gate_id", "unknown")
    v_type     = payload.get("vehicle_type", "4wheels")

    # Determina il tipo di evento dal gate_id
    event = _gate_event_type(gate_id)

    if config.VERBOSE:
        print(f"\n{'='*55}")
        print(f"📨 Ricevuto: {plate} | conf={confidence:.2f} | gate={gate_id} | evento={event}")

    # ── Veicolo a 2 ruote: sempre autorizzato ─────────────────────────────────
    if v_type == "2wheels":
        if config.VERBOSE:
            print(f"   🛵 Veicolo 2 ruote ({plate}) → autorizzato automaticamente")

        open_gate(gate_id, reason="2wheels")
        mqtt.publish_result(plate, "authorized_2wheels", gate_id)
        mqtt.publish_log(plate, "authorized_2wheels", gate_id, event)
        mqtt.publish_gate_command(gate_id, "open", plate)
        log_to_csv(plate, "authorized_2wheels", gate_id, event)

        # Aggiorna il tracker anche per i 2 ruote
        if event == "entrata":
            access_tracker.register_entry(plate, gate_id)
        else:
            access_tracker.register_exit(plate, gate_id)
        return

    # ── Smista sulla logica corretta in base all'evento ───────────────────────
    if event == "entrata":
        _handle_entry(plate, gate_id, mqtt, event)
    else:
        _handle_exit(plate, gate_id, mqtt, event)


def _handle_entry(plate: str, gate_id: str, mqtt: AuthMQTTClient, event: str):
    """
    Logica entrata: controlla access tracker + autorizzazione DB.
    Apre il cancello solo se la targa è autorizzata e non scaduta.
    """
    # Throttle: evita doppia rilevazione dello stesso veicolo in entrata
    if not access_tracker.can_process_entry(plate, gate_id):
        if config.VERBOSE:
            print("   ⏱️  Entrata scartata: rilevazione troppo recente")
        return

    # Verifica autorizzazione via REST API
    if config.VERBOSE:
        print(f"   🔍 Interrogo DB per {plate}...")

    status     = "db_error"
    plate_info = {}

    try:
        is_authorized, info = db.is_plate_authorized(plate)
        plate_info = info or {}

        if is_authorized:
            status = "authorized"
        elif plate_info.get("status") == "expired":
            status = "expired"
        else:
            status = "not_authorized"

        if config.VERBOSE:
            print(f"   📋 Risposta DB: {status} | info: {plate_info}")

    except Exception as e:
        print(f"❌ Errore chiamata DB API: {e}")
        status = "db_error"

    # Apri / nega cancello
    if status == "authorized":
        open_gate(gate_id, reason=f"targa {plate} autorizzata")
        access_tracker.register_entry(plate, gate_id)
        mqtt.publish_gate_command(gate_id, "open", plate)
    else:
        deny_gate(gate_id, reason=status)
        mqtt.publish_gate_command(gate_id, "deny", plate)

    # Log e notifiche
    _publish_and_log(plate, status, gate_id, event, plate_info, mqtt)


def _handle_exit(plate: str, gate_id: str, mqtt: AuthMQTTClient, event: str):
    """
    Logica uscita: il cancello viene SEMPRE aperto (non si blocca un veicolo dentro).
    Il tracker viene interrogato solo per coerenza dei log; un veicolo non tracciato
    viene comunque lasciato uscire (es. sistema riavviato, entrata persa).
    """
    # Throttle uscita: evita doppia lettura del veicolo che esce lentamente
    if not access_tracker.can_process_exit(plate, gate_id):
        if config.VERBOSE:
            print("   ⏱️  Uscita scartata: rilevazione troppo recente")
        return

    # Il cancello di uscita si apre sempre
    open_gate(gate_id, reason=f"uscita {plate}")
    access_tracker.register_exit(plate, gate_id)
    mqtt.publish_gate_command(gate_id, "open", plate)

    # Per le uscite usiamo sempre status="authorized":
    # il veicolo è già dentro, l'autorizzazione fu verificata all'entrata.
    status = "authorized"

    if config.VERBOSE:
        print(f"   🚗 Uscita registrata: {plate} dal gate {gate_id}")

    _publish_and_log(plate, status, gate_id, event, {}, mqtt)


def _publish_and_log(plate: str, status: str, gate_id: str, event: str,
                     plate_info: dict, mqtt: AuthMQTTClient):
    """Pubblica risultato MQTT, logga su DB e su CSV."""
    try:
        db.log_access(plate_number=plate, status=status, event=event)
    except Exception as e:
        print(f"⚠️  Impossibile loggare l'accesso via API: {e}")

    mqtt.publish_result(plate, status, gate_id, plate_info)
    mqtt.publish_log(plate, status, gate_id, event)
    log_to_csv(plate, status, gate_id, event)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    print("🚀 Avvio modulo AUTH...")

    mqtt_client = AuthMQTTClient(
        on_plate_detected=lambda payload: handle_plate(payload, mqtt_client)
    )
    mqtt_client.connect()

    if config.VERBOSE:
        print(f"📡 In ascolto su '{config.TOPIC_PLATES_DETECTED}'...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Auth fermato.")
        mqtt_client.disconnect()
        db.close()


if __name__ == "__main__":
    main()