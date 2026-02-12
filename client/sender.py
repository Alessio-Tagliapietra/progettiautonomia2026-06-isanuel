import cv2
import requests
import time
import json
import sseclient

from detection import initialize_coco_model, detect_vehicles
import config

SERVER_URL = "http://localhost:5000/api/upload"
# URL per ottenere lo stato del servizio
SERVICE_STATE_URL = "http://localhost:5000/api/service/state"

# Configurazione headers
# Camera ID e API Key per l'autenticazione con il server
headers = {
    "camera-id": "camera_client01",
    "API-Key": "g9f3e1d7c4b84eab9f5c1d2e3a4b57kd"
}

client_data = {
    "type": "entrata",
    "gate_id":"my_gate_id" #modificare sulla base dell'id del cancello
}

service_enabled = True


#funzionalità da integrare:
# possibilità di avviare o fermare il servizio da server
# modifica la variabile globale service_enabled
# il client continua comunque ad ascolare eventuali messaggi
# del server per riavvio del servizio
#intanto è impostato sempre su True: il servizio è sempre attivo
def listen_service_state():
    """Thread SSE per aggiornare service_enabled"""
    global service_enabled
    while True:
        try:
            response = requests.get(SERVICE_STATE_URL, stream=True)
            client = sseclient.SSEClient(response)
            for event in client.events():
                service_enabled = event.data == "True"
                print(f"📡 Stato servizio aggiornato: {service_enabled}")
        except Exception as e:
            print(f"❌ Errore SSE: {e}")
            time.sleep(1)
            
def listen_service_state():
    """Thread SSE per aggiornare service_enabled"""
    global service_enabled
    while True:
        try:
            response = requests.get(SERVICE_STATE_URL, stream=True)
            client = sseclient.SSEClient(response)
            for event in client.events():
                service_enabled = event.data == "True"
                print(f"📡 Stato servizio aggiornato: {service_enabled}")
        except Exception as e:
            print(f"❌ Errore SSE: {e}")
            time.sleep(1)


def send_single_frame(frame):
    
    if not service_enabled:
        return False 
    
    if frame is None:
        if config.VERBOSE:
            print("❌ Frame non valido")
        return False
        
    detections = detect_vehicles(frame) or []
    if not detections or len(detections) == 0:
        if config.VERBOSE:
            print("   Nessun veicolo rilevato in questo frame.")
        return True # nessun errore, solo nessun veicolo
                    
            
        # Codifica e invia
    _, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
    files = {
        "image": ("frame.jpg", jpg.tobytes(), "image/jpeg")
    }
        
    data = {
        "metadata": json.dumps({
        "detections": detections,
        "type": client_data["type"],
        "gate": client_data["gate_id"],
        })
    }
            
    try:
        response = requests.post(
            SERVER_URL,
            files=files,
            data=data,
            timeout=0.1,
            headers=headers,
        )
        
        if response.ok:
            if config.VERBOSE:
                print(f"✅ Frame inviato con successo: {response.json()}")
            return True
        else:
            if config.VERBOSE:
                print(f"❌ Errore server: {response.status_code} - {response.text}")
            return False
        
    except requests.exceptions.RequestException as e:
        if config.VERBOSE:
            print(f"❌ Errore invio richiesta: {e}")
        return False



def send_video_stream(source=0, fps=10):
    """Invia frame continui da webcam o video"""
    try:
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            if config.VERBOSE:
                print(f"❌ Impossibile aprire la sorgente video: {source}")
            return
        
        print(f"📹 Streaming da: {source if isinstance(source, str) else 'Webcam'}")
        print(f"   Target FPS: {fps}")
        print("   Premi 'q' per uscire\n")
        
        frame_delay = 1.0 / fps
        frame_count = 0
        success_count = 0
        
        while True:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret:
                if config.VERBOSE:
                    print("⚠️  Fine dello stream")
                break
                    
            
            if service_enabled:
                send_single_frame(frame)
                success_count += 1
            else:
                if config.VERBOSE:
                    print("⚠️  Servizio disabilitato, frame non inviato.")
            
            frame_count += 1
            
            # Mantieni FPS desiderati
            elapsed = time.time() - start_time
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)
        
        cap.release()
        cv2.destroyAllWindows()
        
        if config.VERBOSE:
            print(f"\n📊 Riepilogo:")
            print(f"   Frame totali: {frame_count}")
            print(f"   Inviati con successo: {success_count}")
            print(f"   Percentuale successo: {(success_count/frame_count*100):.1f}%")
        
    except KeyboardInterrupt:
        if config.VERBOSE:
            print("\n⚠️  Interruzione da tastiera")
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    initialize_coco_model()
    path_video = "./test_input/video3.mp4"
    path_image = "./test_input/test_frame.jpg"
    path_image2 = "./test_input/test_frame_scura.jpg"
    send_single_frame(cv2.imread(path_image))
    # send_video_stream(path_video, fps=30)
    
