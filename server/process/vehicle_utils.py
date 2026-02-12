"""
vehicle_utils.py

Modulo per la gestione dei veicoli

funzione offerte:
- get_car
- process_vehicle_simple
- process_detections

"""

try:
    import numpy as np
    from ultralytics import YOLO
    import server.config as config
    from server.process.detection import extract_vehicle_crop, detect_plates_in_vehicle
    from server.process.ocr_utils import find_best_plate_reading, save_vehicle_image
    from server.process.plate_utils import (
        check_authorization,
        log_access_to_db,
        log_plate_result,
        log_to_csv,
    )
    from server.control.context import context

except ImportError as e:
    print(f"Errore nel caricamento dei moduli in vehicle_utils.py: {e}")


def get_car(plate_coordinates: tuple, vehicle_ids: np.ndarray) -> tuple:

    x1, y1, x2, y2 = plate_coordinates

    # Calcola centro della targa
    plate_center_x = (x1 + x2) / 2
    plate_center_y = (y1 + y2) / 2

    # Cerca il veicolo che contiene il centro della targa
    for vehicle in vehicle_ids:
        xcar1, ycar1, xcar2, ycar2, vehicle_id = vehicle

        # Controlla se il centro della targa è dentro il bounding box del veicolo
        if xcar1 <= plate_center_x <= xcar2 and ycar1 <= plate_center_y <= ycar2:
            return xcar1, ycar1, xcar2, ycar2, vehicle_id

    # Nessun veicolo trovato
    return -1, -1, -1, -1, -1


def process_vehicle_simple(
    vehicle_box: tuple, frame: np.ndarray, track_id: int, frame_count: int
) -> tuple:

    # Estrai crop del veicolo
    vehicle_crop = extract_vehicle_crop(vehicle_box, frame)

    # Salva immagine del veicolo
    if config.SAVE_VEHICLE_IMAGES:
        save_vehicle_image(vehicle_crop, track_id, frame_count)

    if vehicle_crop.size == 0:
        return None, None, None, None

    if config.VERBOSE:
        print(f"\n{'='*60}")
        print(f"🚗 Processing Vehicle {track_id} | Frame {frame_count}")
        print(f"   Vehicle size: {vehicle_crop.shape[1]}x{vehicle_crop.shape[0]}")

    # Rileva targa nel frame del veicolo
    plates = detect_plates_in_vehicle(vehicle_crop)

    if not plates:
        if config.VERBOSE:
            print(f"   ✗ No plates detected")
        return None, None, None, None

    if config.VERBOSE:
        print(f"   ✓ {len(plates)} plates detected")

    # Trova la targa con la migliore confidenza
    best_result, best_confidence = find_best_plate_reading(
        plates, track_id, frame_count
    )

    # COntrollo valore minimo di confidenza
    if not best_result or best_confidence < config.OCR_MIN_CONFIDENCE:
        if config.VERBOSE:
            print(f"   ✗ No valid plate found (confidence: {best_confidence:.2f})")
        return None, None, None, None

    # Controlla autorizzazione
    status, plate_info = check_authorization(best_result)

    # Log
    log_plate_result(best_result, status, best_confidence, plate_info)
    log_to_csv(best_result, status, )
    log_access_to_db(best_result, status, )

    return best_result, best_confidence, plate_info, status


def process_detections(
    detections: list, frame: np.ndarray, frame_count: int, checked_vehicles: dict
):

    for det in detections:
        if "track_id" not in det:
            continue

        track_id = det["track_id"]

        # veicolo già controllato, usa risultato salvato
        if track_id in checked_vehicles:
            status, plate_text, plate_info = checked_vehicles[track_id]
            det["label"] = status
            det["plate_text"] = plate_text
            det["plate_info"] = plate_info
            continue

        # solo veicoli da controllare (4 ruote)
        if det["label"] != "to_check":
            continue

        # estrai coordinate veicolo
        vehicle_box = (int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"]))

        # processa veicolo
        plate_text, score, plate_info, status = process_vehicle_simple(
            vehicle_box, frame, track_id, frame_count
        )

        if not plate_text:
            continue

        # aggiorna detection se trovata targa valida
        if plate_text:
            det["label"] = status
            det["plate_text"] = plate_text
            det["plate_info"] = plate_info
            # salva risultato per riuso futuro
            checked_vehicles[track_id] = (status, plate_text, plate_info)

            return plate_text
