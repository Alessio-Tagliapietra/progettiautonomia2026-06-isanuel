# Istruzioni di Messa in Esercizio

La seguente procedura descrive come installare ed avviare il sistema in un ambiente di produzione simulato (localhost).

---

## Indice

1. [Requisiti](#1-requisiti)  
1. [Installazione](#2-installazione)  
2. [Configurazione](#3-configurazione)  
3. [Avvio del Sistema](#4-avvio-del-sistema)  
4. [Utilizzo Interfaccia Web](#5-utilizzo-interfaccia-web)  
5. [Modalità Operative](#6-modalità-operative)  
6. [Troubleshooting](#7-troubleshooting)

---

## 1\. Requisiti 

### 1.1 Requisiti Hardware

* **CPU**: Processore multi-core (≥ 4 core consigliato)  
* **RAM**: ≥ 8 GB  
* **GPU**: NVIDIA GPU con supporto CUDA (opzionale ma fortemente consigliata per prestazioni ottimali)  
* **Storage**: ≥ 5 GB spazio libero

### 1.2 Requisiti Software

* **Sistema Operativo**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+  
* **Python**: ≥ 3.10 (consigliato Python 3.11)  
* **CUDA Toolkit**: 11.8+ (se si utilizza GPU NVIDIA)  
* **Tesseract OCR**: 5.0+ (opzionale, per OCR con Tesseract)  
* **Fast Plate OCR:** 1.0.2+   
* **Browser Web**: Chrome, Firefox, Edge, Safari (per interfaccia web)

### 1.3 Connessione di Rete

* **Internet**: Necessaria per autenticazione OAuth Google  
* **Locale**: Necessaria per comunicazione client-server (modalità distribuita)

---

## 2\. Installazione 

Per configurare l'ambiente di sviluppo, seguire questi passaggi:

### 2.1 Clonazione Repository

Clonare il repository dal link: https://gitlab.com/manuel.sannicolo07/plate\_detection.git

*`git clone https://gitlab.com/manuel.sannicolo07/plate_detection.git`*  
*`cd plate_detection`*

### 2.2 Ambiente Virtuale Python

Creare e attivare un ambiente virtuale per isolare le dipendenze

`windows:`  
*`python -m venv venv`*  
*`venv\Scripts\activate`*

`linux/macOS:`  
*`python3 -m venv venv`*  
*`source venv/bin/activate`*

### 2.3 Installazione dipendenze

Installare tutte le dipendenze tramite il comando: 

*`pip install --upgrade pip`*  
*`pip install -r requirements.txt`*

### 2.4 Installazione Tesseract OCR *(Opzionale ma consigliata)*

1. Scaricare l'installer da: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)  
2. Installare in *`C:\Program Files\Tesseract-OCR\`*  
3. Il percorso è già configurato in *`server/config.py`* come:

*`TESSERACT_CMD_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`*

### 2.5 Download Modelli Yolo

I modelli YOLO dovrebbero essere già presenti nella cartella *`models/yolo/`*. Se mancanti:

* **yolov8n.pt**: Download automatico al primo avvio (modello Ultralytics ufficiale)  
* **license\_plate\_detector.pt**: Modello custom per targhe (deve essere fornito)

---

## 3\. Configurazione 

Il file *`server/config.py`* rappresenta il file di configurazione principale che contiene i parametri operativi del sistema di processing

### 3.1 Configurazioni essenziali

3.1.1 Modalità Sorgente Frame

Scegliere come il sistema riceve i frame da elaborare:

| Modalità | Funzionamento |
| :---: | :---: |
| *`FRAME_SOURCE = "local"`* | Modalità **LOCAL**: usa webcam o file video locale |
| *`FRAME_SOURCE = "non-local"`* |  Modalità **NON-LOCAL**: riceve frame via HTTP da client esterni |

**Quando usare LOCAL:**

* Test con video registrati  
* Demo con webcam  
* Sistema standalone

**Quando usare NON-LOCAL:**

* Architettura client-server distribuita  
* Camera IP remota  
* Integrazione con sistemi esterni

3.1.2 Sorgente Video   
La sorgente video può essere selezionata attraverso il file *`server/config.py`* nel caso nella sorgente LOCAL, oppure attraverso il file *`client/config.py`* nel caso della sorgente NON-LOCAL.

| Parametro | Funzionamento |
| :---: | :---: |
| *`USE_WEBCAM = True`* | Se **True**, utilizza la webcam del dispositivo; se **False**, utilizza il video indicato nel percorso |
| *`VIDEO_PATH = “percorso/file.mp4”`* | Percorso del video di test da utilizzare in caso di *`USE_WEBCAM  = False`* |

3.1.3 Percorsi Modelli YOLO

| Parametro | Funzionamento |
| :---: | :---: |
| *`COCO_MODEL_PATH = os.path.join(MODELS_DIR, "yolo", "yolov8n.pt")`* | Percorso del modello di **rilevazione dei veicoli**; combina il percorso della cartella dei modelli con il file in questione |
| *`PLATE_MODEL_PATH = os.path.join(MODELS_DIR, "yolo", "license_plate_detector.pt")`* | Percorso del modello di **rilevazione delle targhe**; combina il percorso della cartella dei modelli con il file in questione |

**Note:**

* *`yolov8n.pt`*: modello nano (veloce, meno preciso)  
* Altre varianti: *`yolov8s.pt`* (small), *`yolov8m.pt`* (medium), *`yolov8l.pt`* (large)  
* Maggiore dimensione \= maggiore precisione ma più lento

### 3.2 Configurazioni di Personalizzazione

3.2.1 Dispositivo di Elaborazione

| Parametro | Funzionamento |
| :---: | :---: |
| *`DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'`* | Impostato in automatico per utilizzare la GPU se presente; altrimenti utilizza la CPU |

3.2.2 Configuration di Detection

#### **Classi COCO da Rilevare**

| Parametro | Funzionamento |
| :---: | :---: |
| *`CLASSES_TO_DETECT = [1, 2, 3, 5, 7]`* | Elenco totale degli oggetti da rilevare (primo modello di ML) |
| *`VEHICLES_4_WHEELS = [2, 5, 7]`* | Elenco totale dei veicoli di cui bisogna controllare la targa |
| *`VEHICLES_2_WHEELS = [1, 3]`* | Elenco totale dei veicoli autorizzati di principio |

L’elenco totale degli oggetti rilevabili dal modello è visibile al seguente link: [Dataset COCO](https://docs.ultralytics.com/it/datasets/detect/coco/#applications)

#### **Soglie di Confidenza**

| Parametro | Funzionamento |
| :---: | :---: |
| *`DETECTION_CONFIDENCE = 0.2`* | Confidenza minima del modello di rilevazione/classificazione del veicolo per accettare il risultato |
| *`PLATE_DETECTION_CONFIDENCE = 0.2`* | Confidenza minima del modello di rilevazione della targa per accettare il risultato |
| *`OCR_MIN_CONFIDENCE = 0.2`* | Confidenza minima del modello di lettura della targa per accettare il risultato |

**Raccomandazioni:**

* Valori bassi (0.2-0.4): più detection, più falsi positivi  
* Valori alti (0.6-0.8): meno detection, più accurato  
* Per ambienti controllati: alzare le soglie a 0.5+  
* Per massima copertura: mantenere 0.2-0.3

3.2.3 Configurazione OCR

| Parametro | Funzionamento |
| :---: | :---: |
| *`TESSERACT_AVAILABLE = True`* | Auto-rilevato in fase di inizializzazione: abilitazione del modello Tesseract |
| *`FAST_OCR_AVAILABLE = False`* | Auto-rilevato in fase di inizializzazione: abilitazione del modello Fast Plate OCR |
| *`USE_FAST_OCR = True`* | Utilizzo di Fast Plate OCR come modello primario (consigliato) |
| *`TESSERACT_CMD_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`*  | In caso di problemi, permette di indicare il percorso eseguibile di Tesseract |

3.2.4 Configurazione Database e sistema di Fallback

| Parametro | Funzionamento |
| :---: | :---: |
| *`DATABASE_PATH = os.path.join(DATA_DIR, "authorized_plates.db")`* | Percorso del Database SQLite principale |
| *`TXT_PATH = os.path.join(DATA_DIR, "authorized_plates.txt")`* | Percorso dell’elenco delle targhe per fallback di primo livello |
| *`FALLBACK_AUTHORIZED_PLATES =  [...]`* | Elenco delle targhe autorizzate per fallback di secondo livello |

**Note:**

* Il database viene creato automaticamente al primo avvio  
* Le targhe fallback sono usate solo in caso di errore database  
* Formato targhe italiano: AA000AA (2 lettere, 3 numeri, 2 lettere)

3.2.5 Configurazioni Preprocessing Immagini

| Parametro | Funzionamento |
| :---: | :---: |
| *`TARGET_HEIGHT = 120`* | Consente di migliorare la qualità dell’OCR impostando la dimensione target della targa |
| *`VEHICLE_CROP_MARGIN = 10`* | Margine per effettuare i crop: modificare in caso di tagli sbagliati |

3.2.6 Configurazioni Visualizzazione

| Parametro | Funzionamento |
| :---: | :---: |
| *`SHOW_VIDEO = False`* | Mostra finestra video in tempo reale dei frame analizzati: consigliata solo per debug (alta complessità computazionale) |
| *`DISPLAY_WIDTH = 1280  DISPLAY_HEIGHT = 720`* | Dimensioni dello schermo in caso di  *`SHOW_VIDEO = True`* |
| *`BOX_THICKNESS = 2`* | Spessore della linea di bounding box |
| *`FONT_SCALE = 0.8`* | Dimensioni Font Label |
| *`COLORS = {...}`* | Colori della bounding box sulla base del label del veicolo (autorizzato o meno) |

3.2.7 Configurazioni Debug e Logging

| Parametro | Funzionamento |
| :---: | :---: |
| *`VERBOSE = True`* | Stampa i Log dettagliati in console |
| *`SAVE_VEHICLE_IMAGES = False SAVE_PLATE_IMAGES = False  SAVE_DEBUG_PLATES = False`* | Permette di salvare i frame pre e post processo: veicolo croppato, targa croppata, targa post preprocessing |
| *`PLATE_IMAGES_DIR = os.path.join(IMAGE_RESULTS_DIR, "detected_plates") PLATE_IMAGES_DIR_DEBUG = os.path.join(IMAGE_RESULTS_DIR, "debug_plates") VEHICLE_IMAGES_DIR = os.path.join(IMAGE_RESULTS_DIR, "detected_vehicles")`* | Indica il percorso di dove memorizzare le immagini di debug se abilitate |

3.2.8 Configurazioni Autenticazione OAuth

| Parametro | Funzionamento |
| :---: | ----- |
| *`SECRET_KEY = “...”`* | Chiave segreta Flask: generarne una casuale per produzione |
| *`GOOGLE_CLIENT_ID  GOOGLE_CLIENT_SECRET`*  | Credenziali per Google OAuth |
| *`AUTHORIZED_USERS = [...]`* | Elenco delle e-mail degli utenti autorizzati ad accedere all’interfaccia web  |

**Per utilizzare l'autenticazione, configurare le credenziali OAuth:**

* Accedere a Google Cloud Console: [`https://console.cloud.google.com`](https://console.cloud.google.com)  
* Creare un nuovo progetto o selezionare uno esistente  
* Abilitare Google+ API  
* Credenziali → Crea credenziali → ID client OAuth 2.0  
* Tipo di applicazione: Applicazione web  
* URI di reindirizzamento autorizzati: *`http://localhost:5000/callback`*  
* Copiare Client ID e Client Secret nel file *`config.py`*
* creare un file *`.env`* e incollare i dati come nell’esempio presente nel file *`.env.example`*

3.2.9 Configurazioni Autenticazione Camera (Client-Server)

Da modificare per la modalità **NON-LOCAL:**

| Parametro | Funzionamento |
| :---: | :---: |
| *`REQUIRE_CAMERA_AUTH = True`* | Richiedi autenticazione da parte del client per frame upload |
| *`AUTHORIZED_CAMERAS =  {“id”: “key” }`* | Dizionario delle camere autorizzate |

### 3.3 Validazione della configurazione

Al termine di ogni modifica, **verificare la configurazione**:

*`python server/config.py`*

sistema eseguirà controlli e segnalerà eventuali errori:

* File modelli esistenti  
* Percorsi video validi  
* Soglie nei range corretti  
* Database accessibile

## 4\. Avvio del Sistema 

### 4.1 Avvio Completo

Dalla directory principale del progetto:

*`python -m run`*

oppure:

*`python run.py`*

In caso di utilizzo della modalità NON-LOCAL visualizzare la sezione dedicata.

### 4.2 Sequenza di Avvio

Il sistema eseguirà le seguenti operazioni:

| 🚀 Avvio sistema di elaborazione 🔧 Inizializzazione OCR...    ✅ Tesseract disponibile    ✅ LPR disponibile ✅ Visualizzazione caricata ✅ DatabaseManager inizializzato 🌐 Avvio server web    \* Running on http://127.0.0.1:5000 📋 Targhe autorizzate: X 🚀 Inizializzazione sistema...    Device: cuda    Frame source: local    Loading YOLO veicoli...    Loading YOLO targhe...    Inizializzazione SORT tracker... 🎬 Inizio elaborazione...  |
| :---- |

### 4.3 Arresto del sistema

Il sistema è arrestabile tramite i comandi ***`CTRL + C`** `.`*

Il sistema chiude correttamente:

* Database  
* Thread di elaborazione  
* Visualizzazione video

## 5\. Utilizzo Interfaccia Web 

### 5.1 Autenticazione

1. ### Accedere a `http://localhost:5000`

2. ### Cliccare su **"Accedi con Google"**

3. ### Selezionare account Google autorizzato

4. ### Autorizzare l'applicazione

### 5.2 Gestione Targhe

5.2.1 Visualizzazione Targhe

* ### Menu: **Targhe** → **Elenco Targhe**

* ### Visualizza tutte le targhe autorizzate con:

  * ### *Numero targa*

  * ### *Proprietario* (nome e cognome)

  * ### *Ruolo*

  * ### *Data scadenza*

  * ### *Azioni* (Modifica, Elimina)

5.2.1 Aggiungere Targa

1. ### Menu: **Targhe** → **Aggiungi Targa**

2. ### Compilare form:

   * ### **Numero Targa**: es. *AB123CD* (formato italiano)

   * ### **Nome**: Nome proprietario

   * ### **Cognome**: Cognome proprietario

   * ### **Ruolo**: *Docente*, *Studente*, *Personale ATA*, *Visitatore*, ecc.

   * ### **Data Scadenza**: Formato *YYYY-MM-DD*

3. ### Cliccare **"Aggiungi Targa"**

5.2.3 Modificare Targa

1. ### Dalla lista targhe, cliccare **"Modifica"**

2. ### Aggiornare campi desiderati

3. ### Salvare modifiche

5.2.3 Eliminare Targa

1. ### Dalla lista targhe, cliccare **"Elimina"**

2. ### Confermare l'operazione

### 5.3 Visualizzazione Log

5.3.1 Accedere ai Log

* ### Menu: **Log** → **Storico Accessi**

5.3.2 Filtri Disponibili

* ### **Per targa**: Cerca targa specifica

* ### **Per stato**: Filtra authorized / not\_authorized / expired

5.3.3 Esportazione Log

1. ### Cliccare **"Esporta CSV"**

2. ### Scaricare file *access\_logs\_YYYYMMDD\_HHMMSS.csv*

5.3.4 Cancellazione Log

1. ### Cliccare **"Cancella Tutti i Log"**

2. ### Confermare (operazione irreversibile)

## 6\. Modalità Operative 

### 6.1 Modalità LOCAL (Standalone)

**Configurazione:**

| FRAME\_SOURCE \= "local" USE\_WEBCAM \= False VIDEO\_PATH \= "/path/to/video.mp4" |
| :---- |

**Utilizzo:**

* Sistema standalone completo  
* Elabora video pre-registrati o webcam  
* Nessuna comunicazione di rete richiesta

**Avvio:**

*`python run.py`*

### 6.2 Modalità NON-LOCAL (Distribuita)

**Architettura:**

| \[CLIENT \- Camera/Sensore\]           \----- HTTP \---→        \[SERVER \- Elaborazione \+ Web\] |
| :---: |

**Configurazione Server:**

| FRAME\_SOURCE \= "non-local" REQUIRE\_CAMERA\_AUTH \= True AUTHORIZED\_CAMERAS \= {“id”: “key” } |
| :---- |

**Configurazione Client:**

| SERVER\_URL \= "http://localhost:5000/api/upload" headers \= {     "camera-id":  "id",     "API-Key":  "key" } |
| :---- |

**Avvio Server:**

*`python run.py`*

**Avvio Client (terminale separato):**

*`cd client`*

*`python sender.py`*

**Utilizzo:**

* Il server offre un end-point per l’upload dei frame  
* il client invia i frame contenti veicoli identificandosi   
* Il server elabora i frame

### 6.3 Modalità Debug Visivo

**Abilitare visualizzazione:**

| SHOW\_VIDEO \= True VERBOSE \= True SAVE\_DEBUG\_PLATES \= True |
| :---- |

**Controlli tastiera (finestra video):**

* **Q**: Termina elaborazione  
* **ESC**: Termina elaborazione

## 7\. Troubleshooting 

### 7.1 Errori comuni

7.1.1 Errore: Modelli YOLO non trovati

| ❌ Modello COCO non trovato: .../yolov8n.pt |
| :---- |

**Soluzione:**

* Verificare percorsi in config.py  
* Scaricare modelli mancanti nella cartella models/yolo/

7.1.2 Errore: Tesseract non trovato

| ❌ Tesseract non disponibile |
| :---- |

**Soluzione:**

* Installare da: *https://github.com/UB-Mannheim/tesseract/wiki*  
* Verificare percorso in *`server/config.py`*:

|   TESSERACT\_CMD\_PATH \= r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe" |
| :---- |

7.1.3 Errore: CUDA not available

| Device: cpu (CUDA non disponibile) |
| :---- |

**Soluzione:**

* Verificare installazione driver NVIDIA  
* Installare CUDA Toolkit: [*https://developer.nvidia.com/cuda-downloads*](https://developer.nvidia.com/cuda-downloads)  
* Reinstallare PyTorch con supporto CUDA:

|  *pip install torch torchvision \--index-url https://download.pytorch.org/whl/cu118* |
| :---- |

7.1.4 Errore: OAuth Google \- redirect\_uri\_mismatch

**Soluzione:**

* Google Cloud Console → Credenziali  
* Modificare ID client OAuth  
* URI di reindirizzamento autorizzati: aggiungere *http://localhost:5000/callback*  
* Salvare

7.1.5 Errore: Database locked

**Soluzione:**

* Chiudere altre istanze dell'applicazione  
* Verificare permessi file database  
* In caso persistente, cancellare *`authorized_plates.db`* (verrà ricreato)

### 7.2 Performance e Ottimizzazione

7.2.1 Sistema Lento

**Soluzioni:**

* Usare GPU (CUDA) invece di CPU  
* Ridurre risoluzione video  
* Aumentare soglie di confidenza  
* Usare modello *YOLO* più leggero (yolov8n.pt)  
* Disabilitare *SHOW\_VIDEO*

7.2.2 Troppe False Detection

**Soluzione:**

* Aumentare le soglie di confidenza:

| *DETECTION\_CONFIDENCE \= 0.5  \# Aumentare da 0.2 PLATE\_DETECTION\_CONFIDENCE \= 0.5 OCR\_MIN\_CONFIDENCE \= 0.6  \# Aumentare da 0.2 TRACKER\_MIN\_HITS \= 5  \# Aumentare da 3* |
| :---- |

7.2.3 OCR Non Legge Targhe

**Soluzione:**

* verifica tramite modalità di debug la corretta inizializzazione dei modelli  
* abilita il debug per il salvataggio dei frame e analizza le immagini salvate  
* modifica il *TARGET\_HEIGHT* in *`server/config.py`* per facilitare la lettura 

7.2.4 Ripristino Sistema

#### **Reset Completo Database:**

*`# Backup (opzionale)`*

*`cp server/data/authorized_plates.db server/data/authorized_plates.db.backup`*

*`# Cancellare database`*

*`rm server/data/authorized_plates.db`*

*`# Riavviare sistema (verrà ricreato)`*

*`python run.py`*

#### **Reset dei Log:**

* Interfaccia Web → Log → "Cancella Tutti i Log"

7.2.5 Supporto

Per problemi non risolti:

* Verificare log console completi  
* Controllare configurazione con python server/config.py  
* Abilitare debug: 

| *VERBOSE \= True SAVE\_VEHICLE\_IMAGES \= True SAVE\_PLATE\_IMAGES \= True SAVE\_DEBUG\_PLATES \= True* |
| :---- |
