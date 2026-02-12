"""
ocr_utils.py

Modulo per la gestione della lettura targhe tramite ocr

funzione offerte:
- preprocess_plate
- read_plate_ocr
- read_plate_preprocessed
- read_plate_filtered
- read_plate_thresholded
- no_filtering
- read_plate_multiple_methods
- clean_ocr_text
- improve_plate_text
- process_plate_ocr
- find_best_plate_reading
- save_plate_image
- save_debug_plate
- save_vehicle_image
"""

try:
    import cv2
    import numpy as np
    import os
    import time
    import server.config as config
    import re
    import server.config as config
    import pytesseract
    from server.control.context import get_context
except ImportError as e:
    print(f"Errore import OCR utils: {e}")


INT_POS_CORRECTION = {
    "O": "0",
    "Q": "0",
    "U": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "J": "3",
    "A": "4",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
    "g": "9",
    "Z": "2",
}

# sono presenti ache lettere come chiavi poiché
# le targhe italiano escludono le lettere O, I, Q, U
CHAR_POS_CORRECTION = {
    "0": "D",
    "1": "L",
    "2": "Z",
    "3": "J",
    "4": "A",
    "5": "S",
    "6": "G",
    "7": "T",
    "8": "B",
    "9": "D",
    "I": "L",
    "O": "D",
    "Q": "D",
    "U": "V",
}


# ============================================================================
# PREPROCESSING TARGHE ANGOLATE
# ============================================================================


def correct_perspective(plate_img_gray: np.ndarray) -> np.ndarray:
    """
    Corregge prospettiva di targhe angolate
    """
    try:

        # Trova contorni
        _, binary = cv2.threshold(
            plate_img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return plate_img_gray

        # contorno più graned: quello della targa
        largest_contour = max(contours, key=cv2.contourArea)

        # rettangolo minimo ruotato
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.round(box).astype(int)

        # Calcola angolo di rotazione
        angle = rect[2]
        if angle < -45:
            angle += 90

        # Ruota solo se l'angolo è significativo
        if abs(angle) > 5:
            if config.VERBOSE:
                print(f"     Correzione prospettiva: angle={angle:.1f}°")

            h, w = plate_img_gray.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                plate_img_gray,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            return rotated

        return plate_img_gray

    except Exception as e:
        if config.VERBOSE:
            print(f"     Errore correzione prospettiva: {e}")
        return plate_img_gray


# ============================================================================
# LETTURA E PREPROCESSING
# ============================================================================


def preprocess_plate(plate_img: np.ndarray) -> np.ndarray:

    # Converti in grayscale
    if len(plate_img.shape) == 3:
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_img.copy()

    # analisi immagine
    brightness = np.mean(gray)
    contrast = gray.std()

    if config.VERBOSE:
        print(
            f"     Qualità immagine: brightness={brightness:.1f}, contrast={contrast:.1f}"
        )

    # ridimensionamento
    h, w = gray.shape
    target_height = config.TARGET_HEIGHT  # Altezza ottimale per LPR
    if h < target_height:
        scale = target_height / h
        resized = cv2.resize(
            gray, (int(w * scale), target_height), interpolation=cv2.INTER_CUBIC
        )
    else:
        resized = gray

    processed = resized.copy()

    if brightness < 100:
        # Equalizzazione istogramma
        processed = cv2.equalizeHist(resized)

    if contrast < 30:
        # CLAHE per contrasto adattivo
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        processed = clahe.apply(processed)

    # Denoising
    denoised = cv2.fastNlMeansDenoising(
        processed, None, h=10, templateWindowSize=7, searchWindowSize=21
    )

    # Sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    # corrected = correct_perspective(sharpened) #disabilitato, test

    rgb = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)

    save_debug_plate(plate_img, rgb)
    return rgb


def read_plate_tesseract_fast(plate_img: np.ndarray) -> tuple:
    """
    Tesseract veloce per fallback
    Ottimizzato per targhe angolate
    """
    if not config.TESSERACT_AVAILABLE:
        return "", 0.0

    pytesseract.pytesseract.tesseract_cmd = (
        config.TESSERACT_CMD_PATH
    )  # se da problemi con il path utilizzare questa riga per settarlo manualmente

    start_time = time.time()

    try:
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img.copy()

        # Ridimensiona
        h, w = gray.shape
        scale = 3
        resized = cv2.resize(
            gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC
        )

        # Binarizzazione
        _, binary = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Inverte se sfondo scuro
        if np.mean(binary) < 127:
            binary = cv2.bitwise_not(binary)

        # Config Tesseract per targhe
        config_str = (
            "--oem 1 "
            "--psm 7 "
            "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

        # OCR
        data = pytesseract.image_to_data(
            binary, config=config_str, output_type=pytesseract.Output.DICT
        )

        # Estrai testo
        texts = []
        confs = []
        for i, conf in enumerate(data["conf"]):
            if conf >= 0:
                text = data["text"][i].strip()
                if text:
                    texts.append(text)
                    confs.append(conf)

        if not texts:
            return "", 0.0

        full_text = "".join(texts).upper()
        full_text = clean_ocr_text(full_text)
        avg_conf = sum(confs) / len(confs) / 100.0 if confs else 0.0

        elapsed = (time.time() - start_time) * 1000
        print(
            f"       Tesseract: '{full_text}' (conf: {avg_conf:.2f}, {elapsed:.0f}ms)"
        )

        return full_text, avg_conf

    except Exception as e:
        print(f"     ❌ Tesseract error: {e}")
        return "", 0.0


def read_plate_fast_ocr(plate_img: np.ndarray) -> tuple:

    if not config.FAST_OCR_AVAILABLE:
        return "", 0.0

    recognizer = get_context("recognizer")

    if recognizer is None:
        if config.VERBOSE:
            print("     ❌ LPR non inizializzato correttamente")
        return "", 0.0

    start_time = time.time()
    try:

        preprocessed = preprocess_plate(plate_img)
        result = recognizer.run(preprocessed)
        # debug
        # print("="*50)
        # print(result)
        # print("="*50)

        if result and len(result) > 0:
            text = result[0] if isinstance(result, (list, tuple)) else str(result)
            text = clean_ocr_text(text)

            # Calcola confidence
            confidence = calculate_confidence(text)

            elapsed = (time.time() - start_time) * 1000

            if config.VERBOSE:
                print(f"     LPR: '{text}' (conf: {confidence:.2f}, {elapsed:.0f}ms)")

            return text, confidence

        return "", 0.0

    except Exception as e:
        if config.VERBOSE:
            print(f"     ❌ LPR error: {e}")
        return "", 0.0


def read_plate_multiple_methods(plate_img: np.ndarray) -> tuple:
    """
    Strategia ottimale per il tuo caso:
    1. Fast Plate OCR (LPR)
    2. Se bassa confidenza, Tesseract (fallback)
    3. Se entrambi danno risultati, confronta

    Returns:
        (text, confidence, method)
    """

    results = []

    # Fast Plate OCR (LPR)
    if config.USE_FAST_OCR:
        text_lpr, conf_lpr = read_plate_fast_ocr(plate_img)
        if text_lpr and len(text_lpr) >= 6:
            results.append((text_lpr, conf_lpr, "LPR"))

        if conf_lpr >= config.OCR_MIN_CONFIDENCE and is_valid_format(text_lpr):
            if config.VERBOSE:
                print(f"     ✅ LPR confident result")
            return text_lpr, conf_lpr, "LPR"

    # Tesseract:
    # - LPR non disponibile
    # - LPR bassa confidenza
    # - LPR fallisce
    if config.TESSERACT_AVAILABLE:
        text_tess, conf_tess = read_plate_tesseract_fast(plate_img)
        if text_tess and len(text_tess) >= 6:
            results.append((text_tess, conf_tess, "tesseract"))
            if not config.FAST_OCR_AVAILABLE:
                if config.VERBOSE:
                    print(f"     ✅ Tesseract result used (LPR not available)")
                return text_tess, conf_tess, "tesseract"

    # nessun risultato valido
    if not results:
        return "", 0.0, "none"

    # scelta del migliore

    # filtraggio risultati con formato valido
    valid_results = [(t, c, m) for t, c, m in results if is_valid_format(t)]

    if valid_results:
        # Prendi il migliore tra quelli con formato valido
        best = max(valid_results, key=lambda x: x[1])
    else:
        # Nessuno con formato valido, prendi quello con confidence più alta
        best = max(results, key=lambda x: x[1])

    text, conf, method = best

    # Se abbiamo risultati da entrambi e concordano, aumenta confidence
    if len(results) >= 2:
        if results[0][0] == results[1][0]:  # Stesso testo
            conf = min(conf + 0.1, 1.0)
            if config.VERBOSE:
                print(f"       ✅ Agreement between methods → confidence boost")

    return text, conf, method


def process_plate_ocr(
    plate_img: np.ndarray, track_id: int, frame_count: int, plate_index: int
) -> tuple:

    if config.SAVE_PLATE_IMAGES:
        save_plate_image(plate_img, track_id, frame_count, plate_index)

    plate_text, ocr_conf, method = read_plate_multiple_methods(plate_img)

    if not plate_text:
        return None, 0.0, None

    if len(plate_text) < 6:
        return None, 0.0, None

    plate_text = improve_plate_text(plate_text)

    if not plate_text:
        print("     ✗ Unable to improve plate text")
        return None, 0.0, None

    return plate_text, ocr_conf, method


def find_best_plate_reading(plates: list, track_id: int, frame_count: int) -> tuple:
    best_result = None
    best_confidence = 0.0

    for i, plate_data in enumerate(plates):
        plate_img = plate_data["image"]
        detection_score = plate_data["score"]

        if config.VERBOSE:
            print(f"\n   Targa {i+1}:")
            print(f"     Detection confidence: {detection_score:.2f}")
            print(f"     Size: {plate_img.shape[1]}x{plate_img.shape[0]}")

        plate_text, ocr_conf, method = process_plate_ocr(
            plate_img, track_id, frame_count, i
        )

        if not plate_text:
            continue

        if config.VERBOSE:
            print(
                f"     OCR raw: {plate_text} (conf: {ocr_conf:.2f}, method: {method})"
            )

        if ocr_conf > best_confidence:
            best_result = plate_text
            best_confidence = ocr_conf

    return best_result, best_confidence


# ============================================================================
# CLEANING E IMPROVEMENT
# ============================================================================


def clean_ocr_text(text: str) -> str:
    # Rimuove spazi
    text_clean = text.upper().replace(" ", "")

    # Rimuove caratteri non alfanumerici
    text_clean = re.sub(r"[^A-Z0-9]", "", text_clean)

    return text_clean


def is_valid_format(text):
    """
    Verifica formato targa italiana
    AA000AA (moderno) o AA00000 (vecchio)
    """

    if len(text) == 7:
        # Formato moderno
        return text[0:2].isalpha() and text[2:5].isdigit() and text[5:7].isalpha()

    return False


def improve_plate_text(text: str) -> str:
    """Corregge caratteri comuni OCR"""

    # Verifica formato base
    if len(text) < 7:
        return None

    # tronca se troppo lungo
    if len(text) > 7:
        text = text[:7]

    result = ""

    # formato targa italiana --> AA000AA
    #                           0123456
    # le prime due lettere

    for i, char in enumerate(text):

        # char
        if i in [0, 1, 5, 6]:
            if char in CHAR_POS_CORRECTION:
                result += CHAR_POS_CORRECTION[char]
            else:
                result += char
        # digit
        if i in [2, 3, 4]:
            if char in INT_POS_CORRECTION:
                result += INT_POS_CORRECTION[char]
            else:
                result += char

    return result


def calculate_confidence(text: str) -> float:
    """
    Calcola confidence basata su caratteristiche del testo
    """
    if not text:
        return 0.0

    confidence = 0.5  # Base

    # Lunghezza corretta
    if len(text) == 7:
        confidence += 0.2
    elif len(text) in [6, 8]:
        confidence += 0.1

    # Formato valido
    if is_valid_format(text):
        confidence += 0.3

    # Nessun carattere strano
    if text.isalnum():
        confidence += 0.1

    return min(confidence, 1.0)


# ============================================================================
# SALVATAGGIO
# ============================================================================


def save_plate_image(
    plate_img: np.ndarray, track_id: int, frame_count: int, plate_index: int
):
    if config.SAVE_PLATE_IMAGES:
        os.makedirs(config.PLATE_IMAGES_DIR, exist_ok=True)
        filename = (
            f"{config.PLATE_IMAGES_DIR}/{track_id}_{frame_count}_{plate_index}.jpg"
        )
        cv2.imwrite(filename, plate_img)


def save_debug_plate(plate_img: np.ndarray, cleaned: np.ndarray):

    if config.SAVE_DEBUG_PLATES:
        os.makedirs(config.PLATE_IMAGES_DIR_DEBUG, exist_ok=True)
        timestamp = int(time.time() * 1000)
        cv2.imwrite(
            f"{config.PLATE_IMAGES_DIR_DEBUG}/original_{timestamp}.jpg", plate_img
        )
        cv2.imwrite(
            f"{config.PLATE_IMAGES_DIR_DEBUG}/processed_{timestamp}.jpg", cleaned
        )


def save_vehicle_image(vehicle_crop: np.ndarray, track_id: int, frame_count: int):

    if config.SAVE_VEHICLE_IMAGES:
        os.makedirs(config.VEHICLE_IMAGES_DIR, exist_ok=True)
        filename = f"{config.VEHICLE_IMAGES_DIR}/{track_id}_{frame_count}.jpg"
        cv2.imwrite(filename, vehicle_crop)
