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
# PARAMETRI CONTROLLO DISTANZA E ACCESSI
# ============================================================================

# Soglia di distanza per considerare un veicolo "abbastanza vicino"
# Range: 0.0-1.0, dove 0 = molto vicino, 1 = molto lontano
# Valori tipici: 0.3-0.7
DISTANCE_THRESHOLD = 0.5

# Intervallo minimo tra due entrate consecutive della stessa targa (secondi)
# Evita rilevazioni duplicate quando il veicolo passa lentamente
MIN_ENTRY_INTERVAL_SECONDS = 10

# Intervallo minimo tra l'ultima rilevazione e un'uscita (secondi)
# Come da specifica: almeno 60 secondi dall'ultima rilevazione
MIN_EXIT_INTERVAL_SECONDS = 60

# Pulizia automatica dei record vecchi nel tracker (ore)
ACCESS_TRACKER_CLEANUP_HOURS = 24

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


# MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883



GATE_ID  = os.getenv("GATE_ID",  "entrata")
RTSP_URL = os.getenv("RTSP_URL", "rtsp://localhost:8554/camera1")

# ============================================================================
# Avvio delle due istanze in produzione (terminale / systemd):
#
# Istanza 1 — telecamera ingresso:
#   GATE_ID=entrata RTSP_URL=rtsp://192.168.1.10:8554/cam_entrata python -m modules.reader.reader
#
# Istanza 2 — telecamera uscita:
#   GATE_ID=uscita  RTSP_URL=rtsp://192.168.1.11:8554/cam_uscita  python -m modules.reader.reader
#
# Il modulo auth è uno solo e gestisce entrambi i gate_id.
# ============================================================================