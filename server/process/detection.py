"""
detection.py

Modulo per la rilevazione di veicoli e targhe

funzione offerte:
- classify_vehicle
- detect_vehicles
- update_tracking
- detect_plates_in_vehicle
- is_valid_plate_detection
- extract_vehicle_crop

"""

from ultralytics import YOLO
from sort.sort import Sort
import numpy as np
import cv2
import server.config as config
from server.control.context import get_context


def classify_vehicle(class_id: int) -> str:
    if class_id in config.VEHICLES_4_WHEELS:
        return "to_check"

    if class_id in config.VEHICLES_2_WHEELS:
        return "authorized"

    if class_id == 0:
        return "pedestrian"

    return None  # non dovrebbe succedere, controlli già fatti in precedenza


def detect_vehicles(frame: np.ndarray) -> list:

    coco_model: YOLO = get_context("coco_model")

    # detection dei veicoli
    results = coco_model(frame, verbose=False)[0]

    detections = []

    for r in results.boxes.data.tolist():

        # estrazione dati della detection
        x1, y1, x2, y2, score, class_id = r
        class_id = int(class_id)

        if (
            score < config.DETECTION_CONFIDENCE
            or class_id not in config.CLASSES_TO_DETECT
        ):
            continue
        # classificazione veicolo
        label = classify_vehicle(class_id)

        # se non è un veicolo continua
        if label is None:
            continue

        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # aggiunta alla lista delle detection
        detections.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "score": score,
                "class_id": class_id,
                "label": label,
            }
        )

    return detections


def update_tracking(detections: list) -> list:

    tracker: Sort = get_context("tracker")
    if not detections:
        return detections

    coords = [
        [
            float(d["x1"]),
            float(d["y1"]),
            float(d["x2"]),
            float(d["y2"]),
            float(d["score"]),
        ]
        for d in detections
    ]
    # aggiorna il tracker
    track_ids = tracker.update(np.array(coords))

    if len(track_ids) == len(detections):
        for i, det in enumerate(detections):
            det["track_id"] = int(track_ids[i][4])

    return detections


def detect_plates_in_vehicle(vehicle_crop: np.ndarray) -> list:

    plate_model: YOLO = get_context("plate_model")

    # detection delle targhe
    results = plate_model(
        vehicle_crop,
        conf=config.PLATE_DETECTION_CONFIDENCE,  # confidenza minima
        verbose=False,
    )[0]

    plates = []

    for box in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = box
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Verifica dimensioni minime e aspect ratio
        if not is_valid_plate_detection(x1, y1, x2, y2):
            continue

        # Crop targa
        plate_crop = vehicle_crop[y1:y2, x1:x2]

        # debug
        # cv2.imshow("Plate Crop", plate_crop)
        # cv2.waitKey(1)

        if plate_crop.size > 0:
            plates.append(
                {"image": plate_crop, "coords": (x1, y1, x2, y2), "score": score}
            )

    return plates


def is_valid_plate_detection(x1: int, y1: int, x2: int, y2: int) -> bool:
    width = x2 - x1
    height = y2 - y1

    # Verifica dimensioni minime
    if width < 30 or height < 10:
        return False

    # Aspect ratio check
    aspect_ratio = width / float(height)
    if aspect_ratio < 1.5 or aspect_ratio > 7.0:
        return False

    return True


def extract_vehicle_crop(vehicle_box: tuple, frame: np.ndarray) -> np.ndarray:

    x1, y1, x2, y2 = vehicle_box

    # Aggiungi margine
    margin = config.VEHICLE_CROP_MARGIN

    x1_crop = max(0, x1 - margin)
    y1_crop = max(0, y1 - margin)
    x2_crop = min(frame.shape[1], x2 + margin)
    y2_crop = min(frame.shape[0], y2 + margin)

    return frame[y1_crop:y2_crop, x1_crop:x2_crop]
