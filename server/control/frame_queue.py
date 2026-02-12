from queue import Queue
import server.config as config

frame_queue = Queue(maxsize=100)

if config.VERBOSE:
    print("📥 Inizializzata Frame Queue")