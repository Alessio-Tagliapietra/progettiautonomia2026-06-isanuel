import cv2
import time
from modules.reader.detection import detect_vehicles, update_tracking
from modules.reader.vehicle_utils import process_detections
from modules.reader.mqtt_publisher import MQTTPublisher
from fast_plate_ocr import LicensePlateRecognizer
from ultralytics import YOLO
from sort.sort import Sort
import modules.reader.config as config
from modules.webApp.service_controller import service


class Models:
    def __init__(self, coco_model, plate_model, recognizer, tracker):
        self.coco_model = coco_model
        self.plate_model = plate_model
        self.recognizer = recognizer
        self.tracker = tracker


def initialize() -> Models:
    if config.VERBOSE:
        print("🔧 Inizializzazione modelli...")

    # YOLO
    coco_model = YOLO(config.COCO_MODEL_PATH)
    plate_model = YOLO(config.PLATE_MODEL_PATH)

    # Tesseract
    try:
        import pytesseract
        config.TESSERACT_AVAILABLE = True
        if config.VERBOSE: print("✅ Tesseract disponibile")
    except ImportError:
        config.TESSERACT_AVAILABLE = False
        if config.VERBOSE: print("❌ Tesseract non disponibile")

    # Fast Plate OCR
    recognizer = None
    try:
        recognizer = LicensePlateRecognizer("cct-xs-v1-global-model")
        config.FAST_OCR_AVAILABLE = True
        if config.VERBOSE: print("✅ LPR disponibile")
    except Exception as e:
        config.FAST_OCR_AVAILABLE = False
        if config.VERBOSE: print(f"❌ LPR non disponibile: {e}")

    # Tracker
    tracker = Sort(
        max_age=config.TRACKER_MAX_AGE,
        min_hits=config.TRACKER_MIN_HITS,
        iou_threshold=config.TRACKER_IOU_THRESHOLD,
    )

    return Models(coco_model, plate_model, recognizer, tracker)


def main():
    models = initialize()
    publisher = MQTTPublisher(config.MQTT_BROKER, config.MQTT_PORT)
    cap = cv2.VideoCapture(config.RTSP_URL)
    checked_vehicles = {}
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # ── Controllo servizio ──────────────────────────────────────────────
        if not service.is_active():
            # Servizio disattivo: scarta il frame senza elaborarlo.
            # La camera continua a girare, ma CPU/GPU rimangono libere.
            time.sleep(0.1)   # evita busy-loop a 100% CPU
            continue
        # ───────────────────────────────────────────────────────────────────

        detections = detect_vehicles(frame, models.coco_model)
        detections = update_tracking(detections, models.tracker)
        process_detections(
            detections, frame, frame_count,
            checked_vehicles, config.GATE_ID, publisher, models
        )

        frame_count += 1

    cap.release()


if __name__ == "__main__":
    main()

