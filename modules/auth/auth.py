"""
auth.py
Entry point del modulo auth.
Flusso: plates/detected → check DB → gate → log
"""
import csv
import os
import time
from datetime import datetime

import modules.auth.config as config
from modules.auth.mqtt_client import AuthMQTTClient
from modules.auth.gate_controller import open_gate, deny_gate
from modules.auth.access_tracker import access_tracker


# ── Log CSV ────────────────────────────────────────────────────────────────

def log_to_csv(plate: str, status: str, gate_id: str, event: str):
    os.makedirs(os.path.dirname(config.OUTPUT_CSV), exist_ok=True)
    with open(config.OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), plate, status, gate_id, event])


# ── Logica principale ──────────────────────────────────────────────────────

def handle_plate(payload: dict, mqtt: AuthMQTTClient):
    plate      = payload.get("plate", "")
    confidence = payload.get("confidence", 0.0)
    gate_id    = payload.get("gate_id", "unknown")
    v_type     = payload.get("vehicle_type", "4wheels")
    event      = "entrata"   # TODO: distinguere entrata/uscita con gate_id o topic

    if config.VERBOSE:
        print(f"\n{'='*55}")
        print(f"📨 Ricevuto: {plate} | conf={confidence:.2f} | gate={gate_id}")

    # ── Veicolo a 2 ruote: autorizzato senza check DB ─────────────────────
    if v_type == "2wheels":
        if config.VERBOSE:
            print(f"   🛵 Veicolo 2 ruote ({plate}) → autorizzato automaticamente")

        open_gate(gate_id, reason="2wheels")

        mqtt.publish_result(plate, "authorized_2wheels", gate_id)
        mqtt.publish_log(plate, "authorized_2wheels", gate_id, event)
        mqtt.publish_gate_command(gate_id, "open", plate)
        log_to_csv(plate, "authorized_2wheels", gate_id, event)
        return

    # ── Veicolo a 4 ruote: controlla access tracker ───────────────────────────
    if not access_tracker.can_process_entry(plate, gate_id):
        if config.VERBOSE:
            print("   ⏱️  Entrata scartata: troppo recente")
        return

    # ── Query al database via MQTT ─────────────────────────────────────────
    if config.VERBOSE:
        print(f"   🔍 Interrogo DB per {plate}...")

    db_response = mqtt.query_db("check_plate", plate)

    # Timeout o errore DB → nega per sicurezza
    if db_response is None:
        status = "db_error"
        deny_gate(gate_id, reason="db_timeout")
    else:
        status     = db_response.get("status", "not_authorized")
        plate_info = db_response.get("plate_info", {})

        if config.VERBOSE:
            print(f"   📋 Risposta DB: {status} | info: {plate_info}")

        if status == "authorized":
            open_gate(gate_id, reason=f"targa {plate} autorizzata")
            access_tracker.register_entry(plate, gate_id)
            mqtt.publish_gate_command(gate_id, "open", plate)
        else:
            deny_gate(gate_id, reason=status)
            mqtt.publish_gate_command(gate_id, "deny", plate)

    # ── Pubblica risultato e log ───────────────────────────────────────────
    mqtt.publish_result(plate, status, gate_id, plate_info if db_response else {})
    mqtt.publish_log(plate, status, gate_id, event)

    # Log anche sul DB (fire-and-forget, non aspettiamo risposta)
    mqtt.client.publish(
        config.TOPIC_DB_QUERY,
        __import__("json").dumps({
            "action": "log_access",
            "plate": plate,
            "status": status,
            "event": event,
            "gate_id": gate_id,
            "timestamp": datetime.now().isoformat()
        })
    )
    log_to_csv(plate, status, gate_id, event)


# ── Entry point ────────────────────────────────────────────────────────────

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


if __name__ == "__main__":
    main()
