import os

# MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Topic subscribe
TOPIC_PLATES_DETECTED = "plates/detected"
TOPIC_DB_RESPONSE = "db/response"

# Topic publish
TOPIC_DB_QUERY = "db/query"
TOPIC_GATE_COMMAND = "gate/command"
TOPIC_LOGS_NEW = "logs/new"
TOPIC_PLATES_RESULT = "plates/result"

# Timeout attesa risposta dal db (secondi)
DB_RESPONSE_TIMEOUT = 5

# CSV log
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "data", "access_log.csv")

# Intervalli access tracker
MIN_ENTRY_INTERVAL_SECONDS = 10
MIN_EXIT_INTERVAL_SECONDS = 60
ACCESS_TRACKER_CLEANUP_HOURS = 24

VERBOSE = True