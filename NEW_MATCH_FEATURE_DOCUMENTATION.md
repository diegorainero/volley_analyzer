# Nuova Partita - Documentazione della Funzionalità

## 📋 Panoramica

È stata aggiunta una nuova funzionalità che consente agli utenti di creare una nuova partita direttamente dall'interfaccia grafica. Il pulsante "➕ Nuova Partita" è disponibile nella schermata di "Selezione Partita per Formazione".

## 🎯 Obiettivi Implementati

✅ Aggiunto pulsante "Nuova Partita" nella lista match  
✅ Creato dialog `NewMatchDialog` con form completo  
✅ Validazione dei dati inseriti (squadre diverse, date valide, etc.)  
✅ Creazione automatica della partita nel database con status='draft'  
✅ Caricamento dinamico dei team dal database  
✅ Data/Ora di default impostata a oggi  
✅ Aggiornamento della lista match dopo la creazione  
✅ Selezione automatica della nuova partita  

## 🏗️ Architettura

### File Creati/Modificati

1. **`volleyball_scout/ui/new_match_dialog.py`** ✨ NUOVO
   - Classe `NewMatchDialog(QDialog)`
   - Gestisce l'interfaccia per la creazione di una nuova partita
   - Emette signal `match_created` quando la partita è creata

2. **`volleyball_scout/ui/formation_setup_complete.py`** 🔄 MODIFICATO
   - Aggiunto import di `NewMatchDialog`
   - Classe `FormationSetupMatches`: aggiunto pulsante "Nuova Partita"
   - Aggiunti metodi:
     - `_on_new_match_clicked()`: apre il dialog
     - `_on_new_match_created()`: gestisce la creazione della partita

3. **`volleyball_scout/ui/__init__.py`** 🔄 MODIFICATO
   - Aggiunto `NewMatchDialog` all'export

## 🎨 Interfaccia Utente

### NewMatchDialog

**Campi del Form:**
- **Squadra A (Home)**: Dropdown con lista di squadre dal database
- **Squadra B (Away)**: Dropdown con lista di squadre dal database
- **Data e Ora**: QDateTimeEdit con default impostato a oggi
- **Luogo**: QLineEdit opzionale (es. "Palasport di Milano")
- **Note**: QTextEdit opzionale per note aggiuntive

**Pulsanti:**
- ✅ **Salva**: Crea la partita e chiude il dialog
- ❌ **Annulla**: Chiude il dialog senza salvare

### FormationSetupMatches

**Modifiche:**
- Nuovo pulsante "➕ Nuova Partita" posizionato sopra la lista match
- Larghezza massima: 150px
- Connesso al metodo `_on_new_match_clicked()`

## 🔄 Flusso di Utilizzo

```
User clicks "➕ Nuova Partita"
    ↓
Dialog opens with empty form
    ↓
User selects:
  - Squadra A (Home)
  - Squadra B (Away)
  - Data/Ora
  - Luogo (optional)
  - Note (optional)
    ↓
User clicks "✅ Salva"
    ↓
Validation check:
  ✓ Both teams selected
  ✓ Teams are different
  ✓ Date is valid
    ↓
Match created in DB with:
  - home_team_id
  - away_team_id
  - date
  - venue (if provided)
  - notes (if provided)
  - status = 'draft'
    ↓
FormationSetupMatches updates:
  - Reloads match list
  - Selects new match in table
  - Emits match_selected signal
    ↓
(Optional) Opens Formation Setup page for the new match
```

## ✅ Validazione

### Regole di Validazione

1. **Squadra A (Home)**: Obbligatoria
2. **Squadra B (Away)**: Obbligatoria
3. **Squadre diverse**: A ≠ B (non è possibile giocare contro se stessi)
4. **Data/Ora**: Deve essere una data valida

### Messaggi di Errore

- "Selezionare la Squadra A (Home)"
- "Selezionare la Squadra B (Away)"
- "La Squadra A e la Squadra B devono essere diverse"
- "Data/ora non valida"

## 💾 Database

### Modello Match

```python
Match(
    home_team_id: int,      # Foreign key a teams.id
    away_team_id: int,      # Foreign key a teams.id
    date: datetime,         # Data e ora della partita
    venue: str (optional),  # Luogo della partita
    notes: str (optional),  # Note aggiuntive
    status: str = 'draft',  # Stato della partita
)
```

### Status Disponibili

- `draft`: Partita non ancora iniziata
- `in_progress`: Partita in corso
- `completed`: Partita completata

## 🧪 Testing

### Test Creato

File: `test_new_match_dialog.py`

**Test 1: NewMatchDialog**
- Caricamento squadre
- Verifica widget disponibili
- Validazione (squadre non selezionate)
- Validazione (squadre selezionate)

**Test 2: FormationSetupMatches**
- Creazione widget
- Verifica metodi disponibili
- Caricamento match dalla lista

### Esecuzione dei Test

```bash
cd volley_analizer
source venv/bin/activate
python test_new_match_dialog.py
```

**Risultato Atteso:**
```
✅ TUTTI I TEST PASSATI!
```

## 🔗 Integrazione

### Signal Emessi

`NewMatchDialog`:
```python
match_created = pyqtSignal(object)  # Emette dict con dati della nuova partita
```

`FormationSetupMatches`:
```python
match_selected = pyqtSignal(dict)  # Emette il match dict per selezionarlo
```

### Compatibilità PyQt

- **PyQt6**: Usato `toPyDateTime()`
- **PyQt5**: Fallback a `toPython()` se necessario

## 🐛 Gestione degli Errori

### Scenario: Database non raggiungibile
```
QMessageBox.critical(dialog, "Errore", "Errore durante la creazione della partita: {error}")
```

### Scenario: Validazione fallisce
```
QMessageBox.warning(dialog, "Errore di validazione", "{error_message}")
```

## 📝 Codebase

### Classe NewMatchDialog

```python
class NewMatchDialog(QDialog):
    match_created = pyqtSignal(object)
    
    def __init__(self, db_manager, parent=None): ...
    def _load_teams(self): ...
    def _setup_ui(self): ...
    def _validate_input(self) -> tuple[bool, str]: ...
    def _on_save(self): ...
```

### Classe FormationSetupMatches (nuovi metodi)

```python
def _on_new_match_clicked(self): ...
def _on_new_match_created(self, new_match): ...
```

## 🚀 Funzionalità Future Potenziali

1. **Creazione batch di partite**: Form per creare multiple partite da file CSV
2. **Template di partite**: Salva e carica template di partite ricorrenti
3. **Notifiche**: Alert quando una nuova partita è creata
4. **Importazione**: Importa match da sorgenti esterne (calendari, etc.)
5. **Duplicazione**: Duplica una partita esistente con modifiche minori

## 📊 Statistiche

| Metrica | Valore |
|---------|--------|
| File creati | 1 |
| File modificati | 2 |
| Linee di codice aggiunte | ~220 |
| Test implementati | 2 |
| Nuovi metodi | 2 |
| Nuovi signal | 1 |

## ✨ Qualità del Codice

- ✅ Type hints utilizzati
- ✅ Docstring per tutti i metodi
- ✅ Error handling robusto
- ✅ Validazione completa
- ✅ Logging dettagliato
- ✅ Signal/slot pattern con PyQt6
- ✅ Context manager per session DB
- ✅ Commenti esplicativi

## 🎓 Lezioni Apprese

1. PyQt6 usa `toPyDateTime()` non `toPython()`
2. L'ordine di aggiunta dei metodi in una classe non influenza l'accesso
3. I signal di PyQt devono essere emessi dopo il flush() del DB
4. QMessageBox.information() blocca l'esecuzione finché non viene chiuso

---

**Versione**: 1.0  
**Data**: 2024  
**Status**: ✅ Completo e Testato
