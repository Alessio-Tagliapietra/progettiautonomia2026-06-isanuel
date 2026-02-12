# Progettazione del Sistema \- Design

---

## Indice

1. [Architettura generale](#1-architettura-generale)
2. [Modellazione dei dati ](#2-modellazione-dei-dati)
3. [Design del software](#3-design-del-software) 
4. [Scelte tecnologiche](#4-scelte-tecnologiche)
5. [Interfaccia utente (UI/UX)](#5-interfaccia-utente-uiux)

---

## 1\. Architettura generale

Il sistema utilizza un͏'architettur͏a di tipo Client–Server, dove͏ il client ͏(camera S32 C͏am) ha ͏compito di prendere frame video, mentre il server di lavorazione gestisce le azioni di analisi, riconoscimento ͏targhe e control͏lo permessi.

#### 1.1 Componenti Software principali

L'architettura si compone di tre macro-componenti principali:

* **Frontend (Interfaccia Web)**: consente all'amministratore di gestire i veicoli autorizzati, monitorare i log degli accessi e controllare lo stato del sistema tramite browser.  
* **Backend (Server di Elaborazione)**: gestisce il flusso di elaborazione dei frame, l'analisi delle immagini tramite computer vision, l'OCR per la lettura delle targhe e la verifica delle autorizzazioni confrontando con il database.  
* **Database**: conserva le informazioni relative ai veicoli autorizzati e ai log degli accessi in formato SQLite.

### 1.2 Design pattern

Il design pattern adottato è il MVC (Model–View–Controller) in versione web-based:

* **Model**: gestione dei dati e delle operazioni di lettura/scrittura sul database SQLite tramite la classe Database Manager;  
* **View**: interfaccia grafica web implementata con template HTML/CSS renderizzati da Flask;  
* **Controller**: logica di elaborazione, routing delle richieste HTTP e coordinamento tra Model e View.

### 1.3 Componenti Hardware e integrazione Software

Il sistema è progettato per operare in un ambiente integrato hardware-software. Le componenti hardware sono costituite da una camera di acquisizione frame (s32 cam), di un server per l’elaborazione dei frame e gestione piattaforma e del cancello dell’ingresso.

*note*: la modalità di gestione del cancello è ancora da valutare e non fa parte dello scopo attuale del progetto.

---

## 2\. Modellazione dei dati

Il database è stato progettato per mantenere la tracciabilità dei veicoli autorizzati e delle targhe rilevate nel tempo. È implementato in SQLite per garantire leggerezza, portabilità e assenza di dipendenze esterne.

### 2.1 Struttura del database

Il database è composto principalmente da due entità principali:

| Tabella | Campi principali | Descrizione |
| :---- | :---- | :---- |
| authorized\_plates | plate\_number (PK), first\_name, last\_name, role, expiration\_date | Contiene l'elenco delle targhe autorizzate ad accedere con informazioni sul proprietario e ruolo (docente, studente, personale) |
| access\_history | id (PK), plate\_number (FK), timestamp, status, image\_path | Memorizza ogni rilevamento con data, ora e stato dell'autorizzazione (autorizzato/non autorizzato) |

2.2 Relazioni tra entità

---

## 3\. Design del software

### 3.1 Struttura logica elaborazione frame

Il sistema è suddiviso in moduli indipendenti ma cooperanti:

* **Modulo di connessione**: gestione della connessione con la videocamera S32 Cam e acquisizione di frame in tempo reale.  
* **Modulo di rilevamento**: individuazione, classificazione dei veicoli e localizzazione delle targhe tramite YOLO.  
* **Modulo OCR**: lettura del testo della targa (formato italiano) mediante Fast Plate OCR.  
* **Modulo DatabaseManager**: gestisce le interrogazioni e scritture del database SQLite.  
* **Modulo controllo accesso**: coordinamento dei moduli di rilevamento, lettura OCR e verifica nel database per stabilire se il veicolo è *authorized* o *not\_authorized*. 

*note*: come previsto dal documento *Analisi*, i moduli di localizzazione e lettura della targa e di gestione del database vengono eseguiti solo nel caso di classificazione del veicolo come a “4 ruote” e che, quindi, richiede un'analisi più approfondita per determinare se è autorizzato o meno.

### 3.2 Diagramma di sequenza elaborazione frame

## 

### 3.3 Struttura logica interfaccia utente

L’interfaccia utente è organizzata nei seguenti moduli cooperanti:

* **Modulo di Autenticazione**: gestisce l’accesso degli utenti tramite OAuth 2.0 di Google, integrato nel backend Flask. Il funzionamento prevede il reindirizzamento alla pagina di login di Google quanto un utente cerca di accedere. Successivamente all’autorizzazione, Google restituisce un authorization code al server che verrà utilizzato da questo per effettuare una richiesta alle API Google OAuth per leggere i dati del profilo base dell’utente, verificando così che sia un utente autorizzato.  
* **Modulo di Gestione e Comunicazione**: le diverse operazioni dell’interfaccia dono gestite tramite route Flask dedicate. Ogni azione dell’utente corrisponde a una richiesta HTTP GET o POST che viene inviata al server che la elabora, interagisce col database e restituisce la risposta in formato HTML.   
* **Modulo di interazione con il Database**: un Database Manager interno al backend si occupa di operazioni quali lettura, scrittura o aggiornamento dati, quanto richiamato dalla route Flask. Il frontend non accede mai direttamente al database, bensì opera esclusivamente attraverso API logiche del server.

### 3.4 Diagramma di sequenza autenticazione interfaccia utente

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
| Detection veicoli | YOLOv8 (ultralytics) | Velocità di inferenza elevata (adatta al real-time); buona precisione nel rilevamento di oggetti; modello yolov8n.pt leggero e ottimizzato |
| OCR targhe | Fast Plate OCR | Supporto nativo per caratteri alfanumerici italiani ed europei; elevata precisione nel riconoscimento di targhe; facilità di integrazione |
| Database | SQLite (sqlite3) | Leggero e embedded; non richiede server separato; perfetto per applicazioni stand-alone; sufficiente per il volume di dati previsto |
| Framework web | Flask | Minimalista e flessibile; curva di apprendimento ridotta; adatto per applicazioni di piccole-medie dimensioni; ampia community |
| Computer Vision | OpenCV | Libreria standard per elaborazione immagini; operazioni di pre-processing e manipolazione frame; integrazione con YOLO |
| Hardware acquisizione | S32 Cam / arduino con camera | Camera dedicata con buona qualità di acquisizione; compatibilità con protocolli di streaming video; posizionata all'ingresso della struttura |
| *Accelerazione* | *GPU (non necessario)* | *CUDA per accelerare inferenza YOLO; riduce i tempi di elaborazione per garantire il successo di RNF-01 e RNF-02* |

### 

---

## 5\. Interfaccia utente (UI/UX)

L'interfaccia è progettata per essere semplice, intuitiva e funzionale, permettendo agli amministratori della struttura scolastica di gestire il sistema senza necessità di competenze tecniche avanzate. Essendo web-based, è accessibile da qualsiasi dispositivo connesso alla rete locale tramite browser.

### 5.1 Principi di design

* **Accessibilità**: interfaccia costruita secondo la logica responsive garantendo un utilizzo da dispositivi di diverse dimensioni e proporzioni, quali computer, tablet o smartphone.  
* **Chiarezza**: informazioni organizzate in modo logico con etichette descrittive  
* **Consistenza**: stile grafico uniforme su tutte le pagine

### 5.2 Autenticazione

L’accesso all’interfaccia è protetto da autenticazione che garantisce l’accesso solo agli utenti autorizzati. Il sistema di accesso si basa su **OAuth 2.0** di Google e l’utente deve effettuare il login tramite il proprio account Google scolastico. Di conseguenza il sistema non gestisce direttamente le credenziali, aumentando così il livello di sicurezza. 

### 5.3 Sezioni sito 

La gestione delle singole sezioni del sito e delle loro relazioni è gestita tramite Flask. In particolare il sito offre le seguenti sezioni:

* **autenticazione**: pagina di accesso alla piattaforma che necessità di credenziali amministrative.  
* **homepage**: pagina principale contenente i collegamenti alle altre sezioni.  
* **targhe autorizzate**: visualizza l’elenco delle targhe autorizzate indicando il rispettivo proprietario del veicolo, il suo ruolo e la scadenza di validità dell’autorizzazione.  
* **inserimento/modifica targa**: pagina di supporto per aggiungere una nuova targa autorizzata o modificarne una già inserita  
* **log accessi**: visualizza l’elenco dei veicoli che hanno tentato l’accesso alla struttura indicando informazioni temporali e stato dell’autorizzazione.

### 5.4 Wireframe 

I wireframe a seguire rappresentano la logica strutturale delle principali schermate del sito, coerentemente disegnate per offrire un’interfaccia lineare e accessibile.  
Lo scopo di quest’opera è di anticipare, prima dell’esecuzione grafica definitiva, la collocazione degli elementi fondamentali, curando attentamente il disegno dei vari contenuti e la serie delle varie parti sotto l’aspetto visivo.

5.4.1 Homepage  
La schermata iniziale presenta una panoramica generale del sistema di gestione accessi.  
Il layout include la barra di navigazione con le principali sezioni e tre aree informative che illustrano le funzionalità principali: controllo automatico, gestione centralizzata e storico degli accessi.  
Il footer riporta i crediti del progetto e i diritti riservati.

5.4.2 Log degli ultimi accessi  
La pagina dedicata al registro degli accessi consente di consultare in modo chiaro e organizzato lo storico delle rilevazioni effettuate dal sistema.  
Nella parte superiore sono presenti la barra di navigazione e un’intestazione con il titolo della pagina e una breve descrizione.  
La sezione principale include i filtri di ricerca, seguiti dall’elenco degli ultimi accessi registrati o, in assenza di dati, da un messaggio informativo che segnala la mancanza di log disponibili.

5.4.3 Inserimento/modifica targa   
Costituisce una pagina di supporto che consente di aggiungere una nuova targa autorizzata, oppure modificarne una già esistente. Consente l’inserimento/modifica di seguenti dati: numero targa, proprietario, ruolo proprietario, data di scadenza.

---
