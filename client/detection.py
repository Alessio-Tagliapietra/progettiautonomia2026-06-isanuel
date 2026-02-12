import config 
import numpy as np
from ultralytics import YOLO


coco_model : YOLO = None

def initialize_coco_model() -> YOLO:
    global coco_model
    
    if config.VERBOSE:
        print("🔧 Inizializzazione modello COCO...")
        
    coco_model = YOLO(config.COCO_MODEL_PATH)
    coco_model.to("cpu")
    
    if config.VERBOSE:
        print("✅ Modello COCO caricato correttamente")
        

def classify_vehicle(class_id : int) -> str:
    if class_id in config.VEHICLES_4_WHEELS:
        return  "to_check"
    
    if class_id in config.VEHICLES_2_WHEELS:
        return  "authorized"
    
    return None #non dovrebbe succedere, controlli già fatti in precedenza

def detect_vehicles(frame: np.ndarray) -> list:
    global coco_model
    
    # detection dei veicoli 
    results = coco_model(frame, verbose=False)[0]
    
    detections = []
    
    for r in results.boxes.data.tolist():
        
        #estrazione dati della detection
        x1, y1, x2, y2, score, class_id = r
        class_id = int(class_id)
        
        if (score < config.DETECTION_CONFIDENCE
            or class_id not in config.CLASSES_TO_DETECT):
            continue
        #classificazione veicolo
        label = classify_vehicle(class_id)
        
        #se non è un veicolo continua
        if label is None:
            continue
        
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        #aggiunta alla lista delle detection
        detections.append({
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            "score": score,
            "class_id": class_id,
            "label": label
        })
        
    return detections