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
import modules.reader.config as config


def classify_vehicle(class_id: int) -> str:
    if class_id in config.VEHICLES_4_WHEELS:
        return "to_check"

    if class_id in config.VEHICLES_2_WHEELS:
        return "authorized"

    if class_id == 0:
        return "pedestrian"

    return None  # non dovrebbe succedere, controlli già fatti in precedenza


def detect_vehicles(frame: np.ndarray, coco_model : YOLO) -> list:


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


def update_tracking(detections: list, tracker : Sort) -> list:

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





def extract_vehicle_crop(vehicle_box: tuple, frame: np.ndarray) -> np.ndarray:

    x1, y1, x2, y2 = vehicle_box

    # Aggiungi margine
    margin = config.VEHICLE_CROP_MARGIN

    x1_crop = max(0, x1 - margin)
    y1_crop = max(0, y1 - margin)
    x2_crop = min(frame.shape[1], x2 + margin)
    y2_crop = min(frame.shape[0], y2 + margin)

    return frame[y1_crop:y2_crop, x1_crop:x2_crop]
