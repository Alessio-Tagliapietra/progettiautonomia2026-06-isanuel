import paho.mqtt.client as mqtt
import json
from datetime import datetime

class MQTTPublisher:
    def __init__(self, broker, port, topic="plates/detected"):
        self.client = mqtt.Client()
        self.client.connect(broker, port)
        self.topic = topic

    def publish_plate(self, plate_text, confidence, gate_id, vehicle_type="4wheels"):
        payload = {
            "plate": plate_text,
            "confidence": confidence,
            "gate_id": gate_id,
            "vehicle_type": vehicle_type,
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(self.topic, json.dumps(payload))