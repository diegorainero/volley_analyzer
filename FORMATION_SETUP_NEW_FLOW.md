# 🏐 Formation Setup - Nuovo Flusso

## Panoramica

Formation Setup è stato aggiornato per **mostrare prima l'elenco dei match non completati**, poi permettere la selezione per accedere alla formazione.

## Flusso Utente

### Step 1: Click su "🏐 Formation Setup"

```
User clicks "🏐 Formation Setup" in the menu
                    ↓
         _on_section_selected("formation")
                    ↓
           _refresh_formation_panel()
                    ↓
      Queries DB for incomplete matches
      (status = "draft" or "in_progress")
                    ↓
       Creates Match Selector Widget
```

### Step 2: Visualizzazione Lista Match

Quando entri in Formation Setup, vedi:

```
┌─────────────────────────────────────────────────────────────────┐
│  Seleziona una Partita per Inserire la Formazione              │
├──────────────────┬──────────────────┬──────────────┬────────────┤
│ Home             │ Away             │ Data         │ Status     │
├──────────────────┼──────────────────┼──────────────┼────────────┤
│ Genova Volley    │ Piacenza Volley  │ 2024-01-15   │ draft      │
│ Modena Volley    │ Monza Volley     │ 2024-01-16   │ in_progress│
│ Trento Volley    │ Padova Volley    │ 2024-01-17   │ draft      │
└──────────────────┴──────────────────┴──────────────┴────────────┘
│ 📋 Apri Formazione │  ← Button
```

### Step 3: Selezione Match

L'utente può:
- **Double-click su una riga**: Apre immediatamente la FormationPanel per quella partita
- **Selezionare una riga e cliccare il bottone "Apri Formazione"**

### Step 4: Visualizzazione Formazione

Una volta selezionato un match:

```
Apri Formazione (match_id=5)
         ↓
_open_formation_for_match(match)
         ↓
Carica le due squadre del match dal DB
         ↓
Carica i giocatori di entrambe le squadre
         ↓
Crea FormationPanel(teams, players_by_team)
         ↓
Salva match_id nel widget (formation_widget.match_id = 5)
         ↓
Mostra FormationPanel con squadre e giocatori
```

Ora vedi il vero Formation Setup:

```
┌──────────────────────────────────────────────────────────────────┐
│  Inserisci la Formazione Iniziale                               │
│  Metodo di gioco: -                                             │
├──────────────────────────┬──────────────────────────────────────┤
│ Squadra: Genova Volley   │ Squadra: Piacenza Volley           │
│                          │                                      │
│ [1] Rossi (Palleggiatore)│ [1] Neri (Palleggiatore)          │
│ [2] Bianchi (Schiacciatore)│ [2] Blu (Schiacciatore)          │
│ [3] Verdi (Centrale)     │ [3] Gialli (Centrale)             │
│ ... altri giocatori      │ ... altri giocatori                │
│                          │                                      │
│ [SLOT FORMAZIONE]        │ [SLOT FORMAZIONE]                  │
│ - Drag & drop giocatori  │ - Drag & drop giocatori            │
│ - Imposta titolari       │ - Imposta titolari                 │
│                          │                                      │
│ 🔄 Ruota                 │ 🔄 Ruota                           │
│                          │                                      │
│ ✅ Conferma Formazione   │                                     │
└──────────────────────────┴──────────────────────────────────────┘
```

## Implementazione

### File Modificati

- `volleyball_scout/ui/app.py` (linee 424-620)
  - `_refresh_formation_panel()`: Carica lista match non completati
  - `_create_match_selector_widget()`: Crea la tabella con i match
  - `_open_formation_for_match()`: Apre FormationPanel per un match

### Metodi Aggiunti

#### 1. `_refresh_formation_panel()`
- **Purpose**: Carica i match non completati dal database
- **Query**: `Match.status.in_(["draft", "in_progress"])`
- **Return**: Match selector widget o placeholder se nessun match

#### 2. `_create_match_selector_widget(matches)`
- **Purpose**: Crea il widget con la tabella dei match
- **Columns**: Home, Away, Data, Status
- **Features**:
  - Double-click per aprire formazione
  - Bottone "Apri Formazione" per aprire match selezionato

#### 3. `_open_formation_for_match(match)`
- **Purpose**: Apre FormationPanel per un match specifico
- **Logic**:
  1. Carica home_team e away_team dal DB
  2. Carica tutti i giocatori di entrambe le squadre
  3. Crea FormationPanel con i dati
  4. Salva match_id nel widget per successivo salvataggio

## Database Query

```python
# Carica match non completati
matches_data = (
    session.query(Match)
    .filter(Match.status.in_(["draft", "in_progress"]))
    .all()
)

# Per ogni match carica le squadre
home_team = session.query(Team).filter_by(id=match.home_team_id).first()
away_team = session.query(Team).filter_by(id=match.away_team_id).first()

# Per ogni squadra carica i giocatori
players = session.query(Player).filter_by(team_id=team.id).all()
```

## Comportamento

### Caso 1: Ci sono match non completati
→ Mostra tabella con elenco dei match
→ Utente seleziona uno
→ Si apre FormationPanel per quel match

### Caso 2: Nessun match nel database
→ Mostra placeholder:
  ```
  🏐 Formation Setup
  (No incomplete matches in database)
  
  Crea una partita dalla sezione Matches
  ```

### Caso 3: Match selezionato non ha squadre
→ Mostra placeholder:
  ```
  🏐 Formation Setup
  (No teams found for match)
  ```

## Integrazione con FormationPanel

Quando si apre FormationPanel, il widget memorizza il `match_id`:

```python
formation_widget = FormationPanel(teams, players_by_team)
formation_widget.match_id = match["id"]  # Per successivo salvataggio
```

Questo permette a FormationPanel di salvare la formazione associandola al match corretto.

## Vantaggi del Nuovo Flusso

✅ **Usabilità**: L'utente vede prima i match disponibili
✅ **Chiarezza**: È evidente quale partita sta elaborando
✅ **Integrità Dati**: Ogni formazione è associata a un match specifico
✅ **Navigazione**: Facile tornare indietro per cambiare match (click su Formation di nuovo)
✅ **Scalabilità**: Supporta molti match in un elenco scrollabile

## Prossimi Step

1. **Salvataggio Formazione**: Quando l'utente clicca "Conferma Formazione" in FormationPanel, la formazione dovrebbe essere salvata e associata al match

2. **Modifica Formazione**: Se un match ha già una formazione salvata, dovrebbe permettere di modificarla

3. **Indicatori Visivi**: Nel match selector, mostrare se un match ha già una formazione salvata

4. **Feedback Utente**: Mostrare messaggi di successo quando una formazione viene salvata

## Testing

### Test 1: Lista Match
1. Vai a "🏐 Formation Setup"
2. Verifica che appaia una tabella con i match non completati
3. Controlla che colonne siano: Home, Away, Data, Status

### Test 2: Apertura Formazione
1. Double-click su un match
2. Verifica che si apra FormationPanel con le due squadre del match
3. Controlla che i giocatori siano carichi correttamente

### Test 3: Selezione e Bottone
1. Seleziona una riga nella tabella
2. Clicca il bottone "Apri Formazione"
3. Verifica che si apra FormationPanel

### Test 4: Placeholder
1. Se nessun match esiste, verifica che appaia il placeholder corretto
2. Se un match non ha squadre, verifica il messaggio di errore

---

**Status**: ✅ IMPLEMENTATO
**Version**: 2.0 (con match selector)
**Date**: 2024
