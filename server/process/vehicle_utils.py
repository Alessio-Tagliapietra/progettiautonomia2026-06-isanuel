"""
vehicle_utils.py

Modulo per la gestione dei veicoli

funzione offerte:
- get_car
- process_vehicle_simple
- process_detections
- process_entry
- process_exit

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
    from server.process.distance_utils import is_vehicle_close_enough
    from server.process.access_tracker import access_tracker
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
    
    
    print("==============entrato in process_vehicle_simple==========")

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

    # Controllo valore minimo di confidenza
    if not best_result or best_confidence < config.OCR_MIN_CONFIDENCE:
        if config.VERBOSE:
            print(f"   ✗ No valid plate found (confidence: {best_confidence:.2f})")
        return None, None, None, None

    return best_result, best_confidence, None, None


def process_entry(
    plate_text: str, 
    best_confidence: float, 
    gate_id: str
) -> tuple:
    """
    Processa un'entrata: verifica autorizzazione e registra il tentativo.
    
    Args:
        plate_text: targa letta
        best_confidence: confidenza OCR
        gate_id: ID del gate
    
    Returns:
        tuple: (plate_text, best_confidence, plate_info, status)
    """
    if config.VERBOSE:
        print(f"\n   🚪 PROCESSANDO ENTRATA @ {gate_id}")
    
    # Verifica se può essere processata (controllo temporale)
    if not access_tracker.can_process_entry(plate_text, gate_id):
        if config.VERBOSE:
            print(f"   ⏱️  Entrata scartata: rilevazione troppo recente")
        return None, None, None, None
    
    # Controlla autorizzazione
    status, plate_info = check_authorization(plate_text)
    
    # Log
    log_plate_result(plate_text, status, best_confidence, plate_info, event="entrata")
    log_to_csv(plate_text, status, event="entrata")
    log_access_to_db(plate_text, status, event="entrata")
    
    # Registra l'entrata nel tracker
    access_tracker.register_entry(plate_text, gate_id)
    
    return plate_text, best_confidence, plate_info, status


def process_exit(
    plate_text: str, 
    best_confidence: float, 
    gate_id: str
) -> tuple:
    """
    Processa un'uscita: verifica che sia passato abbastanza tempo dall'ultima
    rilevazione e registra l'uscita.
    
    Args:
        plate_text: targa letta
        best_confidence: confidenza OCR
        gate_id: ID del gate
    
    Returns:
        tuple: (plate_text, best_confidence, plate_info, status)
    """
    if config.VERBOSE:
        print(f"\n   🚪 PROCESSANDO USCITA @ {gate_id}")
    
    # Verifica se può essere processata (controllo temporale)
    if not access_tracker.can_process_exit(plate_text, gate_id):
        if config.VERBOSE:
            print(f"   ⏱️  Uscita scartata: rilevazione troppo recente o nessuna entrata")
        return None, None, None, None
    
    # Per le uscite, registriamo sempre (non controlliamo autorizzazione)
    # ma potremmo volere comunque le info della targa
    status, plate_info = check_authorization(plate_text)
    
    # Forza status a "exit" per differenziare nei log
    status = "exit"
    
    # Log
    log_plate_result(plate_text, status, best_confidence, plate_info, event="uscita")
    log_to_csv(plate_text, status, event="uscita")
    log_access_to_db(plate_text, status, event="uscita")
    
    # Registra l'uscita nel tracker
    access_tracker.register_exit(plate_text, gate_id)
    
    return plate_text, best_confidence, plate_info, status


def process_detections(
    detections: list, 
    frame: np.ndarray, 
    frame_count: int, 
    checked_vehicles: dict,
    gate_type: str = "entrata",
    gate_id: str = "unknown"
):
    """
    Processa le detection applicando la logica di entrata/uscita.
    
    Args:
        detections: lista detection
        frame: frame corrente
        frame_count: numero frame
        checked_vehicles: dizionario veicoli già controllati
        gate_type: "entrata" o "uscita"
        gate_id: ID del gate
    """

    for det in detections:        
        if "track_id" not in det:
            continue

        track_id = det["track_id"]

        # veicolo già controllato, usa risultato salvato
        if track_id in checked_vehicles:
            print(f"   ✅ Veicolo {track_id} già controllato")
            status, plate_text, plate_info = checked_vehicles[track_id]
            det["label"] = status
            det["plate_text"] = plate_text
            det["plate_info"] = plate_info
            continue

        # solo veicoli da controllare (4 ruote)
        if det["label"] != "to_check":
            continue

        # ===== CONTROLLO DISTANZA =====
        vehicle_box = (int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"]))
        
        if not is_vehicle_close_enough(vehicle_box, frame.shape):
            if config.VERBOSE:
                print(f"   ⚠️  Veicolo {track_id} troppo lontano, ignorato")
            continue

        # ===== PROCESSING TARGA =====
        plate_text, score, _, _ = process_vehicle_simple(
            vehicle_box, frame, track_id, frame_count
        )

        if not plate_text:
            continue

        # ===== LOGICA ENTRATA/USCITA =====
        if gate_type == "entrata":
            plate_text, score, plate_info, status = process_entry(
                plate_text, score, gate_id
            )
        else:  # uscita
            plate_text, score, plate_info, status = process_exit(
                plate_text, score, gate_id
            )

        # Se il processing ha restituito None, la rilevazione è stata scartata
        if not plate_text:
            continue

        # aggiorna detection se trovata targa valida
        det["label"] = status
        det["plate_text"] = plate_text
        det["plate_info"] = plate_info
        
        # salva risultato per riuso futuro
        checked_vehicles[track_id] = (status, plate_text, plate_info)

        return plate_text