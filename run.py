"""Avvio dell'applicazione principale e del server web."""

from server.web.appWeb import app
import server.config as config

import threading
from server.main import (
    initialize_ocr,
    initialize_visualization,
    initialize_database,
    processing_thread,
    stop_threads,
)

if __name__ == "__main__":
    print("🚀 Avvio sistema di elaborazione")

    initialize_ocr()
    visualization_manager = initialize_visualization()
    initialize_database()

    processing = threading.Thread(target=processing_thread, daemon=True)
    processing.start()

    if config.SHOW_VIDEO:

        web_thread = threading.Thread(
            target=lambda: app.run(port=5000, debug=False, use_reloader=False),
            daemon=True,
        )

        web_thread.start()

        print("🌐 Avvio server web")

        visualization_manager.handle_visualization()

    else:
        visualization = threading.Thread(
            target=visualization_manager.handle_visualization, daemon=True
        )
        visualization.start()

        print("🌐 Avvio server web")

        app.run(port=5000, debug=False, use_reloader=False)

    stop_threads.set()
    processing.join(timeout=2)
