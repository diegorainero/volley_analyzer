# 🏐 Test Navigazione Formation Setup

Questa directory contiene i test e la documentazione per il sistema di navigazione del Formation Setup.

## File Contenuti

### 1. `test_formation_navigation.py`
Script di test automatico che verifica la struttura del widget di navigazione.

**Come eseguire:**
```bash
cd volley_analizer
python3 test_navigation/test_formation_navigation.py
```

**Cosa testa:**
- ✓ Presenza di `QStackedWidget`
- ✓ FormationSetupMatches su Index 0
- ✓ Placeholder su Index 1
- ✓ Index iniziale impostato a 0
- ✓ Signal `match_selected` connesso
- ✓ FormationPanel ha segnale `back_requested`
- ✓ Metodo `_on_back_to_matches` presente
- ✓ Match caricate dal database

### 2. `NAVIGAZIONE_DOCUMENTATION.md`
Documentazione dettagliata del flusso di navigazione, con diagrammi ASCII e spiegazioni.

**Contenuti:**
- Struttura generale con QStackedWidget
- Flusso di navigazione step-by-step
- Componenti principali e responsabilità
- Gestione dello stato
- Dettagli di implementazione
- Workflow completo
- Possibili estensioni future

### 3. `IMPLEMENTATION_SUMMARY.md`
Riepilogo dell'implementazione della navigazione.

**Contenuti:**
- Cosa è stato fatto
- Architettura implementata
- Flusso di navigazione con diagrammi
- Segnali utilizzati
- Gestione del database
- Ciclo di vita dei widget
- Testing e verifiche
- Integrazione con l'app

## Struttura della Navigazione

```
FormationSetupComplete (Main Widget)
├── QStackedWidget
│   ├── Index 0: FormationSetupMatches
│   │   └── Mostra lista di partite
│   │   └── Emette signal match_selected
│   │
│   └── Index 1: FormationPanel
│       └── Mostra dettagli formazione
│       └── Emette signal back_requested
```

## Flusso Principale

1. **Avvio**: App mostra lista di partite (Index 0)
2. **Selezione**: User double-click su una partita
3. **Caricamento**: Dati caricati dal database
4. **Switch**: QStackedWidget passa a Index 1
5. **Modifica**: User modifica la formazione
6. **Back**: Click pulsante "Indietro"
7. **Ritorno**: QStackedWidget torna a Index 0

## Verifiche Eseguite

### Compilazione
```bash
python3 -m py_compile ./volleyball_scout/ui/formation_setup_complete.py
python3 -m py_compile ./volleyball_scout/ui/formation_panel.py
```
✅ Entrambi i file compilano correttamente

### Struttura
```bash
python3 test_navigation/test_formation_navigation.py
```
✅ Tutti i test passano

### Import
✅ Le classi sono importabili dalla app principale

## Segnali Implementati

### FormationSetupMatches
```python
match_selected = pyqtSignal(dict)
# Emesso quando utente double-clicca su una partita
```

### FormationPanel
```python
back_requested = pyqtSignal()
# Emesso quando utente clicca "← Torna Indietro"

formation_confirmed = pyqtSignal(dict)
# Emesso quando utente clicca "Conferma Formazione"
```

## Metodi Chiave

### FormationSetupComplete
- `_on_match_selected(match)` - Riceve segnale dal matches_widget
- `_load_and_show_formation(match)` - Carica dati e mostra FormationPanel
- `_on_back_to_matches()` - Torna alla lista di match

### FormationSetupMatches
- `_load_matches()` - Carica match dal database
- `_on_match_double_clicked(item)` - Gestisce double-click
- `_on_new_match_clicked()` - Apre dialog per nuova partita (bonus feature)

## Database

Tutte le query usano il context manager `session_scope()`:

```python
with self.db.session_scope() as session:
    matches = session.query(Match).filter(...).all()
```

## Integrazione con l'App

Il widget è integrato in:
- `app.py` - Riga 346
- `app_dark.py` - Riga 488

Con import lazy:
```python
try:
    from volleyball_scout.ui.formation_setup_complete import FormationSetupComplete
except ImportError:
    FormationSetupComplete = None
```

## Performance

- **Lazy Loading**: FormationPanel creato solo quando necessario
- **Memory Cleanup**: Widget vecchi liberati dalla memoria
- **Database**: Session gestite correttamente

## Possibili Problemi e Soluzioni

### Match non appare nella lista
1. Verificare che il database abbia match con status "draft" o "in_progress"
2. Eseguire il pulsante "🔄 Aggiorna"

### FormationPanel non si apre
1. Verificare che il match abbia squadre associate (home_team_id e away_team_id)
2. Controllare i logs per errori di database
3. Verificare che le squadre abbiano giocatori

### Pulsante "Indietro" non funziona
1. Verificare che FormationPanel ha il segnale `back_requested`
2. Verificare che il segnale è connesso in `_load_and_show_formation()`
3. Controllare i logs per errori

## Prossimi Step

1. Implementare salvataggio della formazione in DB
2. Aggiungere validazione della formazione
3. Mostrare formazione precedente come default
4. Implementare template di formazioni
5. Aggiungere anteprima prima della conferma

## Notes

- Il codice utilizza PyQt6
- Utilizza SQLAlchemy ORM per il database
- Segue il pattern signals/slots di Qt
- Implementa proper error handling
- Include logging per debugging

## Contatti

Per domande o problemi con la navigazione, consultare:
- `NAVIGAZIONE_DOCUMENTATION.md` per dettagli tecnici
- `IMPLEMENTATION_SUMMARY.md` per un overview dell'implementazione
- Source code in `volleyball_scout/ui/formation_setup_complete.py`

---

**Status:** ✅ Implementato e Testato
**Versione:** 1.0
**Data:** 2024
