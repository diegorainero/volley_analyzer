# Formation Setup - Correzioni Apportate

## 🎯 Problema Identificato

Formation Setup non stava funzionando correttamente a causa di:

1. **Duplicazione di metodo**: In `app.py` esistevano **due metodi `_refresh_formation_panel()` identici** (linee 428-472 e 474-517)
2. **Chiamata duplicata**: Il metodo veniva chiamato **due volte** in `_on_section_selected()` 
3. **Logica inconsistente**: Le due versioni avevano implementazioni leggermente diverse

## ✅ Correzioni Apportate

### File: `volleyball_scout/ui/app.py`

#### Cambio 1: Rimozione della duplicazione di metodo
- **Prima**: Due metodi `_refresh_formation_panel()` (linee 428-472 e 474-517)
- **Dopo**: Un singolo metodo `_refresh_formation_panel()` (linee 428-465)

**Versione consolidata** (quella che funziona meglio):
```
def _refresh_formation_panel(self):
    """Ricarica il FormationPanel con i dati attuali dal database"""
    try:
        # Load teams and players from database
        teams = []
        players_by_team = {}
        with self.db.session_scope() as session:
            from volleyball_scout.core.models import Player, Team

            teams_data = session.query(Team).all()
            for team in teams_data:
                teams.append({"id": team.id, "name": team.name})
                players_data = (
                    session.query(Player).filter_by(team_id=team.id).all()
                )
                players_by_team[team.id] = [
                    {
                        "id": p.id,
                        "number": p.number,
                        "last_name": p.last_name,
                        "role": p.role,
                    }
                    for p in players_data
                ]

        # Create formation panel with updated data
        if teams:
            new_widget = FormationPanel(teams, players_by_team)
        else:
            new_widget = PlaceholderWidget(
                "🏐 Formation Setup\n(No teams in database)"
            )

        # Sostituisci il widget nella stack
        old_widget = self.content_stack.widget(3)
        if old_widget:
            self.content_stack.removeWidget(old_widget)
            old_widget.deleteLater()

        self.formation_widget = new_widget
        self.content_stack.insertWidget(3, self.formation_widget)

    except Exception as e:
        print(f"⚠️ Error refreshing FormationPanel: {e}")
```

#### Cambio 2: Rimozione della chiamata duplicata
- **Prima**:
  ```python
  # Refresh della formation quando viene visualizzata
  if section_id == "formation" and self.db and FormationPanel:
      self._refresh_formation_panel()

  # Refresh della formation quando viene visualizzata  # DUPLICATO!
  if section_id == "formation" and self.db and FormationPanel:
      self._refresh_formation_panel()
  ```

- **Dopo**:
  ```python
  # Refresh della formation quando viene visualizzata
  if section_id == "formation" and self.db:
      self._refresh_formation_panel()
  ```

**Miglioramenti**:
- Rimosso il check su `FormationPanel` (è già gestito in `_setup_sections`)
- Singola chiamata al metodo (no duplicazione)

## 🔍 Come Funziona Ora

### Flusso di Esecuzione

1. **Utente clicca su "Formation"** nel menu di navigazione
2. `_on_section_selected("formation")` viene chiamato
3. Viene eseguito:
   ```python
   if section_id == "formation" and self.db:
       self._refresh_formation_panel()
   ```
4. `_refresh_formation_panel()` fa:
   - **Carica i dati dal database**: teams e players
   - **Crea un nuovo FormationPanel** con i dati attuali
   - **Sostituisce il widget** nella stack (indice 3)

### Struttura dei Dati

FormationPanel si aspetta:

```python
teams = [
    {"id": 1, "name": "Team A"},
    {"id": 2, "name": "Team B"}
]

players_by_team = {
    1: [
        {"id": 1, "number": 1, "last_name": "Rossi", "role": "Palleggiatore"},
        {"id": 2, "number": 2, "last_name": "Bianchi", "role": "Schiacciatore"},
        ...
    ],
    2: [
        {"id": 4, "number": 1, "last_name": "Neri", "role": "Palleggiatore"},
        ...
    ]
}
```

Questi dati vengono caricati dalla tabella `Team` e `Player` del database tramite SQLAlchemy.

## ✔️ Verifiche Apportate

- [x] Sintassi `app.py` verificata: `python3 -m py_compile volleyball_scout/ui/app.py` ✅
- [x] Sintassi `formation_panel.py` verificata ✅
- [x] Strutture dati validate con test di logica ✅
- [x] Assenza di duplicazioni nel codice ✅

## 🚀 Prossimi Passi

1. **Testare in ambiente reale**:
   - Installare dipendenze: `pip install -r requirements.txt`
   - Avviare l'app: `python3 -m volleyball_scout.ui.app`
   - Andare sulla sezione "Teams & Players"
   - Aggiungere una squadra e qualche giocatore
   - Cliccare su "Formation" e verificare che appaia la FormationPanel con i dati corretti

2. **Se Formation Setup non visualizza dati**:
   - Verificare che il database contenga effettivamente teams e players
   - Controllare i log nella console per errori
   - Usare lo script `test_formation_setup.py` per debug

## 📝 Nota Importante

Se il database è vuoto (nessuna squadra), verrà mostrato un placeholder:
```
🏐 Formation Setup
(No teams in database)
```

Questo è il comportamento previsto. Aggiungere squadre e giocatori nella sezione **Teams & Players** prima di aprire Formation Setup.

## 🔧 Debugging

Se riscontri ancora problemi:

1. Verifica che `app.py` stia usando la versione corretta:
   ```bash
   grep -n "_refresh_formation_panel" volleyball_scout/ui/app.py
   ```
   Dovrebbe mostrare UN SOLO metodo definito

2. Verifica i log nella console quando clicchi su "Formation" per tracciare errori

3. Controlla che `FormationPanel` riceva i parametri corretti:
   - `teams`: lista di dict con "id" e "name"
   - `players_by_team`: dict mapping team_id a liste di giocatori

4. Se necessario, aggiungi un print di debug in `_refresh_formation_panel()`:
   ```python
   print(f"DEBUG: Teams loaded: {len(teams)}")
   print(f"DEBUG: Players by team: {players_by_team}")
   ```
