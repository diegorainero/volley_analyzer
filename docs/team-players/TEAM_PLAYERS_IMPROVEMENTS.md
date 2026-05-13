# 🏐 Miglioramenti Pagina "Squadre e Giocatori"

## 📋 Sommario delle Modifiche

Versione: **v2.0** - Interfaccia rinnovata con layout QSplitter, dialog di modifica giocatori e validazione completa.

---

## ✨ Nuove Funzionalità

### 1. **Layout Migliorato con QSplitter**
- **Sidebar sinistra (25%)**: Lista squadre ridotta e ordinata
- **Area principale (75%)**: Dettagli squadra + Lista giocatori
- **Ridimensionabile**: L'utente può trascinare il divisore per cambiare le proporzioni
- **Theme coerente**: Mantiene il dark theme applicato globalmente

### 2. **Dialog di Modifica Giocatore** (`ModifyPlayerDialog`)
Nuovo dialog modale che permette di:
- **Aggiungere nuovo giocatore**: Clicca "➕ Aggiungi Giocatore"
- **Modificare giocatore**: Doppio-click su un giocatore nella lista
- **Modifica inline**: Non usa più il form integrato, ma un dialog pulito e separato

#### Campi Disponibili:
| Campo | Tipo | Vincoli |
|-------|------|---------|
| **Nome** | Testo | Facoltativo |
| **Cognome** | Testo | 🔴 Obbligatorio |
| **Numero Maglia** | NumeroInt | 0-99 |
| **Ruolo** | ComboBox | [Palleggiatore, Opposto, Schiacciatore, Centrale, Libero] |
| **Foto** | File Image | PNG, JPG, JPEG, BMP |

### 3. **Validazione Completa**
```python
✅ Cognome non vuoto
✅ Numero maglia tra 0-99
✅ Ruolo selezionato
✅ Foto opzionale (con preview)
```

### 4. **Aggiornamenti UI**
- ✅ Menu rinominato: "👥 Teams & Players" → "👥 Squadre e Giocatori"
- ✅ Label aggiornate all'italiano
- ✅ Emoji per migliore UX:
  - 🖼️ per logo squadra
  - 📷 per foto giocatore
  - ➕ per aggiungere
  - ❌ per eliminare/annullare
  - ✅ per salvare

---

## 🔧 Dettagli Tecnici

### Classe: `ModifyPlayerDialog(QDialog)`

#### Metodi Principali:
```python
def __init__(self, player=None, parent=None):
    """
    Inizializza il dialog.
    Args:
        player: Player object per modifica, None per nuovo
        parent: Parent widget
    """

def validate() -> bool:
    """Valida i dati inseriti"""

def get_player_data() -> dict:
    """Ritorna dati: {first_name, last_name, number, role, photo}"""
```

#### Ruoli Disponibili (ROLES):
```python
["Palleggiatore", "Opposto", "Schiacciatore", "Centrale", "Libero"]
```

### Classe: `TeamManagementWidget(QWidget)` - Modifiche Principali

#### Layout Nuovo:
```
┌─────────────────────────────────────┐
│ 👥 Squadre e Giocatori              │ (Header)
├────────────────┬────────────────────┤
│  SQUADRE       │  DETTAGLI SQUADRA  │
│  (25%)         │  + GIOCATORI       │
│                │  (75%)             │
│ • Team 1       │  Nome: ...         │
│ • Team 2       │  Cat: ...          │
│ • Team 3       │  ━━━━━━━━━━━━━━━  │
│                │  ➕ Aggiungi       │
│                │  ❌ Rimuovi        │
│                │  ━━━━━━━━━━━━━━━  │
│                │  • #01 - Mario Rossi (Palleggiatore)
│                │  • #10 - Lucia Bianchi (Schiacciatore)
│                │  • #12 - Paolo Verdi (Centrale)
│                │                    │
└────────────────┴────────────────────┘
```

#### Metodi Modificati:
- `_setup_ui()`: Aggiunto QSplitter, rimosso form integrato per giocatori
- `enable_player_form()`: Apre ModifyPlayerDialog
- `edit_player()`: Nuovo metodo, gestisce doppio-click per modifica
- `on_player_selected()`: Semplificato (non più carica form)
- `on_team_selected()`: Numero maglia formattato con `f"#{player.number:02d}"`

---

## 🎯 Flusso Utente

### Aggiungere un Giocatore:
1. Seleziona una squadra dal sidebar
2. Clicca "➕ Aggiungi Giocatore"
3. Dialog "Nuovo Giocatore" si apre
4. Compila: Nome, Cognome, Numero, Ruolo, Foto (opzionale)
5. Clicca "✅ Salva"
6. La lista si aggiorna automaticamente

### Modificare un Giocatore:
1. Seleziona squadra
2. **Doppio-click** su giocatore nella lista
3. Dialog "Modifica Giocatore" si apre con dati precaricati
4. Modifica i campi desiderati
5. Clicca "✅ Salva"
6. La lista si aggiorna

### Eliminare un Giocatore:
1. Seleziona giocatore nella lista
2. Clicca "❌ Rimuovi Giocatore"
3. Conferma eliminazione
4. La lista si aggiorna

---

## 🔍 Mapping Componenti

| Componente | Posizione | Responsabilità |
|-----------|-----------|-----------------|
| `TeamManagementWidget` | `ui/team_management.py` | Gestione squadre e layout principale |
| `ModifyPlayerDialog` | `ui/team_management.py` | Dialog modifica/aggiunta giocatore |
| `app_dark.py` | Menu & routing | Integrazione con l'app principale |
| Database | `core/database.py` | Persistenza squadre e giocatori |

---

## 📝 File Modificati

### `volleyball_scout/ui/team_management.py`
- ✅ Aggiunta classe `ModifyPlayerDialog` (linee 38-147)
- ✅ Refactor `TeamManagementWidget._setup_ui()` con QSplitter
- ✅ Nuovi metodi: `edit_player()`, `on_player_selected()` semplificato
- ✅ `enable_player_form()` aggiornato per usare dialog
- ✅ Validazione completa in `ModifyPlayerDialog.validate()`

### `volleyball_scout/ui/app_dark.py`
- ✅ Menu item rinominato: "👥 Teams & Players" → "👥 Squadre e Giocatori"
- ✅ Dashboard card aggiornata
- ✅ Placeholder widget aggiornato

---

## 🧪 Test Consigliati

```python
# 1. Test creazione dialog
dialog = ModifyPlayerDialog(player=None)
assert dialog.validate() == False  # Senza cognome

# 2. Test validazione
dialog.last_name_input.setText("Rossi")
assert dialog.validate() == True

# 3. Test numero maglia
dialog.number_input.setValue(100)
assert dialog.validate() == False  # > 99

# 4. Test layout QSplitter
splitter.sizes()  # Deve essere [25, 75]
```

---

## 🎨 Theme & Styling

- **Dark Theme**: Coerente con il resto dell'app
- **Dialog Modal**: Blocca l'interazione con la finestra principale
- **ComboBox Ruoli**: Dropdown precompilato con 5 ruoli
- **Emoji Icons**: Migliore usabilità e visibilità

---

## 📦 Dipendenze

Nessuna dipendenza nuova aggiunta. Utilizza:
- ✅ PyQt6 (già presente)
- ✅ SQLAlchemy (già presente)
- ✅ Standard library (pathlib, sys)

---

## 🚀 Uso

L'app si adatta automaticamente al caricamento del TeamManagementWidget:

```python
# app_dark.py
if TeamManagementWidget:
    self.teams_widget = TeamManagementWidget(self.db)
```

Nessuna configurazione aggiuntiva necessaria.

---

## 📌 Note Importanti

1. **Numero Maglia**: Ora con padding a 2 cifre: `#01`, `#10`, `#99`
2. **Ruoli Fissi**: Enum predefinito, non editable dall'utente
3. **Foto Opzionale**: Non è obbligatoria, stored come path
4. **Session Management**: Ogni operazione apre/chiude session sqlite autonomamente
5. **QSplitter Ridimensionabile**: Utente può trascinare per cambiare proporzioni

---

## ✅ Checklist di Completamento

- [x] Layout QSplitter (25% / 75%)
- [x] Dialog `ModifyPlayerDialog` creato
- [x] Doppio-click per modifica
- [x] Validazione completa (cognome, numero, ruolo)
- [x] Ruoli come ComboBox
- [x] Foto con preview e browse
- [x] Salva/Annulla funzionante
- [x] Menu rinominato in italiano
- [x] Dark theme coerente
- [x] Emoji icons aggiunti
- [x] Compilazione Python senza errori
- [x] Imports verificati

---

**Ultima aggiornamento**: 2024
**Versione**: 2.0
**Status**: ✅ Pronto per il testing
