import os

DETECTION_CONFIDENCE = 0.2
CLASSES_TO_DETECT = [0, 1, 2, 3, 5, 7]  
# 0: person
# 1: bicycle  
# 2: car
# 3: motorcycle
# 5: bus
# 7: truck

# ID classi COCO: https://github.com/ultralytics/yolov5/blob/master/data/coco.yaml
CLASSES_TO_DETECT = [0, 1, 2, 3, 5, 7]  
# 0: person
# 1: bicycle  
# 2: car
# 3: motorcycle
# 5: bus
# 7: truck

# Veicoli a 4 ruote (richiedono controllo targa)
VEHICLES_4_WHEELS = [2, 5, 7]  # car, bus, truck

# Veicoli a 2 ruote (sempre autorizzati - no controllo targa)
VEHICLES_2_WHEELS = [1, 3]  # bicycle, motorcycle

VERBOSE = True


APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
COCO_MODEL_PATH = os.path.join(
    MODELS_DIR, "yolo", "yolov8n.pt"
) 

