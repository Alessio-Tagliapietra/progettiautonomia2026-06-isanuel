from flask import Blueprint, request, jsonify, Response
import requests
import cv2
import numpy as np
from datetime import datetime
import json
import time
import threading

from server.control.frame_queue import frame_queue
import server.config as config

receiver = Blueprint("receiver", __name__)

# Contatori per statistiche
stats = {
    "total_received": 0,
    "total_success": 0,
    "total_errors": 0,
    "queue_full_count": 0
}

service_enabled = False

def check_camera_auth(req):
    if not config.REQUIRE_CAMERA_AUTH:
        return True

    camera_id = req.headers.get("camera-id")
    api_key = req.headers.get("API-Key")

    if not camera_id or not api_key:
        return False

    expected_key = config.AUTHORIZED_CAMERAS.get(camera_id)
    return expected_key == api_key


@receiver.route("/api/upload", methods=["POST"])
def upload_frame():
    """Riceve un frame via HTTP POST e lo inserisce nella queue"""
    
    if not check_camera_auth(request):
        stats["total_errors"] += 1
        return jsonify({
            "error": "unauthorized",
            "hint": "missing or invalid camera-id/API-Key headers"
        }), 401
    
    stats["total_received"] += 1
    
    # Verifica presenza file
    if "image" not in request.files:
        stats["total_errors"] += 1
        return jsonify({
            "error": "no image field in request",
            "hint": "use files={'image': ...}"
        }), 400
        
    # Verifica presenza metadata
    if "metadata" not in request.form:
        stats["total_errors"] += 1
        return jsonify({
            "error": "no metadata field in request",
            "hint": "use form-data={'metadata': ...}"
        }), 400

    file = request.files["image"]
    metadata_raw = request.form.get("metadata")
    metadata = json.loads(metadata_raw) if metadata_raw else {}

    
    if not file:
        stats["total_errors"] += 1
        return jsonify({"error": "empty file"}), 400
    
    if not metadata:
        stats["total_errors"] += 1
        return jsonify({"error": "empty metadata"}), 400

    try:
        # Leggi e decodifica immagine
        img_bytes = file.read()
        np_img = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if frame is None:
            stats["total_errors"] += 1
            return jsonify({"error": "invalid image format"}), 400

        # Verifica se la queue è piena
        if frame_queue.full():
            stats["queue_full_count"] += 1
            return jsonify({
                "error": "queue full",
                "queue_size": frame_queue.qsize(),
                "hint": "server is processing frames, try again later"
            }), 429

        # Inserisci nella queue
        frame_queue.put([frame, metadata])
        stats["total_success"] += 1
        
        # Log ogni 10 frame
        if stats["total_success"] % 10 == 0:
            print(f"📡 Frame ricevuti: {stats['total_success']} | Queue size: {frame_queue.qsize()}")
        
        return jsonify({
            "ok": True,
            "timestamp": datetime.now().isoformat(),
            "queue_size": frame_queue.qsize(),
            "frame_shape": frame.shape
        }), 200
        
    except Exception as e:
        stats["total_errors"] += 1
        print(f"❌ Errore nel processing del frame: {e}")
        return jsonify({
            "error": "processing error",
            "details": str(e)
        }), 500



@receiver.route("/api/service/state", methods=["GET"])
def service_state_stream():
    """Server-Sent Events per aggiornare i client sullo stato del servizio"""
    def event_stream():
        last_state = None
        while True:
            global service_enabled
            if service_enabled != last_state:
                yield f"data: {service_enabled}\n\n"
                last_state = service_enabled
            time.sleep(0.1)
    return Response(event_stream(), mimetype="text/event-stream")


@receiver.route("/api/service/set", methods=["POST"])
def set_service_state():
    """Endpoint web per abilitare/disabilitare il servizio"""
    global service_enabled
    data = request.get_json() or {}
    enabled = data.get("enabled")
    if enabled is None:
        return jsonify({"error": "missing 'enabled' field"}), 400
    service_enabled = bool(enabled)
    return jsonify({"service_enabled": service_enabled}), 200

# @receiver.route("/api/stats", methods=["GET"])
# def get_stats():
#     """Ritorna statistiche sulla ricezione frame"""
#     return jsonify({
#         "statistics": stats,
#         "queue_size": frame_queue.qsize(),
#         "queue_maxsize": frame_queue.maxsize
#     }), 200


# @receiver.route("/api/health", methods=["GET"])
# def health_check():
#     """Health check endpoint"""
#     return jsonify({
#         "status": "ok",
#         "queue_available": not frame_queue.full(),
#         "queue_size": frame_queue.qsize()
#     }), 200