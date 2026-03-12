import numpy as np
from ultralytics import YOLO
import modules.reader.config as config
from modules.reader.detection import extract_vehicle_crop
from modules.reader.plate_detection import detect_plates_in_vehicle
from modules.reader.ocr_utils import find_best_plate_reading, save_vehicle_image
from modules.reader.distance_utils import is_vehicle_close_enough


def process_vehicle_simple(vehicle_box, frame, track_id, frame_count, models) -> tuple:
    vehicle_crop = extract_vehicle_crop(vehicle_box, frame)

    if config.SAVE_VEHICLE_IMAGES:
        save_vehicle_image(vehicle_crop, track_id, frame_count)

    if vehicle_crop.size == 0:
        return None, None

    if config.VERBOSE:
        print(f"\n{'='*60}")
        print(f"🚗 Vehicle {track_id} | Frame {frame_count} | {vehicle_crop.shape[1]}x{vehicle_crop.shape[0]}")

    plates = detect_plates_in_vehicle(vehicle_crop, models.plate_model)  # fix

    if not plates:
        if config.VERBOSE: print("   ✗ No plates detected")
        return None, None

    best_result, best_confidence = find_best_plate_reading(plates, track_id, frame_count, models.recognizer)  # fix

    if not best_result or best_confidence < config.OCR_MIN_CONFIDENCE:
        if config.VERBOSE: print(f"   ✗ Confidence troppo bassa ({best_confidence:.2f})")
        return None, None

    return best_result, best_confidence


def process_detections(detections, frame, frame_count, checked_vehicles, gate_id, mqtt_publisher, models):
    for det in detections:
        if "track_id" not in det:
            continue

        track_id = det["track_id"]

        if track_id in checked_vehicles:
            continue

        # ── Veicoli a 2 ruote: autorizzati direttamente ──
        if det["label"] == "authorized":
            mqtt_publisher.publish_plate(
                plate_text=f"2W_{track_id}",
                confidence=1.0,
                gate_id=gate_id,
                vehicle_type="2wheels"
            )
            checked_vehicles[track_id] = f"2W_{track_id}"
            continue

        # ── Veicoli a 4 ruote: lettura targa ──
        if det["label"] != "to_check":
            continue

        vehicle_box = (det["x1"], det["y1"], det["x2"], det["y2"])

        if not is_vehicle_close_enough(vehicle_box, frame.shape):
            if config.VERBOSE: print(f"   ⚠️  Veicolo {track_id} troppo lontano")
            continue

        plate_text, score = process_vehicle_simple(vehicle_box, frame, track_id, frame_count, models)

        if not plate_text:
            continue

        mqtt_publisher.publish_plate(plate_text, score, gate_id)
        checked_vehicles[track_id] = plate_text
    for det in detections:
        if "track_id" not in det or det["label"] != "to_check":
            continue

        track_id = det["track_id"]

        if track_id in checked_vehicles:
            continue

        vehicle_box = (det["x1"], det["y1"], det["x2"], det["y2"])

        if not is_vehicle_close_enough(vehicle_box, frame.shape):
            if config.VERBOSE: print(f"   ⚠️  Veicolo {track_id} troppo lontano")
            continue

        plate_text, score = process_vehicle_simple(vehicle_box, frame, track_id, frame_count, models)  # fix

        if not plate_text:
            continue

        mqtt_publisher.publish_plate(plate_text, score, gate_id)
        checked_vehicles[track_id] = plate_text
        if config.VERBOSE: print(f"   📡 Pubblicato: {plate_text} ({score:.2f})")