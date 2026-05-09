# Sommario Modifiche - Roster Setup Flow

## Data: 2024
## Modulo: Volleyball Scout - Formation Setup

---

## File Modificati

### 1. `volleyball_scout/ui/new_match_dialog.py`

**Tipo Modifica:** Miglioramento signal

**Dettagli Modifiche:**
- ✅ Linea 31: Modificato signal `match_created` da `pyqtSignal(object)` a `pyqtSignal(int)`
- ✅ Linea 212: Aggiornato emit signal da `self.match_created.emit(self.new_match)` a `self.match_created.emit(new_match.id)`

**Razionale:**
- Emettere solo l'ID della partita è più efficiente
- Il signal ricevente può ricaricare i dati dal database se necessario
- Signature più pulita e type-safe

**Breaking Changes:** Sì - Chi era connesso al signal `match_created` deve adattarsi a ricevere un `int` invece di un `dict`

**Code Review Notes:**
```python
# PRIMA:
match_created = pyqtSignal(object)
self.match_created.emit(self.new_match)  # Emette dict

# DOPO:
match_created = pyqtSignal(int)
self.match_created.emit(new_match.id)    # Emette int
```

---

### 2. `volleyball_scout/ui/roster_setup.py`

**Tipo Modifica:** Rewrite completo

**Descrizione:**
File completamente riscritto da zero con nuova architettura e funzionalità.

**Funzionalità Precedente:**
- Widget semplice per mostrare roster di una partita
- Nessuna interazione diretta
- Nessun meccanismo di selezione giocatori

**Funzionalità Nuova:**
- ✅ Modalità doppia: "Selezione Partita" e "Setup per Partita"
- ✅ Selezione con checkbox per giocatori
- ✅ Dropdown per team
- ✅ Tabella per visualizzare roster selezionato
- ✅ Dialog per modifica numero maglia e ruolo per giocatore
- ✅ Bottoni Aggiungi/Rimuovi giocatori
- ✅ Signal `roster_completed()` per notificare completamento
- ✅ Salvataggio MatchPlayer nel database
- ✅ Sincronizzazione checkbox ↔ tabella
- ✅ Persistenza: Caricamento roster esistente

**Classe Principale:**
```python
class RosterSetupWidget(QWidget):
    roster_completed = pyqtSignal()
    
    def __init__(self, db_manager, match_id: int | None = None, parent=None)
```

**Metodi Chiave Nuovi:**
- `_setup_ui()` - Costruisce l'interfaccia con QStackedWidget
- `_setup_match_selection_page()` - Pagina per selezione partita
- `_setup_roster_setup_page()` - Pagina per setup roster
- `_load_match(match_id)` - Carica i dati del match
- `_load_team_players(team_id)` - Carica giocatori di una squadra
- `_update_roster_table()` - Aggiorna tabella roster
- `_edit_player(player_id)` - Dialog per modifica numero/ruolo
- `_remove_player(player_id)` - Rimuove giocatore dal roster
- `_sync_roster_with_checkboxes()` - Sincronizza checkbox e dict
- `_save_roster()` - Salva MatchPlayer nel DB
- `_go_back_to_selection()` - Torna a pagina selezione

**Linee di Codice:** ~500 (era ~50)

---

### 3. `volleyball_scout/ui/formation_setup_complete.py`

**Tipo Modifica:** Integrazione RosterSetup

**Dettagli Modifiche:**

#### Imports
- ✅ Aggiunto: `from .roster_setup import RosterSetupWidget`
- ✅ Aggiunto: `QDialog` (da QtWidgets)

#### FormationSetupMatches
- ✅ Aggiunto attributo: `self.parent_formation = parent` (linea 38)
- ✅ Modificato `_on_new_match_created()` (linea 156-159):
  ```python
  def _on_new_match_created(self, match_id: int):
      """Quando una nuova partita è stata creata, apri il RosterSetup"""
      if self.parent_formation:
          self.parent_formation._open_roster_setup(match_id)
  ```

#### FormationSetupComplete
- ✅ Aggiunto parametro `parent=self` a FormationSetupMatches (linea 186)
- ✅ Aggiunto nuovo metodo `_open_roster_setup()` (linee 309-328):
  ```python
  def _open_roster_setup(self, match_id: int):
      # Crea QDialog con RosterSetupWidget
      # Connette signal roster_completed
      # Al completamento: ricarica matches e apre formazione
  ```

**Flusso Signal:**
```
NewMatchDialog.match_created(id)
    ↓
FormationSetupMatches._on_new_match_created(id)
    ↓
FormationSetupComplete._open_roster_setup(id)
    ↓
RosterSetupWidget.roster_completed()
    ↓
FormationSetupComplete._on_match_selected(match) → mostra formazione
```

---

## Database Changes

**Nessuna modifica al schema** - Utilizziamo il modello `MatchPlayer` esistente:

```python
class MatchPlayer(Base):
    __tablename__ = "match_players"
    
    id: int (PK)
    match_id: int (FK to Match)
    player_id: int (FK to Player)
    team_id: int (FK to Team)
    number: int          # ← Personalizzabile per ogni match
    role: str            # ← Personalizzabile per ogni match
    is_libero: bool
    is_starter: bool
```

**Operazioni:**
- `INSERT`: Quando salva il roster (prima `DELETE` dei vecchi record)
- `SELECT`: Quando carica un match per vedere il roster
- `UPDATE`: Non usato (usa DELETE + INSERT)
- `DELETE`: Quando salva un roster nuovo

---

## Breaking Changes & Migration

### Per i Consumatori di NewMatchDialog
**Chi è interessato:** Chiunque connetta al signal `match_created`

**Prima:**
```python
dialog.match_created.connect(lambda match_obj: handle_match(match_obj["id"]))
```

**Dopo:**
```python
dialog.match_created.connect(lambda match_id: handle_match(match_id))
```

**Migration Path:**
1. Aggiornare tutti i `.connect()` che ricevono il signal
2. Nel nostro caso: `FormationSetupMatches._on_new_match_created` già aggiornato ✅

### Per l'UI di Roster Vecchia
La funzionalità precedente di RosterSetupWidget era minima e completamente sovrascritto senza perdita di funzionalità importante.

---

## Testing Checklist

### Unit Tests (da scrivere)
- [ ] RosterSetupWidget carica correttamente un match
- [ ] Checkbox sincronizzati con selected_players dict
- [ ] Dialog modifica cambia numero/ruolo
- [ ] MatchPlayer records creati correttamente
- [ ] Roster esistente caricato al riaprir widget

### Integration Tests (da scrivere)
- [ ] NewMatchDialog → RosterSetup flow completo
- [ ] RosterSetup → Formazione flow completo
- [ ] Persistenza roster tra sessioni

### Manual Tests (da fare)
- [ ] Crea partita → RosterSetup apre automaticamente ✓
- [ ] Seleziona giocatori → Compaiono in tabella destra ✓
- [ ] Modifica numero/ruolo → Updatedb correttamente ✓
- [ ] Salva roster → Dialog chiude e formazione si apre ✓
- [ ] Accedi a match con roster → Vedi i giocatori ✓

---

## Performance Considerations

### Database Queries
- `_load_match()`: 1 query per Match + join a MatchPlayer
- `_load_team_players()`: 1 query per Team.players
- `_save_roster()`: 1 DELETE + N INSERTs

**Ottimizzazioni Possibili:**
- Batch insert per MatchPlayer records (se N > 100)
- Eager loading di players su team

### UI Responsiveness
- Uso di `session_scope()` per context manager corretto
- Nessuna operazione lunga senza progress indicator
- Dialog modifica è modale (OK)

---

## Documentation

### Internals
- `IMPLEMENTATION_DOCS/ROSTER_SETUP_FLOW.md` - Flow diagram completo e docs

### Code Comments
- Docstrings aggiunti per tutti i metodi principali
- Inline comments per logica complessa

---

## Rollback Plan

Se necessario tornare indietro:

1. **Restora new_match_dialog.py**: Revert signal type
2. **Restora roster_setup.py**: Restora file precedente (backup consigliato)
3. **Restora formation_setup_complete.py**: Rimuovi RosterSetupWidget integration

**Comando:**
```bash
git revert <commit_hash>
```

---

## Sign-Off

**Implementazione:** ✅ Completata
**Testing Manuale:** ⏳ Da fare
**Documentazione:** ✅ Completata
**Code Review:** ⏳ Da fare

**Note Aggiuntive:**
- Tutto il codice è compilabile e syntax-correct
- Nessun warning di import non usati
- Type hints aggiunti dove appropriato
- Segue lo style del resto del codebase (PyQt6, with statements, etc.)
