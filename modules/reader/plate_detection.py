from ultralytics import YOLO
import modules.reader.config as config  # fix import

def detect_plates_in_vehicle(vehicle_crop, plate_model: YOLO) -> list:
    results = plate_model(
        vehicle_crop,
        conf=config.PLATE_DETECTION_CONFIDENCE,
        verbose=False,
    )[0]

    plates = []
    for box in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = box
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        if not is_valid_plate_detection(x1, y1, x2, y2):
            continue

        plate_crop = vehicle_crop[y1:y2, x1:x2]
        if plate_crop.size > 0:
            plates.append({"image": plate_crop, "coords": (x1, y1, x2, y2), "score": score})

    return plates


def is_valid_plate_detection(x1, y1, x2, y2) -> bool:
    width = x2 - x1
    height = y2 - y1
    if width < 30 or height < 10:
        return False
    aspect_ratio = width / float(height)
    return 1.5 <= aspect_ratio <= 7.0