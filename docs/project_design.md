# Progettazione del Sistema \- Design

---

## Indice

1. Architettura generale  
2. Modellazione dei dati  
3. Design del software  
4. Scelte tecnologiche  
5. Interfaccia utente (UI/UX)  
6. Piano di sviluppo

---

## 1\. Architettura generale

Il sistema adotta un'architettura a moduli indipendenti che comunicano tramite il protocollo MQTT. Questo approccio sostituisce la precedente struttura client-server e garantisce un maggiore disaccoppiamento tra i componenti, facilitando la manutenzione, il testing e l'estensione futura del sistema.

I singoli moduli sono progettati per essere autonomi: ognuno si iscrive a specifici topic MQTT per ricevere dati in input e pubblica i propri risultati su topic dedicati, che vengono consumati dai moduli successivi nella pipeline di elaborazione.

#### 1.1 Componenti Software principali

L'architettura si compone dei seguenti macro-componenti:

* **Frontend (Interfaccia Web)**: consente all'amministratore di gestire i veicoli autorizzati, visualizzare i log degli accessi, consultare le analytics e gestire gli utenti amministratori tramite browser.  
* **Backend (Server Flask)**: gestisce il routing HTTP, la logica applicativa, l'interazione con i database e l'autenticazione OAuth 2.0.  
* **Moduli di elaborazione (MQTT)**: pipeline di moduli indipendenti per l'acquisizione dei frame, il rilevamento veicoli, il controllo distanza, l'OCR e il controllo accessi, coordinati tramite broker MQTT.  
* **Broker MQTT (Mosquitto)**: componente middleware responsabile dello smistamento dei messaggi tra i moduli del sistema.  
* **Database principale (SQLite)**: conserva le targhe autorizzate e i log degli accessi.  
* **Database utenti amministratori (SQLite)**: database separato per la gestione degli utenti con accesso all'interfaccia web.

### 1.2 Design pattern

Il design pattern adottato è il MVC (Model–View–Controller) in versione web-based:

* **Model**: gestione dei dati e delle operazioni di lettura/scrittura sul database SQLite tramite la classe Database Manager;  
* **View**: interfaccia grafica web implementata con template HTML/CSS renderizzati da Flask;  
* **Controller**: logica di elaborazione, routing delle richieste HTTP e coordinamento tra Model e View.

Per la pipeline di elaborazione, l'architettura segue un pattern Publisher/Subscriber mediato dal broker MQTT, dove ogni modulo è indipendente e comunica esclusivamente tramite messaggi

## 1.3 Flusso di Comunicazione MQTT

I messaggi scambiati tra i moduli tramite MQTT utilizzano il formato JSON come standard per il payload, in modo da garantire una struttura chiara, flessibile e facilmente interpretabile tra i diversi componenti del sistema.

I principali topic MQTT utilizzati nella pipeline di elaborazione sono:

| Topic MQTT | Publisher | Subscriber | Payload |
| :---- | :---- | :---- | :---- |
| camera/frames | Modulo acquisizione | Modulo rilevamento | Frame video acquisito |
| detection/vehicles | Modulo rilevamento | Modulo controllo distanza | Bounding box e classe veicolo |
| detection/nearby | Modulo controllo distanza | Modulo OCR | Veicoli entro soglia distanza |
| ocr/result | Modulo OCR | Modulo controllo accessi | Targa letta in formato testo |
| access/decision | Modulo controllo accessi | Backend Flask / Attuatore | Esito autorizzazione ed evento entrata/uscita |

## 

### 1.4 Componenti Hardware e integrazione Software

Le componenti hardware del sistema sono: la camera di acquisizione, il server per l'elaborazione e la gestione della piattaforma web, e il cancello dell'ingresso.

La camera (una ESP32-CAM o una Raspberry Pi con modulo camera) trasmette il flusso video al server tramite protocollo RTSP, gestito da MediaMTX come server di streaming. Il server riceve i frame, li elabora attraverso la pipeline MQTT e gestisce la piattaforma web tramite Flask.

La comunicazione tra il server e il cancello avviene tramite MQTT: il modulo di controllo accessi pubblica un comando sul topic dedicato che l'attuatore del cancello riceverà. La modalità di gestione fisica del cancello è ancora in fase di valutazione.

---

## 2\. Modellazione dei dati

Il database è stato progettato per mantenere la tracciabilità dei veicoli autorizzati e delle targhe rilevate nel tempo. È implementato in SQLite per garantire leggerezza, portabilità e assenza di dipendenze esterne.

### 2.1 Struttura Database Principale

Il database è composto principalmente da due entità principali:

| Tabella | Campi principali | Descrizione |
| :---- | :---- | :---- |
| **authorized\_plates** | plate\_number (PK), first\_name, last\_name, role, expiration\_date | Contiene l'elenco delle targhe autorizzate ad accedere con informazioni sul proprietario e ruolo (docente, studente, personale) |
| **access\_history** | id (PK), plate\_number (FK), timestamp, status, event | Memorizza ogni rilevamento con data, ora, stato dell'autorizzazione (autorizzato/non\_autorizzato) e tipo di evento (entrata/uscita). |

Il campo event nella tabella access\_history sostituisce e amplia la precedente struttura: il valore può essere 'entrata' o 'uscita', consentendo di tracciare il ciclo completo di ogni transito del veicolo.

### 2.2 Struttura Database Amministratori

Il database è composto principalmente da due entità principali:

| Tabella | Campi principali | Descrizione |
| :---- | :---- | :---- |
| **admin\_users** | email (PRIMARY KEY), note, added\_at | Elenco degli utenti autorizzati ad accedere all'interfaccia web, con email Google associata al profilo OAuth, ruolo amministrativo e metadati di accesso. |

2.3 Relazioni tra entità

---

## 3\. Design del software

### 3.1 Struttura logica elaborazione frame

Il sistema è suddiviso in moduli indipendenti che comunicano tramite MQTT:

* **Modulo di acquisizione**: gestisce la connessione con la videocamera S32 Cam e pubblica i frame in tempo reale sul topic MQTT camera/frames.  
* **Modulo di rilevamento**: si iscrive a camera/frames, individua e classifica i veicoli tramite YOLO, localizza le targhe e pubblica i risultati su detection/vehicles.  
* **Modulo di controllo distanza**: riceve i dati da detection/vehicles, calcola la distanza stimata del veicolo tramite la dimensione del bounding box, e pubblica su detection/nearby solo i veicoli entro la soglia configurata. Questo evita elaborazioni OCR su veicoli ancora lontani dall'ingresso.  
* **Modulo OCR**: riceve da detection/nearby, esegue la lettura della targa tramite Fast Plate OCR e pubblica il risultato testuale su ocr/result.  
* **Modulo di controllo accessi**: riceve la targa da ocr/result, applica il controllo dell'intervallo temporale per evitare duplicazioni (verifica che la stessa targa non sia già stata registrata negli ultimi N secondi), interroga il database per verificare l'autorizzazione, determina il tipo di evento (entrata/uscita) e pubblica la decisione su access/decision. Salva il risultato nel database.  
* **Modulo DatabaseManager**: gestisce le interrogazioni e le scritture su entrambi i database SQLite (authorized\_plates, access\_history, admin\_users).

*Nota: come da documento Analisi, i moduli di localizzazione targa e OCR vengono eseguiti solo per veicoli classificati a 4 ruote, e solo se entro la soglia di distanza.*

### 3.2 Logica del controllo distanza

### Il controllo della distanza è implementato nel modulo dedicato e si basa sulla dimensione relativa del bounding box del veicolo rispetto all'altezza del frame. Un veicolo occupa una porzione maggiore del frame quanto più è vicino alla camera. La soglia di attivazione è configurabile tramite parametro nel file di configurazione del sistema.

### 3.3 Logica del controllo Intervallo Temporale

Per evitare che la stessa targa venga memorizzata più volte durante il medesimo transito, il modulo di controllo accessi mantiene un dizionario in memoria con le ultime targhe elaborate e il relativo timestamp. Prima di procedere con la verifica dell'autorizzazione, il modulo controlla che siano trascorsi almeno N secondi dall'ultima rilevazione della stessa targa. Il valore di N è configurabile nel file di configurazione del sistema.

3.4 Diagramma di sequenza elaborazione frame (suddivisione moduli)

### 

*\*il sistema di autenticazione utente del modulo WebApp è illustrato al punto 3.6*

### 3.5 Struttura logica interfaccia utente

L’interfaccia utente è organizzata nei seguenti moduli cooperanti:

* **Modulo di Autenticazione**: gestisce l’accesso degli utenti tramite OAuth 2.0 di Google, integrato nel backend Flask. Il funzionamento prevede il reindirizzamento alla pagina di login di Google quanto un utente cerca di accedere. Successivamente all’autorizzazione, Google restituisce un authorization code al server che verrà utilizzato da questo per effettuare una richiesta alle API Google OAuth per leggere i dati del profilo base dell’utente, verificando così che sia un utente autorizzato.  
* **Modulo di Gestione e Comunicazione**: le diverse operazioni dell’interfaccia dono gestite tramite route Flask dedicate. Ogni azione dell’utente corrisponde a una richiesta HTTP GET o POST che viene inviata al server che la elabora, interagisce col database e restituisce la risposta in formato HTML.   
* **Modulo di interazione con il Database**: un Database Manager interno al backend si occupa di operazioni quali lettura, scrittura o aggiornamento dati, quanto richiamato dalla route Flask. Il frontend non accede mai direttamente al database, bensì opera esclusivamente attraverso API logiche del server.

### 3.6 Diagramma di sequenza autenticazione interfaccia utente

passaggi backend autenticazione:

1. **Reindirizzamento login Google**: quando la pagina web viene caricata, Flask genera una richiesta di autorizzazione a Google e l'utente viene reindirizzato alla pagina di login di Google  
2. **Accesso tramite credenziali**: l’utente inserisce le proprie credenziali dell’account Google e se il login ha successo, Google chiede il consenso di condividere i dati richiesti e reindirizza nuovamente l’utente al server Flask   
3. **Ricezione codice autorizzazione**: Flask riceve da Google un *authorization code* che viene utilizzato dal server per effettuare una richiesta al server Google ottenendo di ottenere un *access token* che consente al server Flask di ricavare le informazioni del profilo utente tramite il Userinfo API.  
4. **Verifica autorizzazione**: Flask verifica che l’email dell’utente che tenta l’accesso sia contenuta in un elenco (salvato su file locale) di email di utenti autorizzati. Se l’email è presente, crea una sessione attiva.

---

## 4\. Scelte tecnologiche

La selezione delle tecnologie è stata guidata da criteri di efficienza, disponibilità di documentazione, compatibilità con Python e idoneità al contesto del progetto.

| Componente | Tecnologia scelta | Motivazione |
| ----- | ----- | ----- |
| Linguaggio | Python 3.10+ | Ampia disponibilità di librerie per computer vision e machine learning; sintassi chiara e manutenibilità del codice |
| Comunicazione moduli | MQTT (Mosquitto) | Protocollo leggero, adatto a sistemi embedded e IoT; garantisce il disaccoppiamento tra moduli e supporta la scalabilità dell'architettura. |
| Detection veicoli | YOLOv8 (ultralytics) | Velocità di inferenza elevata (adatta al real-time); buona precisione nel rilevamento di oggetti; modello yolov8n.pt leggero e ottimizzato |
| OCR targhe | Fast Plate OCR | Supporto nativo per caratteri alfanumerici italiani ed europei; elevata precisione nel riconoscimento di targhe; facilità di integrazione |
| Database principale | SQLite (sqlite3) | Leggero ed embedded; non richiede server separato; sufficiente per il volume di dati previsto. |
| Database utenti | SQLite (sqlite3) | Database separato per la gestione degli utenti amministratori, garantendo separazione logica e di sicurezza. |
| Framework web | Flask | Minimalista e flessibile; curva di apprendimento ridotta; adatto per applicazioni di piccole-medie dimensioni; ampia community |
| Computer Vision | OpenCV | Libreria standard per elaborazione immagini; operazioni di pre-processing e manipolazione frame; integrazione con YOLO |
| Hardware acquisizione | S32 Cam / Raspberry Pi con camera | Camera dedicata con buona qualità di acquisizione; compatibilità con protocolli di streaming video; posizionata all'ingresso della struttura |
| *Accelerazione* | *GPU (opzionale)* | *CUDA per accelerare inferenza YOLO; riduce i tempi di elaborazione per garantire il successo di RNF-01 e RNF-02* |

### 

---

## 5\. Interfaccia utente (UI/UX)

L'interfaccia è progettata per essere semplice, intuitiva e funzionale, permettendo agli amministratori della struttura scolastica di gestire il sistema senza necessità di competenze tecniche avanzate. Essendo web-based, è accessibile da qualsiasi dispositivo connesso alla rete locale tramite browser.

### 5.1 Principi di design

* **Accessibilità**: interfaccia costruita secondo la logica responsive garantendo un utilizzo da dispositivi di diverse dimensioni e proporzioni, quali computer, tablet o smartphone.  
* **Chiarezza**: informazioni organizzate in modo logico con etichette descrittive  
* **Consistenza**: stile grafico uniforme su tutte le pagine

### 5.2 Autenticazione

L’accesso all’interfaccia è protetto da autenticazione che garantisce l’accesso solo agli utenti autorizzati. Il sistema di accesso si basa su **OAuth 2.0** di Google e l’utente deve effettuare il login tramite il proprio account Google istituzionale. Di conseguenza il sistema non gestisce direttamente le credenziali, aumentando così il livello di sicurezza. 

### 5.3 Sezioni sito 

La gestione delle singole sezioni del sito e delle loro relazioni è gestita tramite Flask. In particolare il sito offre le seguenti sezioni:

* **autenticazione**: pagina di accesso alla piattaforma che necessità di credenziali amministrative.  
* **homepage**: pagina principale contenente i collegamenti alle altre sezioni.  
* **targhe autorizzate**: visualizza l’elenco delle targhe autorizzate indicando il rispettivo proprietario del veicolo, il suo ruolo e la scadenza di validità dell’autorizzazione.  
* **inserimento/modifica targa**: pagina di supporto per aggiungere una nuova targa autorizzata o modificarne una già inserita  
* **log accessi**: visualizza l’elenco dei veicoli che sono stati autorizzati all'entrata/uscita dalla struttura in una specifica data.  
* **Registro accessi**: Visualizza lo storico completo degli accessi, con filtri per data, targa, stato (autorizzato/non autorizzato) ed evento (entrata/uscita).  
* **Analytics**: Consente agli amministratori di aggiungere, modificare o rimuovere utenti con accesso all'interfaccia web. I dati vengono salvati nel database admin\_users.db.  
* **Gestione utenti**: Form di supporto per aggiungere o modificare una targa autorizzata (numero targa, proprietario, ruolo, data scadenza).


### 5.4 Wireframe 

I wireframe a seguire rappresentano la logica strutturale delle principali schermate del sito, coerentemente disegnate per offrire un’interfaccia lineare e accessibile.  
Lo scopo di quest’opera è di anticipare, prima dell’esecuzione grafica definitiva, la collocazione degli elementi fondamentali, curando attentamente il disegno dei vari contenuti e la serie delle varie parti sotto l’aspetto visivo.

5.4.1 Homepage  
La schermata iniziale presenta una panoramica generale del sistema di gestione accessi.  
Il layout include la barra di navigazione con le principali sezioni e tre aree informative che illustrano le funzionalità principali: controllo automatico, gestione centralizzata e storico degli accessi.  
Il footer riporta i crediti del progetto e i diritti riservati.

La pagina dedicata al registro degli accessi consente di consultare in modo chiaro e organizzato le rilevazioni effettuate dal sistema di entrate e uscite **autorizzate**.  
Nella parte superiore sono presenti la barra di navigazione e un’intestazione con il titolo della pagina e una breve descrizione.  
La sezione principale include il filtro di ricerca per la data, seguito dall’elenco degli ultimi accessi autorizzati registrati o, in assenza di dati, da un messaggio informativo che segnala la mancanza di log disponibili.

Dalla pagina del registro degli accessi autorizzati è poi possibile (tramite il pulsante a destra in alto) passare alla pagina del registro storico, il quale contiene in aggiunta rispetto all’altro tutti i tentativi di accesso (anche quelli di veicoli non autorizzati). La pagina permette operazioni come l’eliminazione di tutti i log e l’esportazione di questi in formato CSV, insieme a svariati filtri di ricerca degli accessi (sulle date, numero di targa, dati anagrafici del proprietario, il ruolo di quest’ultimo, il numero di log da mostrare e lo stato).

5.4.3 Inserimento/modifica targa   
Costituisce una pagina di supporto che consente di aggiungere una nuova targa autorizzata, oppure modificarne una già esistente. Consente l’inserimento/modifica di seguenti dati: numero targa, proprietario, ruolo proprietario, data di scadenza.

5.4.4 Analytics  
Dashboard con grafici e metriche aggregati: grafico accessi nel tempo (line chart), distribuzione per ora del giorno (bar chart), contatori riassuntivi (totale accessi, accessi autorizzati, non autorizzati, veicoli unici).

5.4.5 Gestione Utenti  
Tabella degli utenti amministratori con email, ruolo (o nota generale), data di aggiunta. Pulsanti per aggiungere un nuovo utente, modificarne uno esistente o rimuoverlo.

---

## 6\. Piano di sviluppo

Il progetto è suddiviso in fasi ben definite, con responsabilità distribuite tra i membri del gruppo. La timeline prevede il completamento entro il 28 maggio 2026\. 

### 6.1 Diagramma di Gantt

Il diagramma di Gantt aggiornato è disponibile al seguente link:

[Gant\_Autonomia.pdf](https://drive.google.com/file/d/11WkpgpBcsfOmwf1vfeE4bd33yVWsxwEn/view?usp=sharing)  
[GanntPro](https://app.ganttpro.com/shared/token/b6b6309e361fa4e71d3c1392ede444150195c27976ea17acc5be1b09ff55099e/2072885)
