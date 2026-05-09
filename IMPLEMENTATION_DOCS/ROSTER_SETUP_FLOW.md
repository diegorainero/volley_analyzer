# Flusso Roster Setup - Documentazione Completa

## Overview
Questo documento descrive il flusso completo per la creazione di una nuova partita e l'assegnazione del roster di giocatori.

## Flusso Utente

```
1. Clicca "Nuova Partita" (FormationSetupMatches)
   ↓
2. Si apre NewMatchDialog
   ↓
3. Compila i dati della partita e clicca "Salva"
   ↓
4. Partita creata → Signal match_created(match_id) emesso
   ↓
5. FormationSetupComplete._open_roster_setup(match_id) viene chiamato
   ↓
6. Si apre RosterSetupWidget in modalità "Setup per Partita"
   ↓
7. Seleziona i giocatori disponibili per il match
   ↓
8. Imposta numero maglia e ruolo per ogni giocatore
   ↓
9. Clicca "Salva Roster"
   ↓
10. MatchPlayer records creati per ogni giocatore
    ↓
11. Signal roster_completed emesso
    ↓
12. Dialog chiuso, lista match aggiornata
    ↓
13. Formazione automaticamente caricata per il match
```

## File Modificati

### 1. `new_match_dialog.py`
**Modifiche:**
- Signal `match_created(int)` che emette l'ID della partita creata

**Codice relevante:**
```python
match_created = pyqtSignal(int)  # Emette l'ID della nuova partita

def _on_save(self):
    # ... validazione ...
    with self.db.session_scope() as session:
        # Crea il match
        new_match = Match(...)
        session.add(new_match)
        session.flush()
        
        # Emetti il signal con l'ID
        self.match_created.emit(new_match.id)
```

### 2. `roster_setup.py` (Completamente riscritto)

**Funzionalità principali:**

#### Modalità Doppia
1. **Modalità "Selezione Partita"** (quando match_id è None)
   - Mostra lista di partite disponibili
   - Permette di selezionare una partita manualmente

2. **Modalità "Setup per Partita"** (quando match_id è fornito)
   - Apre direttamente la pagina di setup
   - Non consente torna alla lista

#### Layout UI
```
┌─────────────────────────────────────────────────────────────────┐
│                     📋 Roster Setup                             │
├──────────────────────────────┬──────────────────────────────────┤
│    Team A vs Team B (Data)   │                                  │
├──────────────────────────────┴──────────────────────────────────┤
│                                                                  │
│  SINISTRA                          │         DESTRA             │
│  ─────────────────────────────────│─────────────────────────────│
│  Selezione Giocatori              │    Roster Partita           │
│                                   │                              │
│  Squadra: [Team A ▼]              │    ┌────────────────────┐   │
│                                   │    │ Nome    │Mag│Ruolo │   │
│  Giocatori Disponibili:           │    ├────────────────────┤   │
│  ☑ #3 - Mario Rossi              │    │ Mario   │ 3 │ C   │   │
│  ☐ #5 - Luigi Bianchi            │    │ Francesco│12 │ PL  │   │
│  ☑ #12 - Francesco Verdi         │    │ Giovanni│ 8 │ O   │   │
│  ☐ #7 - Giorgio Neri             │    └────────────────────┘   │
│                                   │                              │
│                                   │   ✅ Salva Roster           │
└──────────────────────────────────┴──────────────────────────────┘
```

#### Funzionalità Principali

**1. Caricamento Match**
```python
def _load_match(self, match_id: int):
    # Carica i dati del match
    # Popola il dropdown delle squadre
    # Carica il roster esistente
    # Mostra la pagina di setup
```

**2. Gestione Giocatori**
- **Checkbox per selezione**: Seleziona/deseleziona giocatori dal dropdown team
- **Modifica numero/ruolo**: Dialog per ogni giocatore selezionato
- **Visualizzazione tabella**: Tabella destra mostra i giocatori selezionati con numero e ruolo

**3. Sincronizzazione**
```python
def _sync_roster_with_checkboxes(self):
    # Sincronizza i checkbox con selected_players dict
    # Aggiunge nuovi giocatori checked
    # Rimuove giocatori unchecked
    # Aggiorna la tabella
```

**4. Salvataggio**
```python
def _save_roster(self):
    # Sincronizza con i checkbox
    # Elimina il vecchio roster (MatchPlayer)
    # Crea nuovi MatchPlayer records
    # Emette roster_completed signal
    # Chiude il dialog
```

### 3. `formation_setup_complete.py`

**Modifiche:**
- Aggiunta importazione `RosterSetupWidget`
- Passaggio di riferimento `parent=self` a `FormationSetupMatches`
- Implementazione di `_open_roster_setup(match_id)`

**Flusso:**
```python
def _on_new_match_created(self, match_id: int):
    # Riceve il signal da NewMatchDialog
    self.parent_formation._open_roster_setup(match_id)

def _open_roster_setup(self, match_id: int):
    # Crea dialog con RosterSetupWidget
    dialog = QDialog(self)
    roster_widget = RosterSetupWidget(self.db, match_id=match_id)
    
    # Connette il signal di completamento
    roster_widget.roster_completed.connect(on_roster_completed)
    
    # Quando completato:
    # 1. Aggiorna la lista match
    # 2. Trova il match appena completato
    # 3. Emette match_selected per caricare la formazione
    
    dialog.exec()
```

## Data Model: MatchPlayer

```python
class MatchPlayer(Base):
    __tablename__ = "match_players"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    number = Column(Integer)          # Numero maglia per questo match
    role = Column(String(30))         # Ruolo nel match
    is_libero = Column(Boolean)
    is_starter = Column(Boolean)
```

**Note Importanti:**
- Un player mantiene il suo `id`, `first_name`, `last_name` da Player
- Ma per ogni match può avere un **numero e ruolo diversi**
- Questo permette flessibilità: stesso giocatore, numero diverso per match diversi

## Signals Flow

### NewMatchDialog → FormationSetupMatches
```
NewMatchDialog.match_created(int)
         ↓
FormationSetupMatches._on_new_match_created(match_id)
         ↓
FormationSetupComplete._open_roster_setup(match_id)
```

### RosterSetupWidget → FormationSetupComplete
```
RosterSetupWidget.roster_completed()
         ↓
FormationSetupComplete.on_roster_completed()
         ↓
FormationSetupMatches._load_matches() [ricarica lista]
FormationSetupComplete.match_selected.emit(match)
         ↓
FormationSetupComplete._load_and_show_formation(match)
```

## Casi d'uso

### UC1: Creare una nuova partita con roster
1. Utente clicca "Nuova Partita"
2. Compila il form → clicca "Salva"
3. Si apre RosterSetup per il match appena creato
4. Seleziona i giocatori, imposta numero/ruolo
5. Clicca "Salva Roster"
6. Formazione si apre automaticamente

### UC2: Modificare il roster di una partita esistente
1. Dalla lista match, seleziona un match (singolo click)
2. *(Questa feature potrebbe essere aggiunta in futuro con un pulsante "Modifica Roster")*
3. RosterSetup si apre per quel match
4. I giocatori esistenti sono già selezionati
5. Puoi aggiungere/rimuovere giocatori
6. Clicca "Salva Roster"

### UC3: Visualizzare formazione dopo roster setup
1. Dopo il salvataggio del roster
2. La lista match viene aggiornata
3. La formazione del match si apre automaticamente

## Implementazione Dettagli Tecnici

### RosterSetupWidget.__init__
```python
def __init__(
    self, 
    db_manager: DatabaseManager, 
    match_id: int | None = None, 
    parent=None
):
    # Se match_id è None → modalità "selezione partita"
    # Se match_id è fornito → modalità "setup per partita"
```

### QStackedWidget Pages
- **Index 0**: Match selection page (solo se match_id è None)
- **Index 1**: Roster setup page (visualizzata automaticamente se match_id è fornito)

### Persistenza Dati
- Quando si apre RosterSetup per un match con roster già esistente:
  1. `_load_match()` legge i MatchPlayer record
  2. Popola `self.selected_players` dict
  3. I checkbox sono pre-selezionati
  4. La tabella mostra i giocatori già nel roster
  5. Modifiche sovrascrivono il vecchio roster al salvataggio

## Testing

### Test Manuale
1. **Crea nuova partita**
   - Clicca "Nuova Partita" → Compila dati → Salva
   - Verifica che RosterSetup si apre automaticamente

2. **Seleziona giocatori**
   - Seleziona team dal dropdown
   - Checkare alcuni giocatori
   - Verifica che compaiono nella tabella destra

3. **Modifica numero/ruolo**
   - Clicca "Modifica" su un giocatore
   - Cambia numero (es. 3 → 5) e ruolo
   - Clicca OK → Verifica nella tabella

4. **Salva roster**
   - Seleziona almeno un giocatore
   - Clicca "Salva Roster"
   - Verifica messaggio di successo
   - Verifica che dialog si chiude
   - Verifica che formazione si apre

5. **Ricarica match con roster**
   - Dalla lista match, seleziona il match appena creato
   - Double-click per aprire formazione
   - Verifica che i giocatori del roster sono visibili

## Possibili Miglioramenti Futuri

1. **Modifica Roster Rapida**: Bottone "Modifica Roster" nella lista match
2. **Validazione**: Minimo/massimo giocatori per match
3. **Template Roster**: Salva/carica template per squadra
4. **Bulk Edit**: Modifica numero/ruolo per più giocatori
5. **Libero Specifico**: UI dedicata per gestire il libero
6. **Storico**: Versioning dei roster per ogni match
