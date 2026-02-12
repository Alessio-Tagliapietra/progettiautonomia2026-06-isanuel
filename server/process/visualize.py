"""
Modulo per la visualizzazione dei risultati
Disegna bounding box, label e informazioni sul frame
"""

import cv2
import numpy as np
import server.config as config
import time
import threading


class Visualization:
    def __init__(self, batch_size=config.BATCH_SIZE):
        self.batch_size = batch_size
        self.frame_buffer = []
        self.lock = threading.Lock()
        self.stop_flag = False

        self.colors = config.COLORS

        if config.VERBOSE:
            print(
                f"📺 Visualization inizializzata (SHOW_VIDEO={config.SHOW_VIDEO}, BATCH_SIZE={batch_size})"
            )

    def add_frame_to_magazine(self, frame, detections):
        if not config.SHOW_VIDEO:
            return

        with self.lock:
            annotated_frame = self.draw_boxes(frame.copy(), detections)

            self.frame_buffer.append(annotated_frame)

    def draw_boxes(self, frame, detections):

        for item in detections:
            # Estrai coordinate
            x1 = int(item["x1"])
            y1 = int(item["y1"])
            x2 = int(item["x2"])
            y2 = int(item["y2"])
            label = item["label"]
            track_id = item.get("track_id", None)
            score = item.get("score", 0)

            # Colore in base al label
            color = self.colors.get(label, (255, 255, 255))

            # Spessore box
            thickness = getattr(config, "BOX_THICKNESS", 2)

            # Disegna rettangolo
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            # Prepara testo label
            # if track_id is not None:
            #     text = f"ID:{track_id} {label}"
            # else:
            #     text = label
            if label == "authorized":
                text = "moto"
            elif label == "not_authorized":
                text = "auto"
            else:
                text = "veicolo_rilevato: " + label

            # Dimensione font
            font_scale = getattr(config, "FONT_SCALE", 0.5)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_thickness = 2

            # Calcola dimensioni testo per background
            (text_width, text_height), baseline = cv2.getTextSize(
                text, font, font_scale, font_thickness
            )

            # Disegna background per il testo
            cv2.rectangle(
                frame,
                (x1, y1 - text_height - baseline - 5),
                (x1 + text_width, y1),
                color,
                -1,  # Riempito
            )

            # Disegna testo
            cv2.putText(
                frame,
                text,
                (x1, y1 - baseline - 5),
                font,
                font_scale,
                (255, 255, 255),  # Testo bianco
                font_thickness,
            )

            # Opzionale: mostra confidenza
            if (
                hasattr(config, "SHOW_CONFIDENCE")
                and config.SHOW_CONFIDENCE
                and score > 0
            ):
                conf_text = f"{score:.2f}"
                cv2.putText(frame, conf_text, (x1, y2 + 20), font, 0.5, color, 1)

        return frame

    def show_frames(self, frames, window_name="Output", resize=True):
        """
        Mostra frame in una finestra

        Args:
            frame: frame da mostrare
            window_name: nome della finestra
            resize: se True, ridimensiona per adattarsi allo schermo

        Returns:
            False se l'utente preme 'q' o ESC, True altrimenti
        """

        for frame in frames:
            if frame is None:
                continue

            display_frame = frame.copy()

            # Ridimensiona se richiesto
            if resize and hasattr(config, "DISPLAY_WIDTH"):
                h, w = display_frame.shape[:2]
                new_w = config.DISPLAY_WIDTH
                scale = new_w / w
                new_h = int(h * scale)

                display_frame = cv2.resize(display_frame, (new_w, new_h))

            info_text = f"Buffer: {len(self.frame_buffer)} frames"
            cv2.putText(
                display_frame,
                info_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Mostra frame
            cv2.imshow(window_name, display_frame)

            # Gestione input tastiera
            key = cv2.waitKey(1) & 0xFF

            # 'q' o ESC per uscire
            if key == ord("q") or key == 27:
                return False

        return True

    def handle_visualization(self):
        if not config.SHOW_VIDEO:
            if config.VERBOSE:
                print("ℹ️ Visualizzazione disabilitata (SHOW_VIDEO=False)")
            return

        if config.VERBOSE:
            print("🎬 Thread visualizzazione avviato")
            print("   Premi 'q' o ESC per terminare la visualizzazione")

        window_created = False
        frames_shown = 0

        while not self.stop_flag:
            with self.lock:
                buffer_size = len(self.frame_buffer)

                # Strategia adattiva: mostra frame anche se non raggiungi il batch_size
                # dopo un certo tempo di attesa
                should_show = buffer_size >= self.batch_size or (
                    buffer_size > 0 and frames_shown == 0
                )

                if should_show:
                    # Estrai i frame da visualizzare
                    num_frames = min(self.batch_size, buffer_size)
                    batch = self.frame_buffer[:num_frames]
                    self.frame_buffer = self.frame_buffer[num_frames:]

                    if config.VERBOSE and frames_shown % 50 == 0:
                        print(
                            f"🎥 Frame visualizzati: {frames_shown} | Buffer: {len(self.frame_buffer)}"
                        )

                    # Crea finestra alla prima visualizzazione
                    if not window_created:
                        cv2.namedWindow("Vehicle Detection Output", cv2.WINDOW_NORMAL)
                        window_created = True
                        if config.VERBOSE:
                            print("✅ Finestra di visualizzazione creata")

                    # Mostra i frame
                    if not self.show_frames(batch):
                        # L'utente ha chiesto di uscire
                        self.stop_flag = True
                        break

                    frames_shown += len(batch)

                else:
                    # Nessun frame da mostrare, attendi
                    pass

            # Breve pausa per non sovraccaricare il lock
            time.sleep(0.01)

        # Visualizza eventuali frame rimanenti
        with self.lock:
            if len(self.frame_buffer) > 0:
                if config.VERBOSE:
                    print(
                        f"📤 Visualizzazione frame rimanenti: {len(self.frame_buffer)}"
                    )
                self.show_frames(self.frame_buffer)
                self.frame_buffer.clear()

        # Chiudi tutte le finestre OpenCV
        cv2.destroyAllWindows()

        if config.VERBOSE:
            print(
                f"✅ Thread visualizzazione terminato (totale frame visualizzati: {frames_shown})"
            )

    def stop(self):
        with self.lock:
            self.stop_flag = True
            if config.VERBOSE:
                print("🛑 Stop richiesto per thread visualizzazione")


# def create_mosaic(images, titles=None, grid_size=None):
#     """
#     Crea un mosaico di immagini (utile per debug)

#     Args:
#         images: lista di immagini
#         titles: lista di titoli (opzionale)
#         grid_size: tuple (rows, cols), se None calcola automaticamente

#     Returns:
#         immagine mosaico
#     """
#     if not images:
#         return None

#     n_images = len(images)

#     # Calcola grid size se non specificato
#     if grid_size is None:
#         cols = int(np.ceil(np.sqrt(n_images)))
#         rows = int(np.ceil(n_images / cols))
#     else:
#         rows, cols = grid_size

#     # Trova dimensioni massime
#     max_height = max(img.shape[0] for img in images)
#     max_width = max(img.shape[1] for img in images)

#     # Crea canvas
#     mosaic = np.zeros((max_height * rows, max_width * cols, 3), dtype=np.uint8)

#     # Riempi mosaico
#     for i, img in enumerate(images):
#         row = i // cols
#         col = i % cols

#         # Converti in BGR se grayscale
#         if len(img.shape) == 2:
#             img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

#         # Ridimensiona se necessario
#         if img.shape[0] != max_height or img.shape[1] != max_width:
#             img = cv2.resize(img, (max_width, max_height))

#         # Posiziona nel mosaico
#         y_start = row * max_height
#         x_start = col * max_width
#         mosaic[y_start:y_start+max_height, x_start:x_start+max_width] = img

#         # Aggiungi titolo se presente
#         if titles and i < len(titles):
#             cv2.putText(
#                 mosaic,
#                 titles[i],
#                 (x_start + 10, y_start + 30),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.7,
#                 (255, 255, 255),
#                 2
#             )

#     return mosaic


# def draw_detection_zones(frame, zones):
#     """
#     Disegna zone di detection (es. ingresso, uscita)

#     Args:
#         frame: frame video
#         zones: lista di dict con 'points' (poligono) e 'label'

#     Returns:
#         frame con zone
#     """
#     annotated_frame = frame.copy()
#     overlay = annotated_frame.copy()

#     colors = [
#         (0, 255, 0),    # Verde
#         (255, 0, 0),    # Blu
#         (0, 255, 255),  # Giallo
#         (255, 0, 255),  # Magenta
#     ]

#     for i, zone in enumerate(zones):
#         points = np.array(zone['points'], dtype=np.int32)
#         label = zone.get('label', f'Zone {i+1}')
#         color = colors[i % len(colors)]

#         # Disegna poligono semi-trasparente
#         cv2.fillPoly(overlay, [points], color)

#         # Disegna bordo
#         cv2.polylines(annotated_frame, [points], True, color, 2)

#         # Aggiungi label
#         centroid = points.mean(axis=0).astype(int)
#         cv2.putText(
#             annotated_frame,
#             label,
#             tuple(centroid),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.7,
#             (255, 255, 255),
#             2
#         )

#     # Blend overlay
#     cv2.addWeighted(overlay, 0.3, annotated_frame, 0.7, 0, annotated_frame)

#     return annotated_frame


# # ============================================================================
# # FUNZIONI UTILITY
# # ============================================================================

# def get_text_size(text, font_scale=0.7, font_thickness=2):
#     """Calcola dimensioni di un testo"""
#     font = cv2.FONT_HERSHEY_SIMPLEX
#     (width, height), baseline = cv2.getTextSize(
#         text, font, font_scale, font_thickness
#     )
#     return width, height, baseline


# def put_text_with_background(frame, text, position, color=(255, 255, 255),
#                              bg_color=(0, 0, 0), font_scale=0.7, font_thickness=2):
#     """Disegna testo con background"""
#     x, y = position
#     font = cv2.FONT_HERSHEY_SIMPLEX

#     width, height, baseline = get_text_size(text, font_scale, font_thickness)

#     # Background
#     cv2.rectangle(
#         frame,
#         (x, y - height - baseline),
#         (x + width, y + baseline),
#         bg_color,
#         -1
#     )

#     # Testo
#     cv2.putText(
#         frame,
#         text,
#         (x, y),
#         font,
#         font_scale,
#         color,
#         font_thickness
#     )


# def draw_progress_bar(frame, progress, position=(10, 10), size=(200, 20),
#                      color=(0, 255, 0), bg_color=(50, 50, 50)):
#     """Disegna una barra di progresso"""
#     x, y = position
#     width, height = size

#     # Background
#     cv2.rectangle(frame, (x, y), (x + width, y + height), bg_color, -1)

#     # Progress
#     progress_width = int(width * progress)
#     cv2.rectangle(frame, (x, y), (x + progress_width, y + height), color, -1)

#     # Bordo
#     cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 255, 255), 1)

#     # Percentuale
#     text = f"{int(progress * 100)}%"
#     text_x = x + width // 2 - 20
#     text_y = y + height // 2 + 5
#     cv2.putText(frame, text, (text_x, text_y),
#                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
