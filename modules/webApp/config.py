import os
from dotenv import load_dotenv
load_dotenv()

# Flask
SECRET_KEY = os.getenv("SECRET_KEY")

# OAuth Google
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI         = "http://localhost:5000/callback"

# REST API del database
DB_API_URL = os.getenv("DB_API_URL", "http://localhost:8001")

# Database utenti web autorizzati (accesso diretto: locale alla webapp)
USERS_DATABASE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "database", "data", "authorized_web_users.db"
)

# Email di seed: vengono inserite solo se il DB utenti è vuoto
SEED_AUTHORIZED_USERS = [
    "manuel.sannicolo07@marconirovereto.it",
    "sannicolomanuel@gmail.com",
]

# MQTT (usato solo per plates/update — notifiche ad altri moduli)
MQTT_BROKER         = "localhost"
MQTT_PORT           = 1883
TOPIC_LOGS_NEW      = "logs/new"
TOPIC_PLATES_UPDATE = "plates/update"

VERBOSE = True