import os
from dotenv import load_dotenv
load_dotenv()

# Flask
SECRET_KEY = os.getenv("SECRET_KEY")

# OAuth Google
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI         = "http://localhost:5000/callback"


# Calendar Google

# Google Calendar — Service Account (sostituisce gcal_credentials.json)
CALENDAR_ID       = os.getenv("CALENDAR_ID")
GCAL_SERVICE_ACCOUNT_INFO = {
    "type":                        os.getenv("GCAL_TYPE", "service_account"),
    "project_id":                  os.getenv("GCAL_PROJECT_ID"),
    "private_key_id":              os.getenv("GCAL_PRIVATE_KEY_ID"),
    "private_key":                 os.getenv("GCAL_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email":                os.getenv("GCAL_CLIENT_EMAIL"),
    "client_id":                   os.getenv("GCAL_CLIENT_ID"),
    "auth_uri":                    os.getenv("GCAL_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
    "token_uri":                   os.getenv("GCAL_TOKEN_URI", "https://oauth2.googleapis.com/token"),
    "auth_provider_x509_cert_url": os.getenv("GCAL_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
    "client_x509_cert_url":        os.getenv("GCAL_CLIENT_CERT_URL"),
    "universe_domain":             os.getenv("GCAL_UNIVERSE_DOMAIN", "googleapis.com"),
}

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