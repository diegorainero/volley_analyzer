# 🏐 Gestione Squadre - Volleyball Scout

## Panoramica

La sezione **Gestione Squadre** permette di gestire in modo completo le informazioni delle squadre di pallavolo, inclusi i dati anagrafici delle giocatrici.

## Accesso

### Dalla finestra Scout principale
1. Apri l'applicazione Volleyball Scout
2. Nel pannello sinistro, clicca su **"Gestione Squadre"**
3. Si aprirà la finestra di gestione squadre

### Avvio diretto
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
source venv/bin/activate
python3 -m volleyball_scout.ui.main_window
```

## Funzionalità

### 1. Gestione Squadre

#### Creazione di una nuova squadra
1. Clicca sul pulsante **"Nuova Squadra"** nel pannello sinistro
2. Inserisci il nome della squadra
3. La squadra verrà creata e selezionata automaticamente

#### Modifica dettagli squadra
1. Seleziona una squadra dalla lista a sinistra
2. Nel pannello destro, modifica i seguenti campi:
   - **Nome Squadra**: Il nome ufficiale della squadra
   - **Impianto di Gioco**: La palestra/stadio dove gioca la squadra
   - **Logo**: Path o URL del logo della squadra (clicca "Scegli Logo" per selezionare un file)
3. Clicca **"Salva Dettagli Squadra"** per applicare le modifiche

#### Eliminazione di una squadra
1. Seleziona la squadra che vuoi eliminare
2. Clicca **"Elimina Squadra Selezionata"**
3. Conferma l'eliminazione (verranno eliminate anche tutte le giocatrici)

### 2. Gestione Giocatrici

#### Aggiunta di una giocatrice
1. Assicurati di avere una squadra selezionata
2. Clicca **"Aggiungi Giocatrice"**
3. Compila il modulo con i seguenti dati:
   - **Nome**: Nome della giocatrice
   - **Cognome**: Cognome della giocatrice
   - **Ruolo**: Ruolo in squadra (es. Palleggiatore, Centrale, Opposto, Schiacciatrice, Libero)
   - **Numero**: Numero di maglia (1-99)
   - **Capitano**: Spunta se è la capitana della squadra
   - **Data di nascita**: Seleziona dal calendario
   - **Foto**: Path o URL della foto della giocatrice (clicca "Scegli foto" per selezionare un file)
4. Clicca **"Salva"** per aggiungere la giocatrice

#### Modifica di una giocatrice
1. Seleziona una giocatrice dalla lista
2. Clicca **"Modifica Giocatrice Selezionata"**

### 3. Inserimento Formazione (Nuovo!)

Dopo aver impostato il roster per un match, il sistema richiede l'inserimento della formazione iniziale per il set.

1. **Selezione Titolari**: Scegli esattamente 6 giocatori titolari dalla lista dei convocati.
2. **Selezione Libero**: Scegli esattamente 1 libero tra i giocatori disponibili.
3. **Conferma**: Clicca su **"Conferma Formazione"** per salvare i dati nel database (campi `is_starter` e `is_libero`) e procedere allo scouting.

> **Nota**: Il sistema valida che siano selezionati esattamente 6 titolari e 1 libero prima di permettere il proseguimento.
3. Modifica i dati nel modulo
4. Clicca **"Salva"** per applicare le modifiche

#### Eliminazione di una giocatrice
1. Seleziona una giocatrice dalla lista
2. Clicca **"Elimina Giocatrice Selezionata"**
3. Conferma l'eliminazione

## Campi Disponibili

### Squadra
| Campo | Tipo | Obbligatorio | Note |
|-------|------|--------------|------|
| Nome | Testo | ✅ | Nome univoco della squadra |
| Impianto di Gioco | Testo | ❌ | Palestra o stadio della squadra |
| Logo | File | ❌ | Immagine del logo (PNG, JPG, GIF) |

### Giocatrice
| Campo | Tipo | Obbligatorio | Note |
|-------|------|--------------|------|
| Nome | Testo | ❌ | Nome proprio |
| Cognome | Testo | ✅ | Cognome |
| Ruolo | Testo | ❌ | Ruolo nel team (es. Palleggiatore, Centrale, etc.) |
| Numero | Numero | ✅ | Numero di maglia (1-99) |
| Capitano | Booleano | ❌ | Spunta se capitana |
| Data di nascita | Data | ❌ | Data di nascita della giocatrice |
| Foto | File | ❌ | Foto della giocatrice |

## Database

### Ubicazione
- **SQLite locale**: `~/.volleyball_scout/data/scout.db`
- **PostgreSQL (cloud)**: Configurabile via `DATABASE_URL`

### Tabelle
- **teams**: Informazioni squadre
- **players**: Informazioni giocatrici

### Reset del database
Se vuoi cancellare tutti i dati e ricominciare da zero:

```bash
rm -f ~/.volleyball_scout/data/scout.db
```

Il database verrà ricreato al prossimo avvio dell'applicazione.

## Esempi di utilizzo

### Creare una squadra con 12 giocatrici
1. Clicca "Nuova Squadra" e inserisci il nome (es. "Cuneo Volley")
2. Compila i dettagli (impianto, logo)
3. Clicca "Salva Dettagli Squadra"
4. Per ogni giocatrice:
   - Clicca "Aggiungi Giocatrice"
   - Inserisci i dati
   - Clicca "Salva"

### Esportare dati tramite Python
```python
from volleyball_scout.core.database import get_db
from volleyball_scout.core.models import Team

db = get_db()
with db.session_scope() as session:
    team = session.query(Team).filter_by(name="Cuneo Volley").first()
    if team:
        for player in team.players:
            print(f"#{player.number} {player.full_name} ({player.role})")
```

## Note Importanti

- ✅ **Backup**: Ricorda di fare backup del file `scout.db` periodicamente
- 🔐 **Univocità**: I nomi delle squadre devono essere unici
- 🖼️ **File**: Le foto e i logo possono essere locali (path relativo/assoluto) o URL
- 📱 **Dati sincronizzati**: Tutti i dati sono sincronizzati in tempo reale con il database

## Risoluzione dei Problemi

### Errore: "Nessuna squadra selezionata"
Soluzione: Seleziona una squadra dalla lista a sinistra prima di aggiungere giocatrici

### Errore: "Squadra non trovata nel database"
Soluzione: Ricarica l'applicazione. Se il problema persiste, contatta lo sviluppatore

### Le modifiche non vengono salvate
Soluzione: Assicurati di cliccare **"Salva Dettagli Squadra"** o **"Salva"** nel form delle giocatrici

## Contatti e Supporto

Per segnalare bug o richieste di miglioramento, contatta lo sviluppatore del progetto.
