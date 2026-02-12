"""
access_tracker.py

Modulo per il tracking temporale degli accessi in entrata/uscita.
Gestisce il controllo del tempo minimo tra rilevazioni successive.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import server.config as config


class AccessTracker:
    """
    Gestisce il tracking temporale degli accessi dei veicoli.
    Memorizza l'ultima rilevazione per ogni targa per evitare duplicati.
    """
    
    def __init__(self):
        # Dizionario: plate_number -> {
        #   'last_entry': datetime,
        #   'last_exit': datetime,
        #   'gate_id': str
        # }
        self.access_history: Dict[str, Dict] = {}
    
    def can_process_entry(self, plate_number: str, gate_id: str) -> bool:
        """
        Verifica se un'entrata può essere processata.
        
        Args:
            plate_number: targa del veicolo
            gate_id: ID del gate
        
        Returns:
            bool: True se l'entrata può essere registrata
        """
        plate_number = plate_number.upper().strip()
        
        if plate_number not in self.access_history:
            # Prima rilevazione, sempre valida
            return True
        
        history = self.access_history[plate_number]
        last_entry = history.get('last_entry')
        
        if last_entry is None:
            return True
        
        # Calcola tempo trascorso dall'ultima entrata
        time_since_last = datetime.now() - last_entry
        min_interval = timedelta(seconds=config.MIN_ENTRY_INTERVAL_SECONDS)
        
        if time_since_last < min_interval:
            if config.VERBOSE:
                remaining = (min_interval - time_since_last).total_seconds()
                print(f"     ⏱️  Entrata troppo recente, attendi {remaining:.0f}s")
            return False
        
        return True
    
    def can_process_exit(self, plate_number: str, gate_id: str) -> bool:
        """
        Verifica se un'uscita può essere processata.
        L'uscita è valida solo se è passato almeno MIN_EXIT_INTERVAL_SECONDS
        dall'ultima rilevazione (entrata o uscita).
        
        Args:
            plate_number: targa del veicolo
            gate_id: ID del gate
        
        Returns:
            bool: True se l'uscita può essere registrata
        """
        plate_number = plate_number.upper().strip()
        
        if plate_number not in self.access_history:
            # Nessuna entrata registrata, uscita non valida
            if config.VERBOSE:
                print(f"     ⚠️  Nessuna entrata registrata per {plate_number}")
            return False
        
        history = self.access_history[plate_number]
        last_entry = history.get('last_entry')
        last_exit = history.get('last_exit')
        
        # Determina l'ultima rilevazione (entry o exit)
        last_detection = last_entry
        if last_exit and (not last_entry or last_exit > last_entry):
            last_detection = last_exit
        
        if last_detection is None:
            return False
        
        # Calcola tempo trascorso dall'ultima rilevazione
        time_since_last = datetime.now() - last_detection
        min_interval = timedelta(seconds=config.MIN_EXIT_INTERVAL_SECONDS)
        
        if time_since_last < min_interval:
            if config.VERBOSE:
                remaining = (min_interval - time_since_last).total_seconds()
                print(f"     ⏱️  Uscita troppo recente, attendi {remaining:.0f}s")
            return False
        
        return True
    
    def register_entry(self, plate_number: str, gate_id: str):
        """
        Registra un'entrata.
        
        Args:
            plate_number: targa del veicolo
            gate_id: ID del gate
        """
        plate_number = plate_number.upper().strip()
        
        if plate_number not in self.access_history:
            self.access_history[plate_number] = {}
        
        self.access_history[plate_number]['last_entry'] = datetime.now()
        self.access_history[plate_number]['gate_id'] = gate_id
        
        if config.VERBOSE:
            print(f"     ✅ Entrata registrata: {plate_number} @ {gate_id}")
    
    def register_exit(self, plate_number: str, gate_id: str):
        """
        Registra un'uscita.
        
        Args:
            plate_number: targa del veicolo
            gate_id: ID del gate
        """
        plate_number = plate_number.upper().strip()
        
        if plate_number not in self.access_history:
            self.access_history[plate_number] = {}
        
        self.access_history[plate_number]['last_exit'] = datetime.now()
        self.access_history[plate_number]['gate_id'] = gate_id
        
        if config.VERBOSE:
            print(f"     ✅ Uscita registrata: {plate_number} @ {gate_id}")
    
    def get_last_access(self, plate_number: str) -> Optional[Dict]:
        """
        Ottiene l'ultima rilevazione per una targa.
        
        Args:
            plate_number: targa del veicolo
        
        Returns:
            Dict con info sull'ultimo accesso o None
        """
        plate_number = plate_number.upper().strip()
        return self.access_history.get(plate_number)
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """
        Rimuove le entry più vecchie di max_age_hours.
        
        Args:
            max_age_hours: età massima in ore
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        plates_to_remove = []
        for plate, history in self.access_history.items():
            last_entry = history.get('last_entry')
            last_exit = history.get('last_exit')
            
            # Trova l'ultima rilevazione
            last_time = last_entry
            if last_exit and (not last_entry or last_exit > last_entry):
                last_time = last_exit
            
            if last_time and last_time < cutoff_time:
                plates_to_remove.append(plate)
        
        for plate in plates_to_remove:
            del self.access_history[plate]
        
        if config.VERBOSE and plates_to_remove:
            print(f"🧹 Cleanup: rimossi {len(plates_to_remove)} record obsoleti")


# Istanza globale del tracker
access_tracker = AccessTracker()