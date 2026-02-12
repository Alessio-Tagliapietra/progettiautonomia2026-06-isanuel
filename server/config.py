"""
File di configurazione, contiene tutti i parametri utilizzati nel codice.
Modificare solo se necessario
"""

try:
    import os
    import torch
    from dotenv import load_dotenv

except ImportError as e:
    print(f"Errore nel caricamento dei moduli in config.py: {e}")


# Carica variabili segrete ambiente da .env
load_dotenv()


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # 'cuda' o 'cpu'

FRAME_SOURCE = (
    "non-local"  # "local utilizza la camera o video, non-local utilizza la frame queue
)

# se FRAME_SOURCE è "local", specificare il percorso del video o usare la webcam:
# Video o webcam
USE_WEBCAM = False  # Se True, usa la webcam invece del video (VIDEO_PATH)

# ============================================================================
# PATH BASE PROGETTO
# ============================================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(APP_DIR, "data")
IMAGE_RESULTS_DIR = os.path.join(DATA_DIR, "image_results")
PLATE_IMAGES_DIR = os.path.join(IMAGE_RESULTS_DIR, "detected_plates")
PLATE_IMAGES_DIR_DEBUG = os.path.join(IMAGE_RESULTS_DIR, "debug_plates")
VEHICLE_IMAGES_DIR = os.path.join(IMAGE_RESULTS_DIR, "detected_vehicles")

# ============================================================================
# PATH FILE PROGETTO
# ============================================================================
TXT_PATH = os.path.join(DATA_DIR, "authorized_plates.txt")
DATABASE_PATH = os.path.join(DATA_DIR, "authorized_plates.db")

VIDEO_PATH = os.path.join(PROJECT_ROOT, "test_input", "video3.mp4")

OUTPUT_CSV = os.path.join(DATA_DIR, "detected_plates.csv")


# ======== Modelli YOLO ===========
COCO_MODEL_PATH = os.path.join(MODELS_DIR, "yolo", "yolov8n.pt")
PLATE_MODEL_PATH = os.path.join(MODELS_DIR, "yolo", "license_plate_detector.pt")


# ============================================================================
# CLASSI DA RILEVARE (COCO Dataset)
# ============================================================================

# ID classi COCO: https://github.com/ultralytics/yolov5/blob/master/data/coco.yaml
CLASSES_TO_DETECT = [1, 2, 3, 5, 7]
# 1: bicycle
# 2: car
# 3: motorcycle
# 5: bus
# 7: truck

# Veicoli a 4 ruote (richiedono controllo targa)
VEHICLES_4_WHEELS = [2, 5, 7]  # car, bus, truck

# Veicoli a 2 ruote (sempre autorizzati - no controllo targa)
VEHICLES_2_WHEELS = [1, 3]  # bicycle, motorcycle


# ============================================================================
# SOGLIE DI DETECTION
# ============================================================================

# Confidenza minima per accettare una detection veicolo/pedone
DETECTION_CONFIDENCE = 0.2

# Confidenza minima per detection targhe
PLATE_DETECTION_CONFIDENCE = 0.2  # Range: 0.0-1.0

# Confidenza minima OCR per accettare la lettura
OCR_MIN_CONFIDENCE = 0.7  # Range: 0.0-1.0


# ============================================================================
# PARAMETRI TRACKER (SORT)
# ============================================================================

TRACKER_MAX_AGE = 30  # Frame massimi senza detection prima di perdere il track
TRACKER_MIN_HITS = 3  # Detection minime prima di confermare un track
TRACKER_IOU_THRESHOLD = 0.3  # Soglia IoU per associare detection a track


# ============================================================================
# PARAMETRI OCR
# ============================================================================

USE_GPU = DEVICE == "cuda"
TESSERACT_AVAILABLE = True
FAST_OCR_AVAILABLE = True  # Fast Plate OCR
USE_FAST_OCR = True  # mettere False per usare solo tesseract
TESSERACT_CMD_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Percorso eseguibile Tesseract
)


# ============================================================================
# PREPROCESSING IMMAGINI
# ============================================================================

# Dimensioni target per il ridimensionamento della targa
TARGET_HEIGHT = 120

# Fattore di scala per preprocessing veicolo
# VEHICLE_SCALE_FACTOR = 1.5 # non implementato, non necessario al momento

# Margine per crop veicolo (pixel),
# evitare di tagliare parti della targa
VEHICLE_CROP_MARGIN = 10


# ============================================================================
# VISUALIZZAZIONE
# ============================================================================

# Mostra finestra video in tempo reale
SHOW_VIDEO = False  # SOLO PER DEBUG!

# Dimensioni finestra visualizzazione
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

# Spessore linee bounding box
BOX_THICKNESS = 2

# Dimensione font label
FONT_SCALE = 0.8

# Colori (BGR format)
COLORS = {
    "authorized": (0, 255, 0),  # Verde
    "not_authorized": (0, 0, 255),  # Rosso
    "pedestrian": (255, 0, 0),  # Blu
    "to_check": (128, 128, 128),  # Grigio
}

# Output
BATCH_SIZE = 2  # Numero di frame da processare in batch


# ============================================================================
# DEBUG E LOGGING
# ============================================================================

# Stampa log dettagliati
VERBOSE = True

# Salva immagini delle targhe rilevate e veicoli rilevati
# sconsigliato in produzione per lo spazio su disco: SOLO PER DEBUG!
SAVE_PLATE_IMAGES = False
SAVE_DEBUG_PLATES = False  # immagini modificate dal preprocessing OCR
SAVE_VEHICLE_IMAGES = False


# Frequenza stampa progress (ogni N frames)
PROGRESS_INTERVAL = 100

# ============================================================================
# AUTENTICAZIONE OAUTH
# ============================================================================

#======= impostazioni OAUTH Google da modificare con le proprie =======
SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/callback"
# elenco utenti autorizzati (email)
AUTHORIZED_USERS = [
    "manuel.sannicolo07@marconirovereto.it",
    "sannicolomanuel@gmail.com",
]

# ============================================================================
# HTTPS SERVER
# ============================================================================

# elenco dei client autorizzati (camera-id: api-key)
AUTHORIZED_CAMERAS = {
    "camera_client01": "g9f3e1d7c4b84eab9f5c1d2e3a4b57kd"  # ID: API Key
}

REQUIRE_CAMERA_AUTH = True


# ============================================================================
# CARICA TARGHE AUTORIZZATE
# ============================================================================

# Targhe fallback se il database e file .txt non è disponibile
# Lista hardcoded, Fallback di secondo livello
FALLBACK_AUTHORIZED_PLATES = [
    "NA13NRU",
    "GX15OGJ",
    "MW51VSU",
]


def load_plates_from_txt():
    plates = []

    if not os.path.exists(TXT_PATH):
        print(f"⚠️ File targhe non trovato: {TXT_PATH}")
        return plates

    try:
        with open(TXT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                plate = line.strip().upper().replace(",", "").replace(";", "")
                if plate:
                    plates.append(plate)

        print(f"📝 Caricate {len(plates)} targhe da file TXT")
        return plates

    except Exception as e:
        print(f"❌ Errore lettura file TXT: {e}")
        return []


def load_authorized_plates():
    """
    Carica le targhe autorizzate dal database o file TXT
    Ritorna lista di targhe valide
    """

    print(f"🔄 Caricamento targhe autorizzate...")
    try:
        from server.database import DatabaseManager

        if os.path.exists(DATABASE_PATH):
            db = DatabaseManager(DATABASE_PATH)
            plates = db.get_all_valid_plates()
            db.close()

            if plates:
                print(f"✅ Caricate {len(plates)} targhe dal database")
                return plates

            print("⚠️ Database vuoto, provo file TXT")

        else:
            print(f"⚠️ Database non trovato: {DATABASE_PATH}")

    except Exception as e:
        print(f"❌ Errore accesso DB: {e}")
        print("➡️ Fallback su file TXT")

    # Fallback di primo livello su file TXT 
    plates_from_txt = load_plates_from_txt()
    if plates_from_txt and len(plates_from_txt) > 0:
        return plates_from_txt

    # Fallback di secondo livello su lista hardcoded
    return FALLBACK_AUTHORIZED_PLATES


# Carica targhe all'import del modulo
ALL_AUTHORIZED_PLATES = []  # caricate in main.py


# ============================================================================
# VALIDAZIONE CONFIGURAZIONE
# ============================================================================


# check effettuato in main.py
def validate_config():
    """Verifica che la configurazione sia valida"""
    errors = []

    # Check files esistenti
    if not os.path.exists(COCO_MODEL_PATH):
        errors.append(f"Modello COCO non trovato: {COCO_MODEL_PATH}")

    if not os.path.exists(PLATE_MODEL_PATH):
        errors.append(f"Modello targhe non trovato: {PLATE_MODEL_PATH}")

    if not USE_WEBCAM and not os.path.exists(VIDEO_PATH):
        errors.append(f"Video non trovato: {VIDEO_PATH}")

    # Check valori soglie
    if not 0 <= PLATE_DETECTION_CONFIDENCE <= 1:
        errors.append("PLATE_DETECTION_CONFIDENCE deve essere tra 0 e 1")

    if not 0 <= OCR_MIN_CONFIDENCE <= 1:
        errors.append("OCR_MIN_CONFIDENCE deve essere tra 0 e 1")

    # Check targhe autorizzate
    if len(ALL_AUTHORIZED_PLATES) == 0:
        errors.append("Nessuna targa autorizzata configurata!")

    if BATCH_SIZE < 1:
        errors.append("BATCH_SIZE deve essere almeno 1")

    if not os.path.exists(DATABASE_PATH):
        errors.append(f"Database non trovato: {DATABASE_PATH}")
        
    if SECRET_KEY is None or SECRET_KEY == "":
        errors.append("SECRET_KEY non è impostata nelle variabili ambiente")
        
    if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_ID == "":
        errors.append("GOOGLE_CLIENT_ID non è impostata nelle variabili ambiente")
        
    if GOOGLE_CLIENT_SECRET is None or GOOGLE_CLIENT_SECRET == "":
        errors.append("GOOGLE_CLIENT_SECRET non è impostata nelle variabili ambiente")

    # Crea directory output se non esistono
    if SAVE_PLATE_IMAGES:
        os.makedirs(PLATE_IMAGES_DIR, exist_ok=True)

    if SAVE_VEHICLE_IMAGES:
        os.makedirs(VEHICLE_IMAGES_DIR, exist_ok=True)

    if SAVE_DEBUG_PLATES:
        os.makedirs(PLATE_IMAGES_DIR_DEBUG, exist_ok=True)

    if errors:
        print("❌ ERRORI DI CONFIGURAZIONE:")
        for error in errors:
            print(f"   - {error}")
        return False

    return True


if __name__ == "__main__":
    # Test configurazione
    print("🔧 Test configurazione...")
    ALL_AUTHORIZED_PLATES = load_authorized_plates()
    if validate_config():
        print("✅ Configurazione valida!")
        print(f"\n📋 Targhe autorizzate: {len(ALL_AUTHORIZED_PLATES)}")
        for plate in ALL_AUTHORIZED_PLATES[:5]:
            print(f"   - {plate}")
        if len(ALL_AUTHORIZED_PLATES) > 5:
            print(f"   ... e altre {len(ALL_AUTHORIZED_PLATES) - 5}")

        print(ALL_AUTHORIZED_PLATES)
    else:
        print("❌ Configurazione non valida!")
