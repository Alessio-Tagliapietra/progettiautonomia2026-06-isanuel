import os

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

TOPIC_DB_QUERY    = "db/query"
TOPIC_DB_RESPONSE = "db/response"

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "authorized_plates.db")

VERBOSE = True