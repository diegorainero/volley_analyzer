# Formation Panel - Guida Visuale

## 📋 Panoramica

Il **FormationPanel** è una nuova interfaccia intuitiva e visuale per selezionare la formazione iniziale (titolari e liberi) per uno o più match di pallavolo.

**Caratteristiche principali:**
- ✅ **Drag & Drop**: Trascina i numeri dei giocatori negli slot di formazione
- ✅ **Visual Feedback**: Gli slot cambiano colore quando sono in hover
- ✅ **Multi-Squadra**: Supporta la formazione per 2 squadre simultaneamente
- ✅ **Click-to-Clear**: Clicca su uno slot per rimuovere il giocatore
- ✅ **Validazione**: Controlla automaticamente che tu abbia 6 titolari + 1 libero per squadra

## 🎨 Layout Visuale

Ogni squadra ha un layout a 3 sezioni:

```
┌─────────────────────────────────────────────────────────────────┐
│ Squadra: Nome                                                   │
├──────────┬──────────────────────────┬──────────────────────────┤
│  LIBERI  │  GIOCATORI DISPONIBILI   │  FORMAZIONE (6 TITOLARI) │
│          │                          │                          │
│  ┌─────┐ │  ◉◉◉◉◉◉  (Bottoni blu)  │  ┌────┬────┬────┐      │
│  │ -   │ │  ◉◉◉◉◉◉  Draggabili     │  │ -  │ -  │ -  │      │
│  └─────┘ │                          │  ├────┼────┼────┤      │
│  ┌─────┐ │                          │  │ -  │ -  │ -  │      │
│  │ -   │ │                          │  └────┴────┴────┘      │
│  └─────┘ │                          │  (Slot gialli)         │
└──────────┴──────────────────────────┴──────────────────────────┘
```

### Sezione Sinistra: Liberi
- **2 slot** per i liberi (più piccoli, sfondo beige)
- Puoi assegnare 1-2 liberi a seconda delle esigenze
- **Clicca per pulire**: Se c'è già un numero, clicca per rimuoverlo

### Sezione Centro: Giocatori Disponibili
- **Griglia 6x2** di bottoni circolari blu (60x60px)
- Mostra il numero del giocatore
- **Draggabili**: Trascinali verso i 6 slot gialli o i 2 slot liberi
- I bottoni diventano **gialli** quando trascinati (per highlighting visuale)

### Sezione Destra: Formazione in Campo
- **Griglia 2x3** di rettangoli gialli (100x100px)
- Rappresenta la **formazione dei 6 titolari** in campo
- **Drop zone**: Accetta numeri trascinati
- **Clicca per pulire**: Se contiene un numero, clicca per rimuoverlo
- I bordi cambiano da **tratteggiati** (vuoti) a **solidi** (pieni)

## 🎮 Come Usare

### Passo 1: Trascinare i Giocatori

1. Seleziona un numero dalla griglia **Giocatori Disponibili** (centro)
2. **Trascina il bottone** verso uno dei 6 slot gialli (formazione)
3. Ripeti finché non hai 6 numeri nei 6 slot

**Esempio:**
```
Drag: Bottone "1" → Slot P1 ✓
Drag: Bottone "2" → Slot P2 ✓
Drag: Bottone "3" → Slot P3 ✓
Drag: Bottone "4" → Slot P4 ✓
Drag: Bottone "5" → Slot P5 ✓
Drag: Bottone "6" → Slot P6 ✓
```

### Passo 2: Assegnare i Liberi

1. Seleziona un giocatore dalla griglia **Giocatori Disponibili**
2. **Trascina il bottone** verso uno dei 2 slot liberi (sinistra)
3. Assegna almeno 1 libero

**Esempio:**
```
Drag: Bottone "15" → Slot L1 ✓
```

### Passo 3: Validazione e Conferma

1. Quando hai **6 titolari + 1 libero**, il pulsante "Conferma Formazione" è abilitato
2. Se mancano giocatori, vedrai un **messaggio di errore** con il numero attuale
3. Premi "Conferma Formazione" per salvare

## 🔧 Funzionalità Avanzate

### Click per Pulire
Se vuoi **rimuovere un giocatore** da uno slot:
1. **Clicca direttamente** sul numero nello slot (P1, P2, L1, ecc.)
2. Lo slot torna vuoto (mostra "-")
3. Il bottone del giocatore resta disponibile nel centro

### Reset Totale
Premi il pulsante **"Reset"** per:
- Pulire tutti i 6 slot di formazione
- Pulire tutti i 2 slot liberi
- Resettare lo stato di tutti i bottoni

### Multi-Squadra
Se nel match ci sono **2 squadre**:
- Vedrai **2 sezioni separate** (una per squadra)
- Devi completare la formazione per **entrambe**
- Se una squadra non è completa, il pannello mostrerà un errore

## 📊 Validazione

Il pannello valida automaticamente:

✅ **Titolari**: Esattamente **6 per squadra**
✅ **Liberi**: Almeno **1 per squadra**
✅ **Univocità**: Ogni giocatore può essere assegnato una sola volta

**Messaggi di Errore:**
```
"Seleziona 6 titolari per Attacco. Attualmente: 5"
"Seleziona almeno 1 libero per Cihsosla Volley"
```

## 🎨 Colori e Stili

| Elemento | Colore | Significato |
|----------|--------|------------|
| Bottone Giocatore (blu) | #4a90e2 | Giocatore non selezionato |
| Bottone Giocatore (giallo) | #f4c430 | Giocatore selezionato/dragging |
| Slot Formazione (giallo) | #f4c430 | Slot per titolari |
| Slot Formazione (border tratteggiato) | #e6b800 | Slot vuoto |
| Slot Formazione (border solido) | #e6b800 | Slot pieno |
| Slot Libero (beige) | #e8d4a2 | Slot per liberi |
| Hover Formazione (giallo brillante) | #ffed4e | Drag in corso, pronto a droppare |

## 🧪 Testing

Esegui il test visivo con:
```bash
python tests/test_formation_panel_ui.py
```

Questo lancerà un'applicazione PyQt6 completa con dati di test, permettendoti di:
- Testare il drag-drop
- Verificare la validazione
- Controllare i messaggi di errore

## 📝 Implementazione Tecnica

### Classi Principali

**`PlayerButton`**
- Bottone draggabili per i giocatori
- Emette MIME data con `player_id|number`
- Cambia colore quando selezionato

**`FormationSlot`**
- Drop zone per i titolari (100x100px)
- Accetta drag events
- Può essere pulito con click

**`LiberoSlot`**
- Drop zone per i liberi (70x70px)
- Simile a FormationSlot ma più piccolo

**`TeamFormationWidget`**
- Gestisce la formazione di una singola squadra
- Organizza i 3 layout (liberi, giocatori, formazione)

**`FormationPanel`**
- Widget principale
- Gestisce 1 o più squadre
- Emette segnale `formation_confirmed` con dati formattati

### Segnale Emesso

Quando la formazione è confermata, emette:
```python
{
    "titolari": {
        team_id_1: [player_id_1, player_id_2, ...],
        team_id_2: [player_id_1, player_id_2, ...]
    },
    "libero": {
        team_id_1: player_id,
        team_id_2: player_id
    }
}
```

## 🔄 Flusso di Integrazione

1. **RosterSetup** → Seleziona i giocatori del match
2. **FormationPanel** → Assegna titolari e liberi
3. **ScoutPanel** → Inizia lo scouting vero e proprio

## 🐛 Troubleshooting

### Il drag-drop non funziona
- ✅ Assicurati che Python sia correctly inizializzato
- ✅ Verifica che PyQt6 sia installato: `pip install PyQt6`
- ✅ Prova il test: `python tests/test_formation_panel_ui.py`

### I colori sono strani
- ✅ Pulisci la cache: `rm -rf volley_analizer/__pycache__`
- ✅ Riavvia l'applicazione

### Il pannello è troppo grande/piccolo
- ✅ I dimensioni sono hardcoded (60px bottoni, 100px slot)
- ✅ Modifica in `formation_panel.py` se necessario

## 📚 File Correlati

- `formation_panel.py` - Implementazione principale
- `main_window.py` - Integrazione nel flusso principale
- `test_formation_panel_ui.py` - Test visivo
- `SCOUTING_FLOW.md` - Flusso completo di scouting
