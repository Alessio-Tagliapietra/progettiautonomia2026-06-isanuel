# Analisi del Progetto

**progetto**: Sistema di machine learning per l’automatizzazione dell’accesso a una struttura privata  
**componenti gruppo:**  Manuel Sannicolò, Isabel Zoner  
**materia**: Autonomia Informatica  
**data inizio progetto**: 16/09/2025

# ---

Indice 

1. [Introduzione](#1.-introduzione)  
2. [Obiettivi e scopo](#2.-obiettivi-e-scopo)  
3. [Contesto e ambito](#3.-contesto-e-ambito)  
4. [Requisiti funzionali](#4.-requisiti-funzionali)  
5. [Requisiti non funzionali](#5.-requisiti-non-funzionali)  
6. [Rischi e criticità](#6.-analisi-dei-rischi-e-criticità)  
7. [Diagramma caso d’uso](#7.-diagramma-caso-d’uso) 

---

# 1\. Introduzione {#1.-introduzione}

Il progetto riguarda lo sviluppo di un sistema di machine learning in grado di rilevare, riconoscere e leggere targhe tramite una fotocamera, con l’obiettivo di rendere automatico l’ingresso all'interno di una struttura ai soli utenti autorizzati. Più in particolare, il sistema è stato progettato per la gestione dell’entrata in una struttura scolastica, in modo tale da consentire l’accesso soltanto a insegnanti, responsabili scolastici e studenti che utilizzano veicoli a due ruote, come motocicli o biciclette. 

Il funzionamento del nostro sistema è basato su tecniche di computer vision, OCR e tracking. Questo perché permettono di rilevare il veicolo, identificarne la targa e poi anche di leggerne il contenuto. Successivamente, la targa viene confrontata con un elenco di veicoli che sono autorizzati; se il veicolo risulta registrato e autorizzato,  allora l’accesso viene consentito, altrimenti viene negato. 

L'architettura del sistema è basata su una struttura a moduli indipendenti che comunicano tramite il protocollo MQTT, garantendo maggiore flessibilità, scalabilità e disaccoppiamento tra i componenti. L'hardware previsto per la realizzazione comprende una S32 Cam oppure, in alternativa, un Raspberry Pi dotato di videocamera, posizionata all'entrata della struttura. I frame catturati vengono elaborati localmente o inviati tramite MQTT al server centrale per l'analisi, il riconoscimento della targa e la determinazione dell'autorizzazione all'accesso.

# 2\. Obiettivi e Scopo {#2.-obiettivi-e-scopo}

### 2.1 Obiettivi

L’obiettivo principale del progetto è automatizzare il controllo degli accessi a una struttura, eliminando la necessità di un operatore umano.  
Per raggiungere questo scopo, il sistema si articola in una serie di obiettivi funzionali di supporto, che cooperano per garantire un funzionamento affidabile e modulare:

* Rilevamento dei veicoli presenti all’interno di ogni frame acquisito dalla telecamera;  
* Classificazione della tipologia di veicolo (es. automobile, motocicletta, bicicletta);  
* Localizzazione della targa nel caso di veicoli a quattro ruote;   
* Lettura del testo della targa tramite OCR, minimizzando gli errori di riconoscimento;  
* Gestione del sistema tramite un'interfaccia dedicata, che permette:   
  * Aggiunta oppure la rimozione di veicoli autorizzati;   
  * Attivazione o disattivazione in maniera temporanea del sistema;   
  * Visualizzazione dell’elenco dei veicoli che hanno tentato l’accesso  
  * Gestione degli utenti che possono usufruire dell’interfaccia  
* Salvataggio dei dati (targhe, timestamp, stato autorizzazione, tipologia evento entrata/uscita) in un archivio locale;   
* Scalabilità del sistema tramite architettura modulare basata su MQTT per permettere futuri miglioramenti, aggiornamenti o integrazioni. 

### 2.2 Benefici

L’adozione di questo nostro sistema comporta numerosi vantaggi, in termini di efficienza, sicurezza e automazione del controllo degli accessi ad un determinato ambiente.   
Più in particolare il sistema permette: 

* Automatizzazione del controllo dei veicoli in ingresso alla struttura, eliminando quindi la necessità di personale;   
* Impedimento d’ingresso a veicoli che non sono autorizzati, garantendo così un maggiore livello di sicurezza e un monitoraggio costante di tutti accessi;   
* Registrazione dei veicoli che transitano, consentendo la creazione di uno storico consultabile;   
* Analisi statistica degli accessi tramite la sezione Analytics dell'interfaccia web;  
* Gestione centralizzata degli utenti amministratori tramite database dedicato;  
* L’ottimizzazione della gestione delle risorse in modo tale da migliorare la fluidità del traffico, in prossimità dell’ingresso alla struttura interessata. 

# 3\. Contesto e ambito {#3.-contesto-e-ambito}

### 3.1 Contesto

Il sistema si inserisce in un contesto di videosorveglianza e monitoraggio automatico dei veicoli, dove le tecnologie di computer vision, intelligenza artificiale vengono impiegate con lo scopo di automatizzare il controllo degli accessi e migliorare la sicurezza. L’obiettivo è quello di ridurre l'intervento dell'uomo, assicurando allo stesso tempo rapidità e affidabilità nell’identificare i veicoli autorizzati. 

Il progetto è stato sviluppato in particolare per l’ambiente scolastico, in modo tale da gestire in modo automatico l’ingresso dei veicoli di docenti, personale autorizzato e studenti che utilizzano mezzi a due ruote. La sua architettura è comunque facilmente adattabile ad altri contesti, quali parcheggi privati o delle strutture aziendali grazie all’architettura modulare basata su MQTT. 

### 3.2 Ambito

Il sistema comprende tutte le funzionalità necessarie per l'analisi automatica dei frame acquisiti dalla videocamera, inclusi il rilevamento veicoli con controllo di distanza, la localizzazione e lettura targhe, il controllo degli accessi con gestione eventi entrata/uscita, e un'interfaccia web per il monitoraggio e la gestione. I dati vengono salvati in un archivio locale SQLite con due database distinti: uno per le targhe autorizzate e i log degli accessi, uno per gli utenti amministratori.

Rimangono escluse dall’ambito del progetto le seguenti funzionalità:

* Gestione della sanzione in caso di infrazioni;  
* Integrazione con sistema di sicurezza nazionali, quali banche dati di targhe rubate;  
* Elaborazione immagini in condizioni estreme come pioggia intensa o nebbia fitta.

### 3.3 Componenti e attori principali

| Componente / Attore | Ruolo | Descrizione |
| :---- | :---- | :---- |
| S32 Cam / Raspberry Pi con fotocamera | Hardware | Dispositivo di acquisizione video incaricato della cattura dei frame dei veicoli in avvicinamento all'ingresso. |
| Modulo di acquisizione e rilevamento | Software | Acquisisce i frame, applica il controllo distanza, rileva e classifica i veicoli, localizza le targhe tramite YOLO e pubblica i risultati via MQTT. |
| Modulo OCR e controllo accessi | Software | Legge il testo della targa, applica il controllo dell'intervallo temporale tra rilevamenti e verifica l'autorizzazione consultando il database. |
| Broker MQTT | Middleware | Componente di comunicazione che smista i messaggi tra i moduli software del sistema, garantendo il disaccoppiamento tra acquisizione ed elaborazione. |
| Database principale (SQLite) | Storage | Memorizza le targhe autorizzate e i log degli accessi (con campo event per entrata/uscita). |
| Database utenti amministratori (SQLite) | Storage | Database separato per la gestione delle credenziali e dei profili degli utenti amministratori dell'interfaccia web. |
| Interfaccia Web (Flask) | Frontend | Interfaccia web accessibile via browser per la gestione delle targhe, visualizzazione log, analytics e gestione utenti amministratori. |
| Amministratori | Gestori | Utenti responsabili della configurazione del sistema, inserimento/rimozione veicoli autorizzati e monitoraggio tramite interfaccia web. |

# 4\. Requisiti Funzionali {#4.-requisiti-funzionali}

| *ID* | Requisito | Descrizione |
| :---- | :---- | :---- |
| RF-01 | Rilevazione veicoli | Il sistema deve rilevare la presenza di veicoli in ogni frame acquisito. |
| RF-02 | Classificazione veicoli | I veicoli rilevati devono essere classificati per tipologia (auto, camion, moto, bicicletta, ecc.). |
| RF-03 | Controllo distanza | Il sistema deve calcolare la distanza stimata del veicolo rilevato e avviare l'analisi approfondita solo al superamento di una soglia minima di vicinanza, evitando elaborazioni su veicoli lontani. |
| RF-04 | Localizzazione targhe | Il sistema deve individuare la regione dell'immagine contenente la targa per veicoli a quattro ruote. |
| RF-05 | Lettura targhe OCR | Il sistema deve leggere e trascrivere in formato testuale il contenuto della targa, riducendo gli errori di riconoscimento. |
| RF-06 | Controllo intervallo rilevamenti | Il sistema deve implementare un meccanismo di controllo temporale per evitare che la stessa targa venga memorizzata più volte durante la medesima sessione di transito. |
| RF-07 | Salvataggio dati accessi | Il sistema deve memorizzare le targhe rilevate con timestamp, stato di autorizzazione e tipo di evento (entrata/uscita). |
| RF-08 | Gestione targhe autorizzate | L'interfaccia web consente agli amministratori di aggiungere, modificare o rimuovere veicoli autorizzati. |
| RF-09 | Registro accessi | L'interfaccia web offre una pagina dedicata per consultare lo storico degli accessi filtrabili per data, targa e stato. |
| RF-10 | Analytics | L'interfaccia web offre una sezione di analytics con statistiche sugli accessi (es. accessi per giorno, veicoli più frequenti, accessi non autorizzati). |
| RF-11 | Gestione utenti amministratori | L'interfaccia web consente la gestione degli utenti amministratori (aggiunta, modifica, rimozione) tramite un database dedicato. |
| RF-12 | Autenticazione amministratori | La gestione del sistema è accessibile solo ad utenti autenticati con credenziali amministrative tramite OAuth 2.0 di Google. |

# 5\. Requisiti non Funzionali  {#5.-requisiti-non-funzionali}

| Categoria | ID | Requisito | Descrizione |
| :---- | :---- | :---- | :---- |
| Prestazioni | *RNF-01* | Analisi in tempo reale | Il sistema deve elaborare i frame in real-time, con un tempo di processamento per veicolo non superiore a 3 secondi |
|  | *RNF-02* | Tempo di risposta | La rilevazione e lettura della targa devono avvenire con latenza minima per garantire efficienza |
| Prestazioni | RNF-03 | Latenza MQTT | La comunicazione tra moduli tramite MQTT deve avvenire con latenza inferiore a 500ms per non compromettere le prestazioni complessive. |
| Usabilità | *RNF-04* | Interfaccia grafica | Il sistema dispone di un’interfaccia utente per la gestione del sistema, inclusa la configurazione dei veicoli autorizzati e attivazione/disattivazione del servizio |
|  | *RNF-05* | Funzioni di log e report  | Il sistema genera automaticamente log e report consultabili per il monitoraggio del servizio |
| Tecnologici | *RNF-06* | Linguaggio | Il sistema deve essere sviluppato in Python 3.10 o versioni superiori |
|  | *RNF-07* | Hardware | Utilizzo di camera con buona qualità di acquisizione video; il sistema deve supportare l’accelerazione tramite GPU se disponibile |
| Tecnologici | RNF-08 | Protocollo MQTT | Il sistema deve utilizzare un broker MQTT (es. Mosquitto) per la comunicazione tra i moduli. |
| Manutenibilità | *RNF-09* | Architettura modulare | Il codice deve essere organizzate in moduli e funzioni separati per facilitare la manutenzione e debugging |
|  | *RNF-10* | Scalabilità | Deve essere possibile estendere le funzionalità, aggiungere nuovi filtri di elaborazione o integrazioni future con altri sistemi |

# 6\. Analisi dei rischi e criticità {#6.-analisi-dei-rischi-e-criticità}

| Rischio | Gravità | Risoluzione |
| :---- | :---- | :---- |
| Qualità video scadente | Alta | Sostituire la videocamera con un dispositivo di qualità superiore o regolare i parametri di esposizione e risoluzione. |
| Condizioni di luce variabili | Media | Implementare tecniche di pre-processing dei frame per migliorare la rilevazione e lettura delle targhe. |
| Condizioni meteorologiche estreme (pioggia intensa o nebbia fitta) | Alta | Prevedere metodi alternativi di accesso alla struttura, come sistemi di badge o tessere. |
| Velocità di elaborazione insufficiente per il real-time | Media | Ottimizzazione del codice e utilizzo di hardware con GPU per accelerare l'elaborazione. Il controllo distanza riduce il numero di elaborazioni non necessarie. |
| Duplicazione di log per lo stesso transito | Bassa | Il modulo di controllo dell'intervallo temporale tra rilevamenti previene la memorizzazione multipla della stessa targa nella medesima sessione di transito. |
| Interruzione della comunicazione MQTT | Media | Implementare meccanismi di riconnessione automatica al broker e gestione degli errori di comunicazione nei singoli moduli. |
| Accesso non autorizzato all'interfaccia di gestione | Alta | Autenticazione tramite OAuth 2.0 di Google con verifica delle email autorizzate, gestite tramite database dedicato agli utenti amministratori. |

# 7\. Diagramma caso d’uso {#7.-diagramma-caso-d’uso}
