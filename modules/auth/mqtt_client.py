"""
mqtt_client.py
Gestisce tutta la comunicazione MQTT del modulo auth.
Pattern db/query → db/response con correlation_id.
"""
import json
import threading
import uuid
from datetime import datetime
from typing import Callable

import paho.mqtt.client as mqtt
import modules.auth.config as config


class AuthMQTTClient:

    def __init__(self, on_plate_detected: Callable):
        self._on_plate_detected = on_plate_detected

        # pending_requests: correlation_id → {"event": Event, "response": dict|None}
        self._pending: dict = {}
        self._lock = threading.Lock()

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ── Connessione ────────────────────────────────────────────────────────

    def connect(self):
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if config.VERBOSE:
            print(f"✅ Auth connesso al broker MQTT (rc={rc})")
        client.subscribe(config.TOPIC_PLATES_DETECTED)
        client.subscribe(config.TOPIC_DB_RESPONSE)

    # ── Ricezione messaggi ─────────────────────────────────────────────────

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            return

        if msg.topic == config.TOPIC_PLATES_DETECTED:
            # Esegui in thread separato per non bloccare il loop MQTT
            threading.Thread(
                target=self._on_plate_detected,
                args=(payload,),
                daemon=True
            ).start()

        elif msg.topic == config.TOPIC_DB_RESPONSE:
            corr_id = payload.get("correlation_id")
            if not corr_id:
                return
            with self._lock:
                if corr_id in self._pending:
                    self._pending[corr_id]["response"] = payload
                    self._pending[corr_id]["event"].set()

    # ── Request/Response verso il database ────────────────────────────────

    def query_db(self, action: str, plate: str) -> dict | None:
        """
        Invia una query al modulo database e attende la risposta.

        Args:
            action: "check_plate" | "log_access"
            plate: numero targa

        Returns:
            dict con la risposta, oppure None se timeout
        """
        corr_id = str(uuid.uuid4())
        event = threading.Event()

        with self._lock:
            self._pending[corr_id] = {"event": event, "response": None}

        payload = {
            "correlation_id": corr_id,
            "action": action,
            "plate": plate,
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(config.TOPIC_DB_QUERY, json.dumps(payload))

        # Attendi risposta con timeout
        received = event.wait(timeout=config.DB_RESPONSE_TIMEOUT)

        with self._lock:
            result = self._pending.pop(corr_id, {}).get("response")

        if not received:
            print(f"⚠️  Timeout risposta DB per {plate} (action={action})")
            return None

        return result

    # ── Publish ────────────────────────────────────────────────────────────

    def publish_result(self, plate: str, status: str, gate_id: str, plate_info: dict = None):
        payload = {
            "plate": plate,
            "status": status,
            "gate_id": gate_id,
            "plate_info": plate_info or {},
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(config.TOPIC_PLATES_RESULT, json.dumps(payload))

    def publish_log(self, plate: str, status: str, gate_id: str, event: str):
        payload = {
            "plate": plate,
            "status": status,
            "gate_id": gate_id,
            "event": event,
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(config.TOPIC_LOGS_NEW, json.dumps(payload))

    def publish_gate_command(self, gate_id: str, action: str, plate: str):
        payload = {
            "gate_id": gate_id,
            "action": action,   # "open" | "deny"
            "plate": plate,
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(config.TOPIC_GATE_COMMAND, json.dumps(payload))