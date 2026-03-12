"""
database_service.py
Entry point del modulo database.
Ascolta su db/query, esegue l'operazione, risponde su db/response.

Azioni supportate:
- check_plate  → verifica autorizzazione targa
- log_access   → registra accesso nel log
"""
import json
import time
import threading
import paho.mqtt.client as mqtt

import modules.database.config as config
from modules.database.database import DatabaseManager


# ── Istanza DB (condivisa, thread-safe grazie a check_same_thread=False) ──
db = DatabaseManager()


# ── Handlers per ogni azione ──────────────────────────────────────────────

def handle_check_plate(payload: dict) -> dict:
    plate = payload.get("plate", "").upper().strip()

    if not plate:
        return {"status": "error", "message": "plate mancante"}

    is_authorized, plate_info = db.is_plate_authorized(plate)

    if is_authorized:
        status = "authorized"
    elif plate_info and plate_info.get("status") == "expired":
        status = "expired"
    else:
        status = "not_authorized"

    if config.VERBOSE:
        print(f"   🔍 check_plate: {plate} → {status}")

    return {
        "status": status,
        "plate": plate,
        "plate_info": plate_info or {}
    }


def handle_log_access(payload: dict) -> dict:
    plate   = payload.get("plate", "").upper().strip()
    status  = payload.get("status", "")
    event   = payload.get("event", "entrata")

    if not plate or not status:
        return {"status": "error", "message": "plate o status mancanti"}

    db.log_access(plate_number=plate, status=status, event=event)

    if config.VERBOSE:
        print(f"   📝 log_access: {plate} | {status} | {event}")

    return {"status": "ok"}


# ── Dispatcher ────────────────────────────────────────────────────────────

HANDLERS = {
    "check_plate": handle_check_plate,
    "log_access":  handle_log_access,
}


def process_query(payload: dict, client: mqtt.Client):
    """Processa una query e pubblica la risposta."""
    action     = payload.get("action", "")
    corr_id    = payload.get("correlation_id")

    handler = HANDLERS.get(action)

    if handler is None:
        print(f"⚠️  Azione sconosciuta: {action}")
        result = {"status": "error", "message": f"azione '{action}' non supportata"}
    else:
        try:
            result = handler(payload)
        except Exception as e:
            print(f"❌ Errore handler '{action}': {e}")
            result = {"status": "error", "message": str(e)}

    # Rispondi solo se c'è un correlation_id (log_access è fire-and-forget)
    if corr_id:
        response = {"correlation_id": corr_id, **result}
        client.publish(config.TOPIC_DB_RESPONSE, json.dumps(response))


# ── MQTT ──────────────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc):
    if config.VERBOSE:
        print(f"✅ Database connesso al broker MQTT (rc={rc})")
    client.subscribe(config.TOPIC_DB_QUERY)
    print(f"📡 In ascolto su '{config.TOPIC_DB_QUERY}'...")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        print("⚠️  Messaggio non valido (non è JSON)")
        return

    # Processa in thread separato per non bloccare il loop MQTT
    threading.Thread(
        target=process_query,
        args=(payload, client),
        daemon=True
    ).start()


# ── Entry point ───────────────────────────────────────────────────────────

def main():
    print("🚀 Avvio modulo DATABASE...")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(config.MQTT_BROKER, config.MQTT_PORT)
    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Database service fermato.")
        client.loop_stop()
        client.disconnect()
        db.close()


if __name__ == "__main__":
    main()
