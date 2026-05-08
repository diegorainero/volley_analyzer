# Match Salvati - Feature Implementation Summary

## Overview
Aggiunta della sezione "Match Salvati" nella schermata `MatchManagementWidget` che mostra tutti i match creati e consente di continuare gli scout incomplet o visualizzare dettagli di quelli completati.

## Modifiche Implementate

### 1. File Modificato: `volleyball_scout/ui/main_window.py`

#### Aggiunta alle Importazioni (L20)
```python
from PyQt6.QtWidgets import (
    ...
    QGroupBox,  # ← AGGIUNTO
    ...
)
```

#### Classe `MatchManagementWidget` (L682-886)

##### Signal Aggiunto (L684)
```python
class MatchManagementWidget(QWidget):
    start_roster_setup = pyqtSignal(int)  # Emit match_id (esistente)
    resume_match = pyqtSignal(int)  # ← AGGIUNTO: Emit match_id per riprendere scout
```

##### Modifiche in `__init__()` (L695-748)

**Sezione "Crea Nuovo Match"**
- Wrap dei form elements in un `QGroupBox("Crea Nuovo Match")`
- Migliore organizzazione visuale

**Sezione "Match Salvati"** (L723-748)
- Aggiunto `QGroupBox("Match Salvati")`
- Aggiunto `self.matches_list_widget = QListWidget()`
- Connessione click: `itemClicked.connect(self._on_match_clicked)`
- Stylesheet personalizzato con bordi arrotondati e padding

**Caricamento iniziale**
- Aggiunta chiamata: `self._load_saved_matches()` in `__init__`

##### Nuovo Metodo: `_load_saved_matches()` (L824-854)
```python
def _load_saved_matches(self):
    """Carica e visualizza tutti i match salvati nella lista"""
    # 1. Pulisce la lista
    # 2. Query al database per tutti i Match ordinati per data (più recenti prima)
    # 3. Per ogni match:
    #    - Estrae home_team.name, away_team.name, data, status
    #    - Crea QListWidgetItem con testo formattato
    #    - Applica colori basati su status:
    #      - "completed": ✅ Verde chiaro (#D4EDDA) con testo verde scuro (#155724)
    #      - "draft"/"in_progress": ⏳ Giallo chiaro (#FFF3CD) con testo marrone (#856404)
    #    - Salva match.id con setData(Qt.ItemDataRole.UserRole)
    #    - Aggiunge item alla lista
```

##### Nuovo Metodo: `_on_match_clicked(item)` (L856-883)
```python
def _on_match_clicked(self, item: QListWidgetItem):
    """Gestisce il click su un match dalla lista"""
    # 1. Recupera match_id dall'item
    # 2. Cerca il match nel database
    # 3. Se status == "completed":
    #    - Mostra QMessageBox.information con dettagli
    # 4. Se status != "completed":
    #    - Mostra QMessageBox.question "Vuoi continuare lo scouting?"
    #    - Se sì: emette resume_match.emit(match_id)
```

##### Nuovo Metodo: `refresh_matches()` (L885-887)
```python
def refresh_matches(self):
    """Metodo pubblico per aggiornare la lista dei match"""
    self._load_saved_matches()
```

##### Modifica a `create_match_and_start()` (L821)
- Aggiunta chiamata `self._load_saved_matches()` dopo la creazione del match
- Aggiorna la lista quando viene creato un nuovo match

### 2. File Modificato: `volleyball_scout/ui/main_window.py` (classe `VolleyballScoutMainWindow`)

#### Nuova Connessione in `init_ui()` (L1035)
```python
self.match_view.resume_match.connect(self.show_formation_panel)
```
- Collega il signal `resume_match` al metodo `show_formation_panel`
- Consente di continuare uno scout da un match salvato

#### Modifica a `show_match_view()` (L1052)
```python
def show_match_view(self):
    self.match_view.load_teams()
    self.match_view.refresh_matches()  # ← AGGIUNTO
    self.stacked_widget.setCurrentIndex(3)
```
- Aggiorna la lista dei match ogni volta che si accede alla schermata Match Management

## Design & Colori

### Status "Incontro da terminare" (draft / in_progress)
- **Icona**: ⏳ (Clessidra)
- **Background**: Giallo chiaro (`#FFF3CD`)
- **Testo**: Marrone scuro (`#856404`)
- **Significato**: Match in corso o da completare

### Status "Incontro terminato" (completed)
- **Icona**: ✅ (Checkmark)
- **Background**: Verde chiaro (`#D4EDDA`)
- **Testo**: Verde scuro (`#155724`)
- **Significato**: Match completato e archiviato

## Flusso di Utilizzo

### Scenario 1: Creare un nuovo match
1. User seleziona due squadre, data, competizione, impianto
2. Click "Avvio Scout (Imposta Roster)"
3. Match creato con status "draft"
4. Lista "Match Salvati" si aggiorna automaticamente
5. Nuovo match appare in giallo con ⏳

### Scenario 2: Continuare uno scout incomplet
1. User visualizza il match in giallo nella lista
2. Click sul match
3. Appare dialog "Vuoi continuare lo scouting?"
4. Click "Yes" → signal `resume_match` emesso
5. Panel di formazione caricato per riprendere lo scout

### Scenario 3: Visualizzare match completato
1. User visualizza il match in verde nella lista
2. Click sul match
3. Appare dialog informativo con dettagli
4. Match è di sola lettura (completato)

## Styling CSS

```python
QListWidget {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 5px;
}
QListWidget::item {
    padding: 10px;
    border-radius: 3px;
    margin: 2px 0px;
}
```

## Database Integration

- Utilizza `Match.status` per determinare lo stato
- Valori supportati: `"draft"`, `"in_progress"`, `"completed"`
- Ordina per `Match.date.desc()` (più recenti prima)
- Fallback a `"?"` se squadra/data non disponibile

## Testing Checklist

- [ ] Creare 2 match con squadre diverse
- [ ] Verificare che compaiano nella lista "Match Salvati"
- [ ] Completare 1 match (status = "completed")
- [ ] Verificare che uno appaia in giallo ⏳
- [ ] Verificare che l'altro appaia in verde ✅
- [ ] Click su match "da terminare" → dialog "Continua scout?"
- [ ] Click "Yes" → carica panel formazione
- [ ] Click su match "completato" → dialog informativo
- [ ] Aggiornare database manualmente e verificare refresh

## Future Enhancements

1. Aggiungere bottone "Elimina" per cancellare match non necessari
2. Aggiungere filtri (solo draft, solo completed, per squadra)
3. Aggiungere ricerca per nome squadra
4. Aggiungere ordinamento (per data, per squadra)
5. Aggiungere statistiche rapide (match totali, completati, pendenti)
6. Aggiungere esportazione dati match completati
7. Aggiungere storico con dettagli set e risultati finali

## Note Tecniche

- Tutti i metodi utilizzano `self.db.session_scope()` per isolamento transazionale
- QListWidget è state-less: ogni refresh ricarica da DB
- User data stored in `Qt.ItemDataRole.UserRole` per sicurezza
- Signal emission non produce side-effects diretti (architecture pattern)
