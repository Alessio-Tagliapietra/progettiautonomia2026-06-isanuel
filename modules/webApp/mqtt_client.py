"""
mqtt_client.py
La webApp ascolta logs/new per aggiornamenti real-time
e pubblica plates/update quando aggiunge/modifica/rimuove targhe.
"""
import json
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import modules.webApp.config as config

# Ultimi log ricevuti via MQTT (buffer in memoria, max 100)
_recent_logs = []
_lock = threading.Lock()


def get_recent_logs(limit: int = 20) -> list:
    with _lock:
        return _recent_logs[-limit:]


def _on_connect(client, userdata, flags, rc):
    if config.VERBOSE:
        print(f"✅ WebApp MQTT connessa (rc={rc})")
    client.subscribe(config.TOPIC_LOGS_NEW)


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        with _lock:
            _recent_logs.append(payload)
            # mantieni solo gli ultimi 100
            if len(_recent_logs) > 100:
                _recent_logs.pop(0)
    except Exception:
        pass


# ── Client globale ─────────────────────────────────────────────────────────
_client = mqtt.Client()
_client.on_connect = _on_connect
_client.on_message = _on_message


def start():
    _client.connect(config.MQTT_BROKER, config.MQTT_PORT)
    _client.loop_start()


def publish_plates_update(action: str, plate: str):
    """
    Notifica gli altri moduli che le targhe autorizzate sono cambiate.
    action: "add" | "update" | "remove"
    """
    payload = {
        "action": action,
        "plate": plate,
        "timestamp": datetime.now().isoformat()
    }
    _client.publish(config.TOPIC_PLATES_UPDATE, json.dumps(payload))