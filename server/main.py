"""
main.py

Sistema di riconoscimento veicoli e targhe.
"""

try:
    from ultralytics import YOLO
    import cv2
    from sort.sort import Sort
    import time
    import threading

    from fast_plate_ocr import LicensePlateRecognizer


except ImportError as e:
    print(f"❌ Errore nel caricamento dei moduli in main.py: {e}")

# ============================================================================
# IMPORT MODULI
# ============================================================================

try:
    import server.config as config

    if config.VERBOSE:
        print("✅ configurazione caricata da config.py")
except ImportError:
    print("❌ Errore nel caricamento di config.py")


try:
    from server.control.context import set_context

    if config.VERBOSE:
        print("✅ Context caricato da context.py")
except ImportError:
    print("❌ Errore caricamento di context.py")


try:
    from server.process.vehicle_utils import process_detections

    if config.VERBOSE:
        print("✅ Funzioni di utilità caricate dagli util")
except ImportError:
    print("❌ Errore nel caricamento degli util")


try:
    from server.process.detection import update_tracking, detect_vehicles

    if config.VERBOSE:
        print("✅ Funzioni di rilevamento caricate da detection")
except ImportError:
    print("❌ Errore nel caricamento di detection.py")


try:
    from server.process.visualize import Visualization

    if config.VERBOSE:
        print("✅ Visualizzazione caricata da visualize.py")
except ImportError:
    print("❌ Errore caricamento di visualize.py")


try:
    from server.database import DatabaseManager

    if config.VERBOSE:
        print("✅ DatabaseManager caricato da database.py")
except ImportError:
    print("❌ Errore caricamento di database.py")


try:
    from server.control.frame_queue import frame_queue

    if config.VERBOSE:
        print("✅ Frame queue caricata da frame_queue.py")
except ImportError:
    print("❌ Errore caricamento di frame_queue.py")


# ============================================================================
# INIZIALIZZAZIONE
# ============================================================================

recognizer = None
visualization_manager = None
db_manager = None
stop_threads = threading.Event()


def initialize_ocr():
    global recognizer

    # Inizializza OCR
    if config.VERBOSE:
        print("🔧 Inizializzazione OCR...")

    try:
        import pytesseract

        config.TESSERACT_AVAILABLE = True
        if config.VERBOSE:
            print("✅ Tesseract disponibile")
    except ImportError:
        config.TESSERACT_AVAILABLE = False
        if config.VERBOSE:
            print("❌ Tesseract non disponibile")

    try:
        recognizer = LicensePlateRecognizer("cct-xs-v1-global-model")
        config.FAST_OCR_AVAILABLE = True
        if config.VERBOSE:
            print("✅ LPR disponibile")
            set_context("recognizer", recognizer)
    except Exception as e:
        config.FAST_OCR_AVAILABLE = False
        if config.VERBOSE:
            print(f"❌ Errore nell'inizializzazione di LPR: {e}")


def initialize_visualization():
    global visualization_manager
    visualization_manager = Visualization()
    return visualization_manager


def initialize_database():
    global db_manager

    try:
        db_manager = DatabaseManager(config.DATABASE_PATH)
        if config.VERBOSE:
            print("✅ DatabaseManager inizializzato correttamente")

        set_context("db_manager", db_manager)

    except Exception as e:
        print(f"❌ Errore nell'inizializzazione del DatabaseManager: {e}")

    config.ALL_AUTHORIZED_PLATES = config.load_authorized_plates()
    config.validate_config()


def load_models():
    if config.VERBOSE:
        print("   Loading YOLO veicoli...")

    coco_model = YOLO(config.COCO_MODEL_PATH)
    coco_model.to(config.DEVICE)

    if config.VERBOSE:
        print("   Loading YOLO targhe...")

    plate_model = YOLO(config.PLATE_MODEL_PATH)
    plate_model.to(config.DEVICE)

    set_context("coco_model", coco_model)
    set_context("plate_model", plate_model)


def initialize_tracker():
    if config.VERBOSE:
        print("   Inizializzazione SORT tracker...")

    tracker = Sort(
        max_age=config.TRACKER_MAX_AGE,
        min_hits=config.TRACKER_MIN_HITS,
        iou_threshold=config.TRACKER_IOU_THRESHOLD,
    )

    set_context("tracker", tracker)


def open_video_source():
    if config.USE_WEBCAM:
        camera = cv2.VideoCapture(0)  # 0 = main camera
        if not camera.isOpened():
            if config.VERBOSE:
                print("❌ Impossibile aprire la webcam")

            stop_threads.set()
            return None
    else:
        camera = cv2.VideoCapture(config.VIDEO_PATH)
        if not camera.isOpened():
            if config.VERBOSE:
                print(f"❌ Impossibile aprire il video: {config.VIDEO_PATH}")

            stop_threads.set()
            return None
    fps = camera.get(cv2.CAP_PROP_FPS)
    if config.VERBOSE:
        print(f"\n📹 Video: {config.VIDEO_PATH} ({fps:.1f} fps)")

    set_context("camera", camera)
    return camera


def initialize_csv():
    with open(config.OUTPUT_CSV, "w") as f:
        f.write("plate_text,timestamp,status,event\n")


def print_progress(frame_count: int, start_time: float):
    if not config.VERBOSE:
        return

    if frame_count % 100 == 0:
        elapsed_time = time.time() - start_time
        print(f"📊 Frame {frame_count} | FPS: {frame_count/elapsed_time:.1f}")


def print_final_states(frame_count: int, start_time: float, checked_vehicles: dict):
    if not config.VERBOSE:
        return

    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ COMPLETATO!")
    print(f"{'='*60}")
    print(f"Tempo: {elapsed_time:.1f}s | FPS: {frame_count/elapsed_time:.1f}")
    print(f"Veicoli controllati: {len(checked_vehicles)}")


# ============================================================================
# THREAD PROCESING PRINCIPALE
# ============================================================================


def processing_thread():
    if config.VERBOSE:
        print("🚀 Inizializzazione sistema...")
        print(f"   Device: {config.DEVICE}")
        print(f"   Frame source: {config.FRAME_SOURCE}")

    load_models()
    initialize_tracker()

    camera = None
    if config.FRAME_SOURCE == "local":
        camera = open_video_source()

        if camera is None:
            return
    else:
        if config.VERBOSE:
            print("   📡 Modalità REMOTE: in attesa di frame HTTP...")

    initialize_csv()

    # stato
    checked_vehicles = {}
    frame_count = 0

    if config.VERBOSE:
        print("\n🎬 Inizio elaborazione...\n")

    start_time = time.time()

    try:
        while not stop_threads.is_set():
            # Acquisizione frame
            # tramite camera/video locale
            if config.FRAME_SOURCE == "local":
                ret, frame = camera.read()
                if not ret:
                    if config.VERBOSE:
                        print("⚠️  Fine del video o impossibile leggere il frame")
                    break

            # tramite frame queue (http upload)
            else:
                if frame_queue.empty():
                    time.sleep(0.1)
                    if config.VERBOSE:
                        print("⏳ In attesa di nuovi frame...")
                    continue

                data = frame_queue.get()

                frame = data[0]
                metadata = data[1]

                if frame is None:
                    if config.VERBOSE:
                        print("⚠️  Frame None, non valido")
                    continue

            frame_count += 1

            print_progress(frame_count, start_time)

            # detections = detect_vehicles(frame)
            if config.FRAME_SOURCE == "local":
                detections = detect_vehicles(frame)
            else:
                metadata = metadata or {}

                detections = metadata.get("detections", [])

            detections = update_tracking(detections)

            process_detections(detections, frame, frame_count, checked_vehicles)

            visualization_manager.add_frame_to_magazine(frame, detections)

    except KeyboardInterrupt:
        if config.VERBOSE:
            print("\n⚠️  Interruzione utente")

    finally:
        if camera:
            camera.release()
        if config.SHOW_VIDEO:
            cv2.destroyAllWindows()
        stop_threads.set()
        print_final_states(frame_count, start_time, checked_vehicles)


def print_database_stats():
    if config.VERBOSE and db_manager:
        stats = db_manager.get_statistics()
        print("📊 Statistiche Database:")
        print(f"   Targhe totali: {stats.get('total_plates', 0)}")
        print(f"   Targhe valide: {stats.get('valid_plates', 0)}")
        print(f"   Targhe scadute: {stats.get('expired_plates', 0)}")


def main():

    initialize_ocr()
    initialize_visualization()
    initialize_database()

    print_database_stats()

    thread_process = threading.Thread(target=processing_thread)
    thread_visualize = threading.Thread(
        target=visualization_manager.handle_visualization
    )
    thread_process.start()
    thread_visualize.start()

    try:
        thread_process.join()
        thread_visualize.join()
    except KeyboardInterrupt:
        stop_threads.set()
        thread_process.join(timeout=2)
        thread_visualize.join(timeout=2)


if __name__ == "__main__":
    main()
