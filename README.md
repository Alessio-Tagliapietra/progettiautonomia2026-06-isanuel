# 🚗 Sistema di Rilevamento Targhe Automatico

Sistema intelligente per il controllo accessi veicolari basato su Computer Vision, riconoscimento targhe OCR e database autorizzazioni.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg)](https://github.com/ultralytics/ultralytics)

---

## 📋 Indice

- [Caratteristiche](#-caratteristiche)
- [Demo](#-demo)
- [Architettura](#️-architettura)
- [Requisiti](#-requisiti)
- [Installazione Rapida](#-installazione-rapida)
- [Configurazione](#️-configurazione)
- [Utilizzo](#-utilizzo)
- [Struttura Progetto](#-struttura-progetto)
- [API Endpoints](#-api-endpoints)
- [Sviluppo](#sviluppo)
- [Troubleshooting](#-troubleshooting)
- [Contribuire](#contribuire)
- [Licenza](#licenza)
- [Documentazione](#documentazione)
---

## ✨ Caratteristiche

### 🎯 Funzionalità Principali

- ✅ **Rilevamento Veicoli Multi-Classe** - Auto, moto, bus, camion, biciclette (YOLOv8)
- 🔍 **Detection Targhe** - Rilevamento ad alta precisione delle targhe veicolari
- 📖 **OCR Avanzato** - Lettura targhe con doppio motore (Tesseract + Fast Plate OCR)
- 🎯 **Tracking Multi-Oggetto** - Algoritmo SORT per tracciamento persistente
- 🗄️ **Database Integrato** - SQLite per gestione targhe autorizzate e log accessi
- 🌐 **Interfaccia Web Responsive** - Dashboard completa per gestione sistema
- 🔐 **Autenticazione OAuth 2.0** - Login sicuro con Google
- 📊 **Analytics e Reportistica** - Statistiche, export CSV, visualizzazione storico
- ⚡ **Elaborazione Real-Time** - Pipeline ottimizzata per prestazioni elevate
- 🔧 **Architettura Modulare** - Client-Server per deployment distribuito

| Componente          | Tecnologia                            |
| ------------------- | ------------------------------------- |
| **Computer Vision** | YOLOv8 (Ultralytics)                  |
| **OCR**             | Tesseract, Fast Plate OCR             |
| **Tracking**        | SORT (Simple Online Realtime Tracker) |
| **Backend**         | Python 3.10+, Flask                   |
| **Database**        | SQLite3                               |
| **Frontend**        | HTML5, Bootstrap 5, JavaScript        |
| **Autenticazione**  | OAuth 2.0 (Google)                    |
| **Deep Learning**   | PyTorch, CUDA                         |

---

## 🎬 Demo

### Screenshot

**Dashboard Principale**

```
┌──────────────────────────────────────────────┐
│  🔐 Autenticazione Google                    |
│  Login effettuato come: user@gmail.com       │
│                                              │
│                                              │
│  🚗 Gestione Targhe Autorizzate              │
│  ┌────────────────────────────────────────┐  │
│  │ AB123CD | Mario Rossi | Attiva         │  │
│  │ XY789ZK | —           | Scaduta        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  📋 Log Accessi                              │
│  ┌────────────────────────────────────────┐  │
│  │ 2025-01-10 14:30 | AB123CD | OK        │  │
│  │ 2025-01-10 14:32 | XY789ZK | NEGATO    │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘


```

**Rilevamento in Tempo Reale**

```
Frame: 1523 | FPS: 28.5
┌────────────────────────────────────┐
│  [🚗 Car - ID:42]                 │
│  ┌──────────────────┐              │
│  │  [AB123CD]       │              │
│  │  Conf: 0.89      │              │
│  │  ✅ AUTORIZZATO  │             │
│  └──────────────────┘              │
└────────────────────────────────────┘
```

---

## 🏗️ Architettura

### Diagramma del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Camera     │  │    Video     │  │   Webcam     │   │
│  │   IP/RTSP    │  │    File      │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                           │                             |
│                           |                             |
│           1. Vehicle Detection (YOLOv8)                 │
|                           |                             |
│                    [Frame Queue]                        │
└───────────────────────────┼─────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   PROCESSING LAYER                     │
│  ┌────────────────────────────────────────────────┐    │
│  │     ↓                                          │    │
│  │  2. Multi-Object Tracking (SORT)               │    │
│  │     ↓                                          │    │
│  │  3. Plate Detection (YOLO Custom)              │    │
│  │     ↓                                          │    │
│  │  4. OCR (Tesseract + Fast Plate OCR)           │    │
│  │     ↓                                          │    │
│  │  5. Authorization Check (Database)             │    │
│  │     ↓                                          │    │
│  │  6. Logging & Visualization                    │    │
│  └────────────────────────────────────────────────┘    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   DATA LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   SQLite     │  │     CSV      │  │    Images    │  │
│  │   Database   │  │    Export    │  │    Debug     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   WEB INTERFACE                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Flask Application (Port 5000)                   │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │ Dashboard  │  │   Plates   │  │    Logs    │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  OAuth 2.0 (Google Authentication)         │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Flusso di Elaborazione

```python
Frame Input
    ↓
YOLO Vehicle Detection (cars, bikes, buses, trucks)
    ↓
SORT Tracking (persistent IDs)
    ↓
Vehicle Classification (2-wheels → auto-authorize | 4-wheels → check plate)
    ↓
YOLO Plate Detection (locate plate in vehicle crop)
    ↓
Image Preprocessing (scaling, denoising, sharpening)
    ↓
OCR Dual-Engine (Tesseract + Fast Plate OCR)
    ↓
Text Correction (format validation, character mapping)
    ↓
Database Authorization Check
    ↓
Log Access + Update UI

```

---

## 📦 Requisiti

### Hardware

| Componente  | Minimo            | Consigliato             |
| ----------- | ----------------- | ----------------------- |
| **CPU**     | Quad-core 2.5 GHz | 8-core 3.0+ GHz         |
| **RAM**     | 8 GB              | 16 GB+                  |
| **GPU**     | -                 | NVIDIA GPU (CUDA 11.8+) |
| **Storage** | 5 GB              | 10 GB+ SSD              |

### Software

| Requisito         | Versione                                |
| ----------------- | --------------------------------------- |
| **Python**        | ≥ 3.10                                  |
| **OS**            | Windows 10/11, Ubuntu 20.04+, macOS 11+ |
| **CUDA**          | 11.8+ (opzionale, per GPU)              |
| **Tesseract OCR** | 5.0+ (opzionale)                        |

---

## 🚀 Installazione Rapida

### 1. Clone Repository

```bash
git clone https://gitlab.com/manuel.sannicolo07/plate_detection.git
cd plate_detection
```

### 2. Ambiente Virtuale

**Windows:**

```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installa Dipendenze

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Tesseract OCR (Opzionale)

**Windows:**

- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Installa in `C:\Program Files\Tesseract-OCR\`

**Linux:**

```bash
sudo apt update
sudo apt install tesseract-ocr
```

**macOS:**

```bash
brew install tesseract
```

### 5. Configura OAuth Google

1. Vai a [Google Cloud Console](https://console.cloud.google.com)
2. Crea progetto
3. Abilita Google+ API
4. Crea credenziali OAuth 2.0
5. Aggiungi URI: `http://localhost:5000/callback`
6. Copia Client ID e Secret in `server/config.py`:

```python
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"
```

### 6. Aggiungi Utenti Autorizzati

In `server/config.py`:

```python
AUTHORIZED_USERS = [
    "your-email@gmail.com",
    "admin@domain.com"
]
```

### 7. Avvia il Sistema

```bash
python run.py
```

### 8. Accedi all'Interfaccia

Apri browser: `http://localhost:5000`

---

## ⚙️ Configurazione

### Configurazione Base

File principale: `server/config.py`

#### **Modalità Operativa**

```python
# LOCAL: usa webcam o video file
# NON-LOCAL: riceve frame via HTTP
FRAME_SOURCE = "local"  # o "non-local"
```

#### **Sorgente Video**

```python
# File video
VIDEO_PATH = "video3.mp4"
USE_WEBCAM = False

# Webcam
USE_WEBCAM = True
```

#### **Dispositivo**

```python
# Auto-detect GPU
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Forza CPU
DEVICE = 'cpu'
```

#### **Soglie Detection**

```python
# Confidenza veicoli (0.0-1.0)
DETECTION_CONFIDENCE = 0.2

# Confidenza targhe (0.0-1.0)
PLATE_DETECTION_CONFIDENCE = 0.2

# Confidenza OCR minima (0.0-1.0)
OCR_MIN_CONFIDENCE = 0.2
```

#### **Tracking SORT**

```python
TRACKER_MAX_AGE = 30        # Frame max senza detection
TRACKER_MIN_HITS = 3        # Detection minime per conferma
TRACKER_IOU_THRESHOLD = 0.3 # Soglia overlap
```

### Configurazioni Avanzate

Consulta la [Documentazione Completa](docs/configuration.md) per tutte le opzioni.

---

## 🎮 Utilizzo

### Modalità Standalone (Local)

**1. Configura sorgente:**

```python
# server/config.py
FRAME_SOURCE = "local"
VIDEO_PATH = "path/to/video.mp4"
```

**2. Avvia:**

```bash
python run.py
```

**3. Accedi:** `http://localhost:5000`

---

### Modalità Client-Server

**Architettura:**

```
[Client - Camera] --HTTP--> [Server - Processing + Web]
```

#### **Server Side**

**1. Configura:**

```python
# server/config.py
FRAME_SOURCE = "non-local"
AUTHORIZED_CAMERAS = {
    "camera_01": "secret-api-key-123"
}
```

**2. Avvia:**

```bash
python run.py
```

#### **Client Side**

**1. Configura:**

```python
# client/config.py
SERVER_URL = "http://192.168.1.100:5000/api/upload"
headers = {
    "camera-id": "camera_01",
    "API-Key": "secret-api-key-123"
}
```

**2. Avvia (terminale separato):**

```bash
cd client
python sender.py
```

---

### Gestione via Web Interface

#### **Dashboard**

- Statistiche real-time
- Controllo servizio (start/stop)
- Accessi recenti

#### **Gestione Targhe**

```
Targhe → Aggiungi Nuova Targa
- Numero: AB123CD
- Nome: Mario
- Cognome: Rossi
- Ruolo: Docente
- Scadenza: 2025-12-31
```

#### **Log Accessi**

```
Log → Filtri
- Per targa: AB123CD
- Per stato: Autorizzato/Non autorizzato
- Export CSV
```

---

## 📁 Struttura Progetto

```
plate_detection/
│
├── 📂 client/                    # Modulo client (invio frame)
│   ├── client.py                 # Script principale
│   ├── config.py                 # Config client
│   └── detection.py              # Detection lato client
│
├── 📂 server/                    # Modulo server (processing)
│   │
│   ├── 📂 connection/            # Comunicazione HTTP
│   │   └── frame_receiver.py    # Endpoints ricezione
│   │
│   ├── 📂 control/               # Logica controllo
│   │   ├── context.py           # Context manager
│   │   └── frame_queue.py       # Queue frame
│   │
│   ├── 📂 data/                  # Dati persistenti
│   │   ├── authorized_plates.db # Database SQLite
│   │   └── detected_plates.csv  # Export CSV
│   │
│   ├── 📂 process/               # Pipeline elaborazione
│   │   ├── detection.py         # Detection veicoli/targhe
│   │   ├── ocr_utils.py         # OCR e preprocessing
│   │   ├── plate_utils.py       # Verifica autorizzazioni
│   │   ├── vehicle_utils.py     # Processing veicoli
│   │   └── visualize.py         # Rendering
│   │
│   ├── 📂 web/                   # Interfaccia web
│   │   ├── 📂 static/           # CSS, JS
│   │   ├── 📂 templates/        # HTML
│   │   ├── appWeb.py            # Flask app
│   │   └── user.py              # User model
│   │
│   ├── config.py                 # ⚙️ Configurazione principale
│   ├── database.py               # Database manager
│   └── main.py                   # Entry point processing
│
├── 📂 models/yolo/               # Modelli YOLO
│   ├── yolov8n.pt               # Veicoli/pedoni
│   └── license_plate_detector.pt # Targhe
│
├── 📂 docs/                      # Documentazione
│   ├── project_analysis.md          # Analisi progetto
│   ├── prohject_design.md         # Design progetto
│   ├── startup_instructions.md    # Guida installazione
│   ├── test.md           # Collaudo e report
│   ├── implementation.md           # Implementazione
│   └── user_manual.md           # Manuale utente
|
├── run.py                        # 🚀 Avvio sistema completo
├── requirements.txt              # Dipendenze Python
├── .gitignore
├── LICENSE
└── README.md                     # Questo file
```

---

## 🔌 API Endpoints

### Frame Upload (Client → Server)

**POST** `/api/upload`

```bash
curl -X POST http://localhost:5000/api/upload \
  -H "camera-id: camera_01" \
  -H "API-Key: secret-key" \
  -F "image=@frame.jpg" \
  -F 'metadata={"detections": [...]}'
```

**Response:**

```json
{
	"ok": true,
	"timestamp": "2025-01-10T14:30:15.123456",
	"queue_size": 5,
	"frame_shape": [720, 1280, 3]
}
```

## 🛠️ Sviluppo

### Setup Ambiente Dev

```bash
# Clone
git clone https://gitlab.com/manuel.sannicolo07/plate_detection.git
cd plate_detection

# Venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install con dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # (se presente)

# Pre-commit hooks
pre-commit install
```

### Test Configurazione

```bash
python server/config.py
```

Output atteso:

```
🔧 Test configurazione...
✅ Configurazione valida!
📋 Targhe autorizzate: 10
   - AB123CD
   - XY789ZK
   ...
```

### Debug Mode

```python
# server/config.py
VERBOSE = True
SHOW_VIDEO = True
SAVE_DEBUG_PLATES = True
SAVE_PLATE_IMAGES = True
SAVE_VEHICLE_IMAGES = True
```

### Test Singoli Moduli

**Database:**

```bash
python server/database.py
```

**Detection:**

```bash
python server/process/detection.py
```

**OCR:**

```bash
python server/process/ocr_utils.py
```

---

## 🐛 Troubleshooting

### Problema: CUDA not available

**Soluzione:**

```bash
# Verifica CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Reinstalla PyTorch con CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

### Problema: Tesseract non trovato

**Windows:**

```python
# server/config.py
TESSERACT_CMD_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**Linux:**

```bash
sudo apt install tesseract-ocr
```

---

### Problema: OAuth redirect_uri_mismatch

**Soluzione:**

1. Google Cloud Console → Credenziali
2. Modifica OAuth Client ID
3. Aggiungi: `http://localhost:5000/callback`
4. Salva

---

### Problema: Performance lente

**Soluzioni:**

- Usa GPU (CUDA)
- Riduci risoluzione video
- Aumenta soglie confidenza
- Disabilita `SHOW_VIDEO`

```python
DETECTION_CONFIDENCE = 0.5  # Aumenta da 0.2
SHOW_VIDEO = False
DEVICE = 'cuda'
```

---

### Log Debug Completi

```python
# server/config.py
VERBOSE = True
SAVE_PLATE_IMAGES = True
SAVE_DEBUG_PLATES = True
SAVE_VEHICLE_IMAGES = True

```

Immagini salvate in:

- `server/data/image_results/detected_plates/`
- `server/data/image_results/debug_plates/`
- `server/data/image_results/detected_vehicles/`

## Contribuire

Contributi, bug reports e feature requests sono benvenuti!

### Come Contribuire

1. **Fork** il repository
2. **Crea** un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** le modifiche (`git commit -m 'Add AmazingFeature'`)
4. **Push** al branch (`git push origin feature/AmazingFeature`)
5. **Apri** una Pull Request

### Linee Guida

- Seguire PEP 8 per codice Python
- Aggiungere docstrings a funzioni/classi
- Testare modifiche prima di PR
- Documentare nuove features

### Bug Report

Aprire issue includendo:

- Descrizione problema
- Steps per riprodurre
- Output errore/log
- Sistema operativo e versione Python

---

## Licenza

Distribuito sotto licenza MIT. Vedi [LICENSE](./LICENSE) per maggiori informazioni.

---

## Documentazione

- [Analisi di progetto](docs/project_analysis.md)
- [Design progetto](docs/project_design.md)
- [Implementazione](docs/implementation.md)
- [Manuale utente](docs/user_manual.md)
- [Collaudo e report](docs/test.md)
- [Guida installazione](docs/startup_instructions.md)


## Autori

**Manuel Sannicolò**

- Email: manuel.sannicolo07@marconirovereto.it
- GitLab: [@manuel.sannicolo07](https://gitlab.com/manuel.sannicolo07)
- Istituto: Marconi Rovereto

**Isabel Zoner**

- Email: isabel.zoner07@marconirovereto.it
- Istituto: Marconi Rovereto

---

## Ringraziamenti

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8
- [Alex Bewley](https://github.com/abewley/sort) - SORT Tracker
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Fast Plate OCR](https://github.com/ankandrew/fast-plate-ocr)
- [Flask](https://flask.palletsprojects.com/)

---

<div align="center">

**Progetto di autonomia informatica a.s. 2025-26 1Q**

Made by Manuel Sannicolò, Isabel Zoner

</div>

---

**Versione Manuale:** 1.0  
 **Ultimo Aggiornamento:** Gennaio 2026  
 **Sistema:** Gestione Accessi Veicolari v1.0