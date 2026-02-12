# Manuale Utente

# **Sistema di gestione accesso di veicoli**

---

## Indice

1. [Introduzione](#1-introduzione)  
2. [Accesso al Sistema](#2-accesso-al-sistema)  
3. [Panoramica Dashboard](#3-panoramica-dashboard)  
4. [Gestione Targhe Autorizzate](#4-gestione-targhe-autorizzate)  
5. [Consultazione Log Accessi](#5-consultazione-log-accessi)  
6. [Controllo Servizio](#6-controllo-servizio)  
7. [Domande Frequenti](#7-domande-frequenti)

---

## 1\. Introduzione 

Benvenuti nel sistema di gestione accessi veicolari. Questa piattaforma consente di:

* ✅ Gestire le targhe autorizzate all'accesso  
* 📊 Monitorare tutti gli accessi in tempo reale  
* 📋 Consultare lo storico completo degli eventi  
* ⚙️ Controllare lo stato del sistema di rilevamento

### **Chi può usare il sistema?**

Solo gli utenti autorizzati con account Google registrato dall'amministratore possono accedere alla piattaforma.

---

## 2\. Accesso al Sistema 

### 2.1 Come effettuare il login

**Passo 1: Aprire il browser**

* Utilizzare un browser moderno (Chrome, Firefox, Edge, Safari)  
* Digitare nella barra degli indirizzi:  
  * `http://localhost:5000` (se sul computer locale)  
  * Oppure l'indirizzo IP fornito dall'amministratore (es. `http://192.168.1.100:5000`)

**Passo 2: Pagina di login**

Verrà visualizzata la schermata di accesso con il pulsante **"Accedi con Google"**

\!\[Login\](esempio: schermata con pulsante blu Google)

**Passo 3: Autenticazione Google**

1. Cliccare sul pulsante **"Accedi con Google"**  
2. Si aprirà una finestra di Google  
3. Selezionare il proprio account Google dalla lista  
4. Se richiesto, inserire la password  
5. Al primo accesso, autorizzare l'applicazione cliccando **"Consenti"**

**Passo 4: Accesso completato**

Dopo l'autenticazione, verrete automaticamente reindirizzati alla dashboard principale del sistema.

---

### 2.2 Cosa fare se l'accesso viene negato

Se compare il messaggio:

| ⚠️ "Non sei autorizzato ad accedere" |
| :---- |

**Causa:** Il vostro indirizzo email non è nella lista degli utenti autorizzati.

**Soluzione:**

1. Verificare di aver utilizzato l'account Google corretto  
2. Contattare l'amministratore di sistema  
3. Fornire il proprio indirizzo email Gmail  
4. Attendere che l'amministratore aggiunga l'email alla whitelist  
5. Riprovare il login

---

### 2.3 Come effettuare il logout

Per uscire dal sistema in modo sicuro:

1. Cliccare sul menu utente in alto a destra (icona profilo o nome)  
2. Selezionare **"Logout"**  
3. Verrà visualizzato il messaggio: *"Logout effettuato con successo"*  
4. Si verrà reindirizzati alla pagina di login

💡 **Consiglio:** Effettuare sempre il logout quando si lascia il computer incustodito, specialmente se condiviso con altri.

---

## 3\. Panoramica Dashboard 

Dopo il login, viene visualizzata la **Dashboard principale** con tutte le informazioni essenziali.

### 3.1 Elementi della Dashboard

#### **Barra di Navigazione (in alto)**

* **Logo/Nome Sistema** (in alto a sinistra)  
* **Menu principale:**  
  * 🏠 **Home** \- Torna alla dashboard  
  * 🚗 **Targhe** \- Gestione targhe autorizzate  
  * 📋 **Log** \- Storico accessi  
* **Utente** (in alto a destra) \- Nome utente e pulsante Logout

#### **Pannello Statistiche**

La dashboard mostra tre riquadri informativi:

**📊 Targhe Totali**

* Numero complessivo di targhe registrate nel sistema  
* Include targhe valide, scadute e in attesa

**✅ Targhe Valide**

* Targhe attualmente autorizzate all'accesso  
* Non include quelle scadute

**⏰ Targhe Scadute**

* Targhe con autorizzazione scaduta  
* Richiedono rinnovo per essere riattivate

---

## 4\. Gestione Targhe Autorizzate 

### 4.1 Visualizzare tutte le targhe

**Passo 1:** Dalla dashboard, cliccare su **"Targhe"** nel menu principale

**Passo 2:** Verrà visualizzata la pagina "Gestione Targhe" con una tabella contenente:

| Colonna | Descrizione |
| :---: | ----- |
| **Numero Targa** | Targa veicolo (es. AB123CD) |
| **Proprietario** | Nome e Cognome |
| **Ruolo** | Categoria (Docente, Studente, ecc.) |
| **Scadenza** | Data fine autorizzazione |
| **Azioni** | Pulsanti Modifica/Elimina |

**Passo 3:** Utilizzare la barra di ricerca per trovare rapidamente una targa specifica

---

### 4.2 Aggiungere una nuova targa

**Quando aggiungere una targa:**

* Nuovo dipendente/studente  
* Visitatore autorizzato  
* Rinnovo con cambio veicolo

**Procedura:**

**Passo 1:** Nella pagina "Gestione Targhe", cliccare il pulsante verde **"+ Aggiungi Nuova Targa"**

**Passo 2:** Compilare il modulo con i dati richiesti:

#### **📝 Campo: Numero Targa (obbligatorio)**

* **Formato:** Seguire lo standard italiano **AA000AA**  
  * 2 lettere \+ 3 numeri \+ 2 lettere  
  * Esempio corretto: `AB123CD`, `FG456HI`, `XY789ZK`  
  * Esempio errato: `123ABC`, `AB12CD`, `ABCD123`  
* **Maiuscole/minuscole:** Il sistema converte automaticamente in maiuscolo  
* Inserire senza spazi

#### **👤 Campo: Nome (obbligatorio)**

* Nome del proprietario del veicolo  
* Esempio: `Mario`, `Laura`

#### **👤 Campo: Cognome (obbligatorio)**

* Cognome del proprietario  
* Esempio: `Rossi`, `Bianchi`

#### **🎓 Campo: Ruolo (obbligatorio)**

* Selezionare dalla lista a tendina:  
  * **Docente** \- Insegnante  
  * **Studente** \- Alunno  
  * **Personale ATA** \- Personale amministrativo/tecnico  
  * **Visitatore** \- Ospite temporaneo  
  * **Altro** \- Altre categorie

#### **📅 Campo: Data Scadenza (facoltativo)**

* Cliccare sul calendario per selezionare la data  
* Formato visualizzato: `GG/MM/AAAA` (es. 31/12/2025)  
* **Se lasciato vuoto:** L'autorizzazione non scade mai

💡 **Suggerimento:** Per autorizzazioni permanenti (es. dipendenti a tempo indeterminato), lasciare vuota la data di scadenza.

**Passo 3:** Cliccare il pulsante **"Salva Targa"**

**Passo 4:** Verrà visualizzato un messaggio di conferma:

| ✅ "Targa AB123CD aggiunta con successo\!” |
| :---: |

La targa è immediatamente attiva e il sistema inizierà a riconoscerla.

---

### 4.3 Modificare una targa esistente

**Quando modificare una targa:**

* Cambio proprietario del veicolo  
* Aggiornamento ruolo  
* Estensione scadenza  
* Correzione errori di inserimento

**Procedura:**

**Passo 1:** Nella tabella delle targhe, individuare la riga da modificare

**Passo 2:** Cliccare il pulsante **"Modifica"** nella colonna "Azioni"

**Passo 3:** Il modulo si aprirà con i dati attuali già inseriti

**Passo 4:** Modificare i campi desiderati:

* Tutti i campi sono modificabili  
* Il numero targa può essere cambiato solo eliminando e ricreando

**Passo 5:** Cliccare **"Salva Modifiche"**

**Passo 6:** Conferma:

| ✅ "Targa aggiornata con successo\!" |
| :---: |

---

### 4.4 Eliminare una targa

**Quando eliminare una targa:**

* Dipendente/studente non più autorizzato  
* Fine periodo visitatore  
* Veicolo dismesso  
* Targa inserita per errore

**Procedura:**

**Passo 1:** Nella tabella delle targhe, individuare la riga da eliminare

**Passo 2:** Cliccare il pulsante **"Elimina"** (icona cestino 🗑️) nella colonna "Azioni"

**Passo 3:** Apparirà un popup di conferma:

| ⚠️ "Vuoi davvero eliminare questa targa?" Questa operazione è irreversibile. |
| :---: |

**Passo 4:** Cliccare:

* **"OK"** per confermare l'eliminazione  
* **"Annulla"** per tornare indietro senza eliminare

**Passo 5:** Se confermato, verrà visualizzato:

| ✅ "Targa AB123CD rimossa\!" |
| :---: |

#### **⚠️ Importante da sapere:**

**Cosa viene eliminato:**

* La targa dal database autorizzazioni  
* L'autorizzazione all'accesso

**Cosa NON viene eliminato:**

* I log storici degli accessi passati (mantenuti per tracciabilità)  
* Le statistiche associate

💡 **Alternativa all'eliminazione:** Se si vuole solo revocare temporaneamente l'accesso senza perdere i dati, modificare la data di scadenza impostandola a una data passata.

---

### 4.5 Gestione Scadenze

#### **Targhe in scadenza**

Il sistema evidenzia automaticamente le targhe in scadenza:

* 🟡 **30 giorni o meno** \- Giallo (scadenza imminente)  
* 🔴 **Scaduta** \- Rosso (autorizzazione non più valida)

#### **Cosa fare con targhe scadute**

**Opzione 1: Rinnovare**

1. Cliccare "Modifica" sulla targa scaduta  
2. Aggiornare la data di scadenza con una nuova data futura  
3. Salvare

**Opzione 2: Eliminare**

* Se il veicolo non deve più avere accesso, eliminare la targa

---

## 5\. Consultazione Log Accessi 

La sezione **Log Accessi** permette di visualizzare tutti gli eventi di rilevamento targhe.

### 5.1 Visualizzare i log

**Passo 1:** Dal menu principale, cliccare su **"Log"**

**Passo 2:** Verrà visualizzata la tabella "Storico Accessi" con:

| Colonna | Descrizione | Esempio |
| ----- | ----- | ----- |
| **Data e Ora** | Timestamp rilevamento | 2025-01-10 14:32:15 |
| **Targa** | Numero targa rilevata | AB123CD |
| **Frame** | Numero progressivo nel video | 1523 |
| **Confidenza** | Sicurezza lettura OCR (0-1) | 0.89 |
| **Stato** | Esito verifica autorizzazione | Autorizzato / Non autorizzato / Scaduto |
| **Track ID** | ID tracciamento veicolo | 42 |

#### **Codici Colore Stato:**

* 🟢 **Verde (Autorizzato)** \- Targa valida, accesso consentito  
* 🔴 **Rosso (Non autorizzato)** \- Targa non in database, accesso negato  
* 🟡 **Giallo (Scaduto)** \- Targa presente ma con autorizzazione scaduta

---

### 5.2 Filtrare i log

I filtri permettono di trovare rapidamente eventi specifici.

#### **Filtro per Numero Targa**

**Utilizzo:** Vedere tutti gli accessi di una targa specifica

**Procedura:**

1. Nella sezione filtri in alto, individuare il campo **"Filtra per targa"**  
2. Inserire il numero targa (es. `AB123CD`)  
3. Cliccare il pulsante **"Filtra"**  
4. La tabella mostrerà solo i log di quella targa

**Esempio pratico:**

*"Quante volte è passato il veicolo AB123CD questa settimana?"*

---

#### **Filtro per Stato**

**Utilizzo:** Visualizzare solo accessi autorizzati, negati o scaduti

**Procedura:**

1. Nel menu a tendina **"Stato"**, selezionare:  
   * **Tutti** \- Nessun filtro  
   * **Autorizzato** \- Solo accessi validi  
   * **Non autorizzato** \- Solo accessi negati  
   * **Scaduto** \- Solo targhe scadute  
2. Cliccare **"Filtra"**

**Esempio pratico:**

*"Quanti tentativi di accesso non autorizzati ci sono stati oggi?"*

---

#### **Combinare più filtri**

È possibile applicare entrambi i filtri contemporaneamente:

**Esempio:**

* Targa: `AB123CD`  
* Stato: `Non autorizzato`  
* Risultato: Tutti i tentativi falliti della targa AB123CD

---

#### **Rimuovere i filtri**

Per tornare alla visualizzazione completa:

1. Cliccare il pulsante **"Reset"**  
2. Tutti i filtri verranno rimossi  
3. La tabella mostrerà nuovamente tutti i log

---

### 5.3 Esportare i log in CSV

L'esportazione permette di analizzare i dati con programmi esterni (Excel, Google Sheets).

**Quando esportare:**

* Report mensili/annuali  
* Analisi statistiche  
* Backup dati  
* Archiviazione storica

**Procedura:**

**Passo 1:** Nella pagina "Log Accessi", cliccare il pulsante **"📥 Esporta CSV"** in alto a destra

**Passo 2:** Il browser scaricherà automaticamente il file:

* Nome file: `access_logs_AAAAMMGG_HHMMSS.csv`  
* Esempio: `access_logs_20250110_143045.csv`

**Passo 3:** Aprire il file con:

* **Microsoft Excel**  
* **Google Sheets**  
* **LibreOffice Calc**  
* Qualsiasi programma che legge CSV

#### **Contenuto del file CSV:**

ID,Targa,Data e Ora,Frame,Confidenza,Stato,Track ID  
1,AB123CD,2025-01-10 14:30:15,1523,0.89,Autorizzato,42  
2,XY789ZK,2025-01-10 14:35:22,1876,0.92,Non autorizzato,43

#### **Cosa fare con il CSV:**

✅ **Statistiche:**

* Contare accessi per targa  
* Orari di punta  
* Frequenza settimanale/mensile

✅ **Grafici:**

* Andamento accessi nel tempo  
* Percentuale autorizzati vs non autorizzati

✅ **Audit:**

* Verifiche amministrative  
* Report per direzione

---

### 5.4 Cancellare tutti i log

⚠️ **ATTENZIONE:** Questa operazione è **IRREVERSIBILE** e cancella definitivamente tutti i log storici.

**Quando cancellare:**

* Fine anno scolastico/lavorativo  
* Dopo aver esportato un backup  
* Pulizia sistema di test  
* Reset per nuova stagione

**Procedura:**

**Passo 1:** Nella pagina "Log Accessi", cliccare il pulsante rosso **"🗑️ Resetta Log"**

**Passo 2:** Apparirà un popup di avviso:

⚠️ **"Resettando i logs eliminerai tutti i log di accesso in modo permanente"**

Questa operazione **NON PUÒ essere annullata**.

**Passo 3:** Il popup offre due opzioni:

**Prima di eliminare (CONSIGLIATO):**

1. Cliccare **"Esporta prima i log"**  
2. Verrà scaricato il backup CSV  
3. Tornare e ripetere l'operazione di reset

**Eliminazione diretta:**

1. Cliccare **"Elimina tutti i log"** per confermare  
2. Tutti i log verranno cancellati immediatamente

**Passo 4:** Conferma dell'operazione:

✅ **"Tutti i log sono stati eliminati con successo"**

La tabella sarà vuota e ripartirà dal conteggio 1\.

#### **Cosa NON viene cancellato:**

* Database targhe autorizzate  
* Configurazioni sistema  
* Utenti autorizzati

---

## 6\. Controllo Servizio 

Il servizio di rilevamento può essere attivato o disattivato dalla dashboard.

### 6.1 Stato del servizio

Lo stato è visibile sulla dashboard:

* 🟢 **Servizio Attivo** \- Il sistema sta elaborando frame  
* 🔴 **Servizio Disattivato** \- Il sistema è in pausa

### 6.2 Attivare il servizio

**Quando attivare:**

* Inizio giornata lavorativa  
* Dopo manutenzione  
* Quando si desidera iniziare il rilevamento

**Procedura:**

1. Dalla dashboard, cliccare il pulsante verde **"🟢 Attiva Servizio"**  
2. Conferma: *"Servizio attivato\!"*  
3. Il sistema inizierà a processare i frame video

### 6.3 Disattivare il servizio

**Quando disattivare:**

* Fine giornata lavorativa  
* Durante manutenzione targhe  
* Per risparmiare risorse sistema  
* Durante eventi speciali senza controllo accessi

**Procedura:**

1. Dalla dashboard, cliccare il pulsante rosso **"🔴 Disattiva Servizio"**  
2. Conferma: *"Servizio disattivato\!"*  
3. Il sistema smetterà di elaborare frame

💡 **Nota:** Quando disattivato, l'interfaccia web continua a funzionare normalmente. Solo il rilevamento video viene sospeso.

---

## 7\. Domande Frequenti 

### 7.1 Accesso e Autenticazione

**Q: Ho dimenticato la password, come faccio?**

R: Il sistema utilizza Google OAuth, quindi non c'è una password da ricordare. Se non ricordate la password del vostro account Google, usate la procedura di recupero di Google.

---

**Q: Posso accedere con un account non Google?**

R: No, attualmente il sistema supporta solo l'autenticazione tramite account Google. Contattate l'amministratore se necessitate di metodi alternativi.

---

**Q: Posso autorizzare altri utenti?**

R: No, solo l'amministratore di sistema può aggiungere utenti alla whitelist. Inviate una richiesta all'amministratore con l'email da autorizzare.

---

### 7.2 Gestione Targhe

**Q: La targa che ho inserito non viene riconosciuta dal sistema**

R: Verificate:

1. **Formato corretto:** Deve essere AA000AA (es. AB123CD)  
2. **Targa valida:** Controllate che non sia scaduta  
3. **Riavvio sistema:** In rari casi, riavviare il sistema per ricaricare il database  
4. Se il problema persiste, controllate i log per vedere se la targa viene rilevata ma classificata come "non autorizzata"

---

**Q: Posso inserire targhe straniere?**

R: Il sistema è ottimizzato per targhe italiane formato AA000AA. Per targhe di formati diversi, contattare l'amministratore per verifica compatibilità.

---

**Q: Cosa succede se inserisco una targa duplicata?**

R: Il sistema rileverà il duplicato e mostrerà un errore: *"Targa già presente nel database"*. Non verranno create duplicazioni.

---

**Q: Come faccio a vedere quante targhe ho inserito?**

R: Il numero totale è visibile sulla dashboard nel riquadro "Targhe Totali". Per l'elenco completo, andare nella sezione "Targhe".

---

**Q: Posso impostare autorizzazioni con orari specifici?**

R: Attualmente il sistema supporta solo date di scadenza. Per controlli orari, contattare l'amministratore per eventuali personalizzazioni.

---

### 7.3 Log e Monitoraggio

**Q: Il sistema non rileva i veicoli nel video**

R: Possibili cause:

1. **Servizio disattivato:** Verificare che il pulsante "Attiva Servizio" sia verde  
2. **Video non avviato:** L'amministratore deve avviare correttamente il sistema  
3. **Illuminazione scarsa:** Video troppo scuri possono ridurre le detection  
4. **Configurazione:** Contattare l'amministratore per verificare le soglie di confidenza

---

**Q: Perché alcuni accessi hanno confidenza bassa?**

R: La confidenza indica quanto il sistema è sicuro della lettura OCR della targa:

* **0.8-1.0:** Lettura molto affidabile  
* **0.5-0.7:** Lettura discreta (targa leggibile ma non ottimale)  
* **0.2-0.4:** Lettura incerta (condizioni difficili)

Valori bassi possono dipendere da:

* Targa sporca o danneggiata  
* Angolazione sfavorevole  
* Scarsa illuminazione  
* Movimento veloce del veicolo

---

**Q: Cosa significa "Track ID"?**

R: È l'identificativo univoco assegnato dal sistema a ogni veicolo rilevato nel video. Lo stesso veicolo che passa più volte avrà lo stesso Track ID per tutta la durata del tracciamento.

---

**Q: Quanto spazio occupano i log?**

R: Dipende dal traffico. In media:

* 100 accessi/giorno ≈ 10 KB  
* 1000 accessi/giorno ≈ 100 KB  
* I log occupano pochissimo spazio, ma è buona norma esportare e cancellare periodicamente (es. fine anno).

---

**Q: Posso recuperare log cancellati?**

R: No, una volta cancellati i log sono irrecuperabili. **Esportate sempre un backup CSV prima di cancellarli.**

---

### 7.4 Prestazioni e Problemi Tecnici

**Q: L'interfaccia web è lenta**

R: Possibili soluzioni:

1. Aggiornare la pagina (F5)  
2. Svuotare cache browser (Ctrl+Shift+Canc)  
3. Controllare connessione internet  
4. Contattare amministratore se il problema persiste

---

**Q: La pagina non si carica**

R: Verificare:

1. Il server è acceso e funzionante  
2. L'indirizzo URL è corretto  
3. La connessione di rete è attiva  
4. Provare a riavviare il browser  
5. Contattare l'amministratore se il server è offline

---

**Q: I filtri non funzionano**

R: Provare a:

1. Cliccare "Reset" e riapplicare il filtro  
2. Verificare di aver inserito la targa correttamente (maiuscole, senza spazi)  
3. Aggiornare la pagina  
4. Se persiste, segnalare all'amministratore

---

### 7.5 Sicurezza e Privacy

**Q: I miei dati sono al sicuro?**

R: Sì. Il sistema:

* Utilizza autenticazione Google OAuth sicura  
* Memorizza solo dati di accesso veicoli (targhe)  
* Non raccoglie dati personali sensibili  
* I log sono accessibili solo agli utenti autorizzati

---

**Q: Chi può vedere i log degli accessi?**

R: Solo gli utenti autorizzati che hanno effettuato il login possono accedere ai log. Ogni accesso viene tracciato per audit.

---

**Q: Posso vedere chi ha modificato una targa?**

R: Attualmente il sistema non traccia le modifiche per utente. Per questa funzionalità avanzata, contattare l'amministratore.

---

### 7.6 Supporto

**Q: A chi mi devo rivolgere per problemi tecnici?**

R: Contattare l'amministratore di sistema fornendo:

* Descrizione del problema  
* Screenshot dell'errore (se presente)  
* Cosa stavate facendo quando si è verificato  
* Browser e sistema operativo utilizzato

---

**Q: Esiste un numero di supporto?**

R: Contattare l'amministratore per i contatti di supporto specifici della vostra organizzazione.

---

**Q: Come posso suggerire miglioramenti?**

R: Inviare suggerimenti all'amministratore di sistema. Feedback e proposte sono sempre benvenuti per migliorare il servizio.

---

**Versione Manuale:** 1.0  
 **Ultimo Aggiornamento:** Gennaio 2026  
 **Sistema:** Gestione Accessi Veicolari v1.0
