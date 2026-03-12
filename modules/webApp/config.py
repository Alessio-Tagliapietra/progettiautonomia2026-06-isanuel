import os
from dotenv import load_dotenv
load_dotenv()

# Flask
SECRET_KEY = os.getenv("SECRET_KEY")

# OAuth Google
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI         = "http://localhost:5000/callback"

# Database targhe (accesso diretto)
DATABASE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "database", "data", "authorized_plates.db"
)

# Database utenti web autorizzati (separato)
USERS_DATABASE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "database", "data", "authorized_web_users.db"
)

# Email di seed: vengono inserite solo se il DB utenti è vuoto
SEED_AUTHORIZED_USERS = [
    "manuel.sannicolo07@marconirovereto.it",
    "sannicolomanuel@gmail.com",
]

# MQTT
MQTT_BROKER         = "localhost"
MQTT_PORT           = 1883
TOPIC_LOGS_NEW      = "logs/new"
TOPIC_PLATES_UPDATE = "plates/update"

VERBOSE = True