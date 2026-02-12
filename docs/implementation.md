# Implementazione di Progetto

---

## Indice

1. [Ambiente di Sviluppo](#1-ambiente-di-sviluppo)  
2. [Struttura del Codice](#2-struttura-del-codice)  
3. [Decisioni di Design](#3-decisioni-di-design)  
4. [Gestione delle Versioni](#4-gestione-delle-versioni)  
5. [Esempi di Codice](#5-esempi-di-codice)

---

## 1\. Ambiente di sviluppo 

#### 1.1 Requisiti di Sistema

Il progetto richiede **Python 3.10 o superiore** per garantire la compatibilità con tutte le librerie utilizzate. In particolare è consigliato l’utilizzo di Python 3.11 per garantire la massima compatibilità ed efficienza dei vari moduli applicativi.  
 L'applicazione è stata sviluppata e testata su sistemi Windows, ma può essere eseguita anche su Linux e macOS con le opportune modifiche ai percorsi dei file.

#### 1.2 Dipendenze Python

Le librerie necessarie per l'esecuzione del progetto sono elencate nel file *`requirements.txt`* e includono i seguenti componenti principali:

**Framework e librerie per il machine learning:**

* ultralytics: fornisce i modelli YOLO per la detection di veicoli e targhe  
* torch: backend per l'esecuzione dei modelli di deep learning  
* fast-plate-ocr: libreria specializzata per il riconoscimento ottico delle targhe

**Elaborazione immagini e computer vision:**

* opencv-python: gestisce l'elaborazione dei frame video e le operazioni di preprocessing delle immagini  
* numpy: supporta le operazioni matematiche e la manipolazione degli array per l'elaborazione delle immagini  
* pytesseract: fornisce un'alternativa per l'OCR tramite il motore Tesseract

**Framework web e database:**

* Flask: gestisce l'interfaccia web e gli endpoint API per la comunicazione tra client e server  
* flask-login: implementa il sistema di autenticazione degli utenti  
* authlib: gestisce l'autenticazione OAuth2 con Google  
* sqlite3: fornisce il database per la gestione delle targhe autorizzate e dei log di accesso

**Tracking e comunicazione:**

* sort-tracker: implementa l'algoritmo SORT per il tracking degli oggetti rilevati  
* requests: gestisce le comunicazioni HTTP tra il client e il server  
* sseclient: supporta gli eventi Server-Sent Events per gli aggiornamenti in tempo reale

### 1.3 Modelli pre-addestrati

Il sistema utilizza tre modelli YOLO pre-addestrati, posizionati nella directory *`models/yolo/`*:

| Modello | Dimensione | Funzione |
| ----- | ----- | ----- |
| *`yolov8n.pt`* | \~6 MB | Detection veicoli e persone (COCO dataset) |
| *`license_plate_detector.pt`* | \~6 MB | Modello personalizzato per la localizzazione targhe nei veicoli |

### 

#### 1.4 Installazione

Per configurare l'ambiente di sviluppo, seguire questi passaggi:

1. Clonare il repository dal link: https://gitlab.com/manuel.sannicolo07/plate\_detection.git

*`git clone https://gitlab.com/manuel.sannicolo07/plate_detection.git`*  
*`cd plate_detection`*

2. Creare un ambiente virtuale Python per isolare le dipendenze del progetto. Attivare l'ambiente virtuale.

*`python -m venv venv`*  
*`#per Linux / MacOS:`*  
*`source venv/bin/activate`*  
*`#per Windows:`*  
*`venv\Scripts\activate`*

3. installare tutte le dipendenze tramite il comando: 

*`pip install -r requirements.txt`*

4. Per l'utilizzo completo dell'OCR con Tesseract, è necessario installare separatamente il software Tesseract OCR e configurare il percorso dell'eseguibile nel file *`config.py`*.

#### 1.5 Database SQLite

Il database viene inizializzato automaticamente all'avvio del sistema nella directory *`server/data/`*:

*`server/data/`*  
*`├── authorized_plates.db    # Database principale`*  
*`├── authorized_plates.txt   # Backup targhe (fallback)`*  
*`└── detected_plates.csv     # Log CSV delle detection`*

**Schema Database:** come documentato nel Documento 2 (Progettazione), sezione 2.1

---

## 2\. Struttura del codice 

Il progetto è organizzato secondo un'architettura modulare che separa chiaramente le responsabilità tra componenti client e server.

#### 2.1 Architettura della Directory

L’architettura della directory può essere visualizzata direttamente dal file [README](../README.md).

#### 2.2 Modulo **Client**

Il modulo client rappresenta l'unità di acquisizione video che può essere implementata su dispositivi edge come telecamere intelligenti o computer embedded. Il file *`client.py`* gestisce l'invio dei frame al server tramite richieste HTTP POST. Prima dell'invio, il client esegue una detection preliminare dei veicoli utilizzando il modello YOLO configurato in *`detection.py`*, riducendo così il carico di elaborazione sul server inviando solo i frame che contengono effettivamente veicoli. Il file *`config.py`* del client contiene i parametri di configurazione specifici per l'acquisizione video e la comunicazione con il server.

#### 2.3 Modulo **Server**

Il modulo server implementa l'intero sistema di elaborazione e gestione delle autorizzazioni.

2.3.1 Sottosistema **Connection**

Il file *`frame_receiver.py`* implementa gli endpoint Flask per ricevere i frame dal client tramite HTTP POST. Gestisce l'autenticazione delle telecamere tramite API key e inserisce i frame ricevuti in una coda per l'elaborazione asincrona. Implementa anche endpoint per il controllo dello stato del servizio tramite Server-Sent Events.

2.3.2 Sottosistema **Control**

 Il modulo *`context.py`* implementa un sistema di gestione del contesto globale che permette ai vari moduli di condividere risorse come modelli di machine learning, database manager e tracker senza creare dipendenze circolari. Il file *`frame_queue.py`* gestisce la coda thread-safe per la gestione dei frame in ingresso, permettendo di disaccoppiare la ricezione dall'elaborazione.

2.3.3 Sottosistema **Process**

 Questo è il cuore del sistema di elaborazione. Il file *`detection.py`* gestisce il tracking degli oggetti rilevati utilizzando l'algoritmo SORT e la detection delle targhe all'interno dei veicoli identificati. Il modulo *`ocr_utils.py`* implementa l'intera pipeline di preprocessing delle immagini delle targhe e la lettura OCR, con supporto sia per Fast Plate OCR che per Tesseract. Include algoritmi di correzione prospettica per targhe angolate, equalizzazione dell'istogramma e sharpening. Il file *`plate_utils.py`* gestisce la verifica delle autorizzazioni consultando il database e implementa il logging degli accessi. Il modulo *`vehicle_utils.py`* coordina l'elaborazione completa di ogni veicolo rilevato, dalla detection alla verifica finale. Infine, *`visualize.py`* gestisce il rendering dei bounding box e delle informazioni sui frame video (utilizzato per debug).

2.3.4 Sottosistema **Web**

L'applicazione Flask in *`appWeb.py`* fornisce l'interfaccia web per la gestione del sistema. Implementa l'autenticazione OAuth2 con Google per garantire l'accesso solo agli utenti autorizzati. Fornisce pagine per la visualizzazione e modifica delle targhe autorizzate, consultazione dei log di accesso, e controllo dello stato del servizio. I template HTML nella directory *`templates`* utilizzano Bootstrap per un'interfaccia responsive e professionale.

2.3.5 **Database** e **Configurazione**

 Il file *`database.py`* implementa il DatabaseManager che gestisce tutte le operazioni sul database SQLite, incluse le operazioni CRUD sulle targhe autorizzate e il logging degli accessi. Il file *`config.py`* centralizza tutti i parametri configurabili del sistema, dai percorsi dei modelli alle soglie di confidenza, dalle credenziali OAuth alle impostazioni di visualizzazione.

#### 2.4 File principale per l’esecuzione

### 

Il file *`run.py`* funge da entry point dell'applicazione server, orchestrando l'inizializzazione di tutti i componenti e l'avvio del thread di elaborazione e del server web Flask.

#### 2.5 Recap suddivisione funzioni

#### 2.5.1 Lato client

| Modulo | File | Funzione |
| :---: | :---: | :---: |
| Processing Client | sender.py | Acquisisce frame (webcam /video), lo invia al server (POST) dopo la detection |
|  | detection.py | Inizializza YOLO, classifica veicoli e filtra in base a classi e confidence |
|  | config.py | Configurazione client: path, soglie, modalità verbose … |

#### 2.5.2 Lato Server

| Modulo | File | Funzione |
| :---: | :---: | :---: |
| Connection | frame\_receiver.py | Riceve frame HTTP e li mette in queue |
| Control | context.py | Dizionario globale condiviso (memorizza OCR, database, modelli YOLO..) |
|  | frame\_queue.py | Queue thread-safe (max 100 frame) per evitare perdita di frame dal server |
| Process | detection.py | Detection targhe YOLO, crop, dimensioni targa |
|  | ocr\_utils.py | Lettura targhe: OCR multiplo \+ correzione caratteri formato IT |
|  | plate\_utils.py | Verifica autorizzazioni targa, logging accessi |
|  | vehicle\_utils.py | Processing completo veicolo |
|  | visualize.py | Rendering video con bounding box |
| Web | appWeb.py | Server Flask, OAuth 2.0, CRUD targhe |
|  | user.py | Modello utente per Flask-login, autenticazione |
| Main | config.py | Tutte le configurazioni di sistema |
|  | database.py | classe DatabaseManager, SQLite per targhe e log |
|  | main.py | Inizializza tutti i valori e gestisce il thread principale |

---

## 3\. Decisioni di Design 

#### 3.1 Sistema di Fallback per Targhe Autorizzate

Per garantire la continuità operativa del sistema anche in presenza di guasti o indisponibilità parziali delle componenti software, è stato progettato e implementato un **sistema di fallback multilivello** per la gestione delle targhe autorizzate.

Il sistema prevede una gerarchia di fonti di dati, interrogate in ordine di priorità. In condizioni normali, le targhe autorizzate vengono caricate dal **database principale**, che rappresenta la fonte primaria e più aggiornata delle informazioni. Tuttavia, nel caso in cui il database non sia raggiungibile, risulti corrotto o non contenga alcuna targa valida, il sistema non interrompe il proprio funzionamento, ma attiva automaticamente un meccanismo di recupero.

Il primo livello di fallback consiste nella lettura di un **file di testo esterno** (*`authorized_plates`*`.txt`), memorizzato all’interno della struttura del progetto. Questo file consente di mantenere un elenco minimo di targhe autorizzate indipendente dal database e facilmente modificabile senza richiedere l’accesso all’interfaccia web o la riconfigurazione del sistema.

Qualora anche il file di testo non fosse disponibile o risultasse vuoto, il sistema ricorre infine a un insieme di **targhe di emergenza hardcoded** (*`FALLBACK_AUTHORIZED_PLATES`*), definite direttamente nel codice sorgente. Questo ultimo livello rappresenta una misura di sicurezza estrema, pensata per evitare il blocco totale del sistema in scenari critici.

L’intero meccanismo è stato progettato secondo il principio del **fail-safe**, privilegiando la disponibilità del servizio e assicurando che il sistema non operi mai in uno stato non deterministico. Ogni fase del processo di caricamento è accompagnata da messaggi di log esplicativi, facilitando le operazioni di diagnostica e manutenzione. Questo approccio garantisce un’elevata robustezza complessiva e rende il sistema resiliente a errori infrastrutturali o di configurazione.

#### 3.2 Sistema di Correzione OCR con Dizionari Contestuali

Una delle decisioni implementative più significative riguarda il sistema di correzione dei risultati OCR tramite i dizionari *`INT_POS_CORRECTION`* e *`CHAR_POS_CORRECTION`* definiti in *`ocr_utils.py`*. Questa scelta è stata motivata dalla necessità di migliorare drasticamente l'accuratezza del riconoscimento delle targhe italiane, che seguono il formato standardizzato AA000AA.

Il sistema OCR, anche con modelli specializzati, tende a confondere caratteri visivamente simili quando le condizioni di illuminazione non sono ottimali o quando le targhe sono sporche o angolate. Il dizionario *`INT_POS_CORRECTION`* corregge gli errori nelle posizioni numeriche della targa, dove lettere come O, I, Q e U vengono frequentemente rilevate al posto dei numeri 0, 1 e altri. Analogamente, *`CHAR_POS_CORRECTION`* gestisce le correzioni nelle posizioni alfabetiche, dove numeri possono essere erroneamente riconosciuti come lettere.

La peculiarità delle targhe italiane, che escludono specifiche lettere (O, I, Q, U) per evitare ambiguità, rende questa correzione particolarmente efficace. Il sistema applica queste correzioni in modo contestuale basandosi sulla posizione del carattere nella stringa, garantendo che ogni carattere sia validato secondo le regole del formato atteso. Questo approccio ha dimostrato di aumentare significativamente il tasso di riconoscimento corretto, riducendo i falsi negativi che potrebbero portare al rifiuto di veicoli autorizzati.

#### 3.3 Strategia Multi-OCR con Fallback

La decisione di implementare un sistema di doppio OCR rappresenta un elemento cruciale per garantire la robustezza del sistema in diverse condizioni operative. Il modulo *`ocr_utils.py`* implementa la funzione *`read_plate_multiple_methods`* che orchestra questa strategia.

Il sistema tenta prima la lettura tramite Fast Plate OCR, un modello di deep learning specializzato per il riconoscimento delle targhe che offre prestazioni superiori in condizioni ideali. Se questo primo tentativo produce un risultato con confidenza elevata e formato valido, il sistema lo accetta immediatamente, ottimizzando i tempi di elaborazione.

Tuttavia, quando Fast Plate OCR non è disponibile, fallisce completamente, o produce risultati con bassa confidenza, il sistema attiva automaticamente il fallback su Tesseract OCR. Tesseract, pur essendo generalmente meno accurato per le targhe, può produrre risultati migliori in specifiche condizioni, come targhe molto sporche o con riflessi particolari, dove i pattern appresi da Fast Plate OCR potrebbero non essere efficaci.

La strategia prevede anche un meccanismo di confronto quando entrambi i metodi producono risultati validi. Se i due OCR concordano sul testo rilevato, il sistema aumenta automaticamente la confidenza del risultato finale, fornendo una validazione incrociata che riduce ulteriormente la probabilità di errore. Questa implementazione bilancia efficacemente accuratezza e resilienza, garantendo che il sistema possa operare anche quando uno dei due motori OCR non è disponibile o non sta performando in modo ottimale.

#### 3.4 Sistema di Configurazione Centralizzato

La decisione di centralizzare tutte le impostazioni nel file *`config.py`* risponde all'esigenza di rendere il sistema facilmente configurabile e manutenibile senza modificare il codice sorgente. Questo file rappresenta un unico punto di riferimento per tutti i parametri operativi del sistema.

Il file include la configurazione dei percorsi dei modelli e dei file di dati, permettendo un facile adattamento a diverse strutture di directory. Definisce le soglie di confidenza per le detection di veicoli e targhe, i parametri del tracker SORT, e le impostazioni OCR, permettendo un fine-tuning del sistema basato sulle specifiche esigenze operative senza dover navigare attraverso multiple file sorgente.

Particolarmente significativa è la gestione delle credenziali di autenticazione OAuth e delle chiavi API per le telecamere, che sono centralizzate e facilmente modificabili. Il file include anche la configurazione del logging verboso e delle directory di output per il debug, facilitando lo sviluppo e la risoluzione dei problemi.

Un aspetto cruciale è la definizione della lista *`FALLBACK_AUTHORIZED_PLATES`* e della funzione *`load_authorized_plates().`* Questa implementazione garantisce la resilienza del sistema anche in caso di indisponibilità del database. Se il database SQLite non è accessibile o è corrotto, il sistema utilizza automaticamente la lista di targhe di fallback definita nella configurazione, permettendo al sistema di continuare a operare in modalità degradata piuttosto che fallire completamente. Questa scelta progettuale è fondamentale per sistemi critici dove la disponibilità è prioritaria rispetto alla completezza delle funzionalità.

#### 3.5 Architettura Client-Server con Processing Distribuito

La scelta di implementare un'architettura client-server con detection preliminare lato client rappresenta un'ottimizzazione significativa per scenari di deployment reale. Questa decisione permette di ridurre drasticamente il traffico di rete e il carico computazionale sul server centrale, consentendo la gestione di multiple telecamere simultaneamente. Il client esegue una detection leggera dei veicoli prima di inviare i frame, trasmettendo al server solo le immagini che contengono effettivamente veicoli da analizzare. Questa architettura è particolarmente vantaggiosa in installazioni con larghezza di banda limitata o con un elevato numero di telecamere distribuite geograficamente.

---

## 4\. Gestione delle Versioni 

Il progetto utilizza Git come sistema di controllo versione per tracciare tutte le modifiche al codice sorgente e facilitare la collaborazione tra i membri del team.

**Repository del progetto:** *`https://gitlab.com/manuel.sannicolo07/plate_detection.git`*

Il repository include commit significativi e ben descritti che documentano l'evoluzione del progetto, con contributi evidenti da parte di entrambi i membri del team. La history dei commit mostra chiaramente le fasi di sviluppo, dalle implementazioni iniziali dei moduli core, all'integrazione dell'interfaccia web, fino alle ottimizzazioni finali del sistema OCR.

Ogni commit segue le best practice con messaggi descrittivi che specificano il tipo di modifica, il componente interessato e una breve descrizione dell'implementazione. I branch sono stati utilizzati per lo sviluppo di feature specifiche prima dell'integrazione nel branch principale, garantendo la stabilità del codice in produzione.

---

## 5\. Esempi di Codice 

#### 5.1 Classe DatabaseManager

La classe *`DatabaseManager`* gestisce tutte le operazioni sul database SQLite per le targhe autorizzate. Il metodo principale verifica se una targa è autorizzata controllando anche la data di scadenza.

| def is\_plate\_authorized(self, plate\_number: str) \-\> Tuple\[bool, Optional\[Dict\]\]:     """Verifica se una targa è autorizzata e non scaduta"""     try:         plate\_number \= plate\_number.upper().strip()         cursor \= self.connection.cursor()         cursor.execute("SELECT \* FROM authorized\_plates WHERE plate\_number \= ?",                        (plate\_number,))                  row \= cursor.fetchone()         if not row:             return False, None                  plate\_info \= dict(row)                  \# Verifica scadenza         if expiration\_date \< today:             return False, plate\_info                      return True, plate\_info     except Exception as e:         return False, None  |
| :---- |

Il codice normalizza la targa in maiuscolo, esegue una query sicura usando parametri, e verifica la data di scadenza prima di autorizzare l'accesso.

#### 5.2 Funzione di Preprocessing OCR

La funzione *`preprocess_plate`* migliora la qualità dell'immagine della targa prima dell'OCR applicando trasformazioni adattive basate sulle caratteristiche dell'immagine

| def preprocess\_plate(plate\_img: np.ndarray) \-\> np.ndarray:     """Preprocessa l'immagine della targa per migliorare l'accuratezza OCR"""     gray \= cv2.cvtColor(plate\_img, cv2.COLOR\_BGR2GRAY)          \# Analisi qualità     brightness \= np.mean(gray)     contrast \= gray.std()          \# Equalizzazione per immagini scure     if brightness \< 100:         processed \= cv2.equalizeHist(gray)          \# CLAHE per contrasto basso     if contrast \< 30:         clahe \= cv2.createCLAHE(clipLimit=3.0,                                                     tileGridSize=(8, 8))         processed \= clahe.apply(processed)          \# Denoising e sharpening     denoised \= cv2.fastNlMeansDenoising(processed)     sharpened \= cv2.filter2D(denoised, \-1, kernel)          return cv2.cvtColor(sharpened, cv2.COLOR\_GRAY2RGB) |
| :---- |

Il preprocessing applica equalizzazione dell'istogramma per immagini scure e CLAHE per migliorare il contrasto, seguito da denoising e sharpening per rendere i caratteri più leggibili.

#### 5.3 Funzione di Detection Targhe nei Veicoli

La funzione *`detect_plates_in_vehicle`* utilizza il modello YOLO specializzato per individuare le targhe all'interno dell'immagine di un veicolo, applicando filtri per validare le detection.

| def detect\_plates\_in\_vehicle(vehicle\_crop: np.ndarray) \-\> list:     """Rileva le targhe all'interno dell'immagine di un veicolo"""     plate\_model \= get\_context("plate\_model")          \# Detection delle targhe     results \= plate\_model(vehicle\_crop,                           conf=config.PLATE\_DETECTION\_CONFIDENCE,                           verbose=False)\[0\]          plates \= \[\]          for box in results.boxes.data.tolist():         x1, y1, x2, y2, score, class\_id \= box         x1, y1, x2, y2 \= int(x1), int(y1), int(x2), int(y2)                  \# Verifica dimensioni minime e aspect ratio         if not is\_valid\_plate\_detection(x1, y1, x2, y2):             continue                  \# Estrai l'immagine della targa         plate\_crop \= vehicle\_crop\[y1:y2, x1:x2\]                  if plate\_crop.size \> 0:             plates.append({                 'image': plate\_crop,                 'coords': (x1, y1, x2, y2),                 'score': score             })          return plates |
| :---- |

La funzione esegue l'inferenza del modello YOLO per targhe sul crop del veicolo e filtra i risultati verificando che le dimensioni e l'aspect ratio siano compatibili con una targa reale. Per ogni detection valida, estrae l'immagine della targa e restituisce una lista di dizionari contenenti l'immagine, le coordinate e lo score di confidenza, permettendo elaborazioni successive sull'OCR.
