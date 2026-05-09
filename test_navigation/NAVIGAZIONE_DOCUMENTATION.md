# 🏐 Formation Setup - Documentazione Navigazione

## Struttura Generale

L'app utilizza un **QStackedWidget** per navigare tra due schermate principali:

```
FormationSetupComplete (Main Widget)
├── QStackedWidget
│   ├── Index 0: FormationSetupMatches (Lista Partite)
│   └── Index 1: FormationPanel (Dettagli Formazione)
```

## Flusso di Navigazione

### 1. **Avvio Iniziale**
- L'app mostra la lista di partite (FormationSetupMatches)
- QStackedWidget è impostato a Index 0
- L'utente vede la tabella con le partite in corso

```
┌─────────────────────────────────┐
│ 🏐 Selezione Partita per Formazione │
├─────────────────────────────────┤
│ Home      │ Away      │ Data   │ Status │
├─────────────────────────────────┤
│ Team A    │ Team B    │ date   │ draft  │
│ Team C    │ Team D    │ date   │ in_... │
│                               │
│ [🔄 Aggiorna]                    │
└─────────────────────────────────┘
```

### 2. **Selezione Partita (Double-Click)**
```
User double-clicks on a match in the table
        ↓
FormationSetupMatches._on_match_double_clicked()
        ↓
Emits: match_selected(match_dict)
        ↓
FormationSetupComplete._on_match_selected(match)
        ↓
_load_and_show_formation(match)
```

### 3. **Caricamento Formazione**
```
_load_and_show_formation():
    1. Query database per home_team e away_team
    2. Carica lista giocatori per team
    3. Crea FormationPanel con dati
    4. Connette signal back_requested → _on_back_to_matches
    5. Aggiunge FormationPanel a QStackedWidget (index 1)
    6. setCurrentIndex(1) → Mostra FormationPanel
```

### 4. **Modifica Formazione**
```
┌──────────────────────────────────────────┐
│ Inserisci la Formazione Iniziale        │
├──────────────────────────────────────────┤
│ Team A              │ Team B             │
│ [Formazione 1]      │ [Formazione 2]     │
│ [Giocatori]         │ [Giocatori]        │
│ [Libero]            │ [Libero]           │
├──────────────────────────────────────────┤
│ [← Torna] [Reset] [Conferma Formazione]  │
└──────────────────────────────────────────┘
```

### 5. **Torna alla Lista**
```
User clicks "← Torna Indietro" button
        ↓
Emits: back_requested signal
        ↓
FormationSetupComplete._on_back_to_matches()
        ↓
stacked_widget.setCurrentIndex(0) → Mostra lista
        ↓
matches_widget._load_matches() → Aggiorna la lista
```

## Componenti Principali

### FormationSetupMatches (Index 0)
**Responsabilità:**
- Mostrare lista di partite (status: draft o in_progress)
- Gestire double-click per selezionare una partita
- Emettere segnale `match_selected` con i dati del match

**Attributi:**
- `db_manager`: Accesso al database
- `matches`: Lista di partite caricate
- `matches_table`: Tabella Qt per visualizzare i dati

**Segnali:**
- `match_selected(dict)`: Emesso quando l'utente seleziona una partita

### FormationSetupComplete (Main Widget)
**Responsabilità:**
- Gestire QStackedWidget
- Coordinare navigazione tra lista e formazione
- Caricamento dati dal database
- Gestione ciclo di vita dei widget

**Attributi:**
- `stacked_widget`: QStackedWidget per navigazione
- `matches_widget`: Istanza di FormationSetupMatches
- `current_match`: Match attualmente in modifica
- `current_formation_panel`: FormationPanel attualmente visibile

**Metodi pubblici:**
- `_on_match_selected(match)`: Riceve segnale dal matches_widget
- `_load_and_show_formation(match)`: Carica e mostra la formazione
- `_on_back_to_matches()`: Torna alla lista di match

### FormationPanel (Index 1)
**Responsabilità:**
- Mostrare layout per inserire la formazione
- Visualizzare due squadre affiancate
- Gestire drag-drop dei giocatori nei slot
- Confermare la formazione

**Segnali:**
- `formation_confirmed(dict)`: Emesso quando la formazione è confermata
- `back_requested()`: Emesso quando l'utente clicca il pulsante "Indietro"

## Gestione dello Stato

### Durante la Navigazione Match → Formazione:
1. `current_match` è impostato
2. Query DB per caricamento team e giocatori
3. FormationPanel è creato con dati freschi
4. Signal `back_requested` è connesso
5. Widget è aggiunto a QStackedWidget
6. Index cambia a 1

### Durante la Navigazione Formazione → Match:
1. QStackedWidget torna a index 0
2. `matches_widget._load_matches()` aggiorna la lista
3. FormationPanel vecchio rimane in memoria (buono per rifiuto modifiche)

## Dettagli di Implementazione

### Creazione FormationPanel Dinamica
```python
# Rimuove la vecchia FormationPanel se esiste
if self.current_formation_panel is not None:
    widget = self.stacked_widget.widget(1)
    if widget:
        self.stacked_widget.removeWidget(widget)
        widget.deleteLater()

# Crea la nuova FormationPanel
formation_panel = FormationPanel(teams, players_by_team, ...)
formation_panel.match_id = match["id"]

# Connette il segnale di ritorno
formation_panel.back_requested.connect(self._on_back_to_matches)

# Aggiunge al stacked widget
self.stacked_widget.addWidget(formation_panel)
self.stacked_widget.setCurrentIndex(1)
```

### Gestione Database
```python
with self.db.session_scope() as session:
    # Carica squadre
    home_team = session.query(Team).filter_by(id=...).first()
    
    # Carica giocatori per squadra
    players = session.query(Player).filter_by(team_id=...).all()
    
    # Prepara dati
    teams.append({"id": ..., "name": ...})
    players_by_team[team_id] = [...]
```

## Testing

Per testare la navigazione, esegui:
```bash
python3 test_navigation/test_formation_navigation.py
```

Il test verifica:
- ✓ Presenza di QStackedWidget
- ✓ FormationSetupMatches su Index 0
- ✓ Placeholder su Index 1
- ✓ Index corrente è 0 all'inizio
- ✓ Signal match_selected è connesso
- ✓ FormationPanel ha segnale back_requested
- ✓ Metodo _on_back_to_matches esiste
- ✓ Lista di match è caricata

## Note Importanti

1. **Caricamento Lazy**: FormationPanel è creato solo quando l'utente seleziona una partita
2. **Cleanup**: La vecchia FormationPanel è rimossa e liberata dalla memoria quando se ne crea una nuova
3. **Segnali**: Tutti i segnali usano PyQt6 `pyqtSignal()` con emit corretti
4. **Database**: Tutte le query usano context manager `session_scope()` per evitare leak
5. **Error Handling**: Implementato try/except con logging

## Workflow Completo

```
┌─────────────────────────────────────────┐
│ Avvio App                              │
│ Index = 0 (Lista Match)                │
└──────────────┬──────────────────────────┘
               │
               │ User Double-Click Match
               ↓
┌─────────────────────────────────────────┐
│ _on_match_selected(match)               │
│ Carica dati dal DB                      │
│ Crea FormationPanel                     │
│ Connette back_requested signal          │
│ Aggiunge a QStackedWidget (index 1)     │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│ setCurrentIndex(1)                      │
│ Mostra FormationPanel                   │
└──────────────┬──────────────────────────┘
               │
               │ User modifica formazione
               │ e clicca "Indietro"
               ↓
┌─────────────────────────────────────────┐
│ _on_back_to_matches()                   │
│ setCurrentIndex(0)                      │
│ Aggiorna lista match                    │
└──────────────┬──────────────────────────┘
               │
               ↓ (Torna allo stato iniziale)
┌─────────────────────────────────────────┐
│ Index = 0 (Lista Match)                │
└─────────────────────────────────────────┘
```

## Possibili Estensioni Future

1. **Salvamento automatico**: Salvare la formazione mentre viene modificata
2. **Validazione**: Controllare che la formazione sia completa prima di permettere la conferma
3. **Cronologia**: Mostrare la formazione precedente per il match
4. **Anteprima**: Preview della formazione prima di confermare
5. **Template**: Usare template di formazioni precedenti
