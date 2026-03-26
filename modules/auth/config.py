import os

# MQTT
MQTT_BROKER = "localhost"
MQTT_PORT   = 1883

# Topic subscribe
TOPIC_PLATES_DETECTED = "plates/detected"

# Topic publish
TOPIC_GATE_COMMAND  = "gate/command"
TOPIC_LOGS_NEW      = "logs/new"
TOPIC_PLATES_RESULT = "plates/result"

# REST API del database
DB_API_URL = os.getenv("DB_API_URL", "http://localhost:8001")

# CSV log locale
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "data", "access_log.csv")

# Intervalli access tracker
MIN_ENTRY_INTERVAL_SECONDS   = 10
MIN_EXIT_INTERVAL_SECONDS     = 60
ACCESS_TRACKER_CLEANUP_HOURS  = 24

VERBOSE = True