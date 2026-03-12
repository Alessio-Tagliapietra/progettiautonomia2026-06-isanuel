"""
distance_utils.py

Modulo per il calcolo della distanza del veicolo dalla camera.
Utilizzato per filtrare veicoli troppo lontani.
"""

import numpy as np
import modules.reader.config as config


def calculate_vehicle_distance(bbox: tuple, frame_shape: tuple) -> float:
    """
    Stima la distanza del veicolo in base alle dimensioni del bounding box.
    Più grande è il bbox, più vicino è il veicolo.
    
    Args:
        bbox: tuple (x1, y1, x2, y2) del bounding box
        frame_shape: tuple (height, width, channels) del frame
    
    Returns:
        float: distanza normalizzata (0-1), dove 0 = molto vicino, 1 = molto lontano
    """
    x1, y1, x2, y2 = bbox
    frame_height, frame_width = frame_shape[:2]
    
    # Calcola area del bbox
    bbox_width = x2 - x1
    bbox_height = y2 - y1
    bbox_area = bbox_width * bbox_height
    
    # Area totale del frame
    frame_area = frame_height * frame_width
    
    # Percentuale di occupazione del frame
    occupation_ratio = bbox_area / frame_area
    
    # Converti in distanza (inversamente proporzionale)
    # Più grande il bbox, più piccola la distanza
    distance = 1.0 - min(occupation_ratio * 10, 1.0)  # normalizzato 0-1
    
    return distance


def is_vehicle_close_enough(bbox: tuple, frame_shape: tuple, 
                            threshold: float = None) -> bool:
    """
    Verifica se il veicolo è abbastanza vicino per essere processato.
    
    Args:
        bbox: tuple (x1, y1, x2, y2) del bounding box
        frame_shape: tuple (height, width, channels) del frame
        threshold: soglia di distanza (0-1). Se None, usa config.DISTANCE_THRESHOLD
    
    Returns:
        bool: True se il veicolo è abbastanza vicino
    """
    if threshold is None:
        threshold = config.DISTANCE_THRESHOLD
    
    distance = calculate_vehicle_distance(bbox, frame_shape)
    
    if config.VERBOSE:
        bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        print(f"     Distanza veicolo: {distance:.3f} (area bbox: {bbox_area:.0f}px²)")
    
    return distance <= threshold


def get_bbox_center(bbox: tuple) -> tuple:
    """
    Calcola il centro del bounding box.
    
    Args:
        bbox: tuple (x1, y1, x2, y2)
    
    Returns:
        tuple: (center_x, center_y)
    """
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y


def get_bbox_area(bbox: tuple) -> float:
    """
    Calcola l'area del bounding box.
    
    Args:
        bbox: tuple (x1, y1, x2, y2)
    
    Returns:
        float: area in pixel²
    """
    x1, y1, x2, y2 = bbox
    return (x2 - x1) * (y2 - y1)