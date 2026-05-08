# 🏐 Flusso di Scouting Completo

## 📋 Panoramica

Il sistema di **Volleyball Scout** fornisce un flusso completo per:
1. Creare e gestire match di pallavolo
2. Configurare il roster (convocati)
3. Selezionare la formazione iniziale (titolari e liberi)
4. Analizzare le azioni durante lo scouting

## 🎯 Flusso Principale

```
┌─────────────────┐
│  DASHBOARD      │
│  (Home Screen)  │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│  MATCH MANAGEMENT        │
│  - Crea nuovo match      │
│  - Seleziona squadre     │
│  - Scegli data/ora       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  ROSTER SETUP            │
│  - Seleziona giocatori   │
│  - Sceglie team per room │
│  - Convocati lista       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  FORMATION PANEL ✨ NEW  │
│  - Drag & Drop giocatori │
│  - 6 titolari + 1 libero │
│  - Validazione auto      │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  SCOUT PANEL             │
│  - Analizza azioni       │
│  - Registra eventi       │
│  - Statistiche in tempo  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  MATCH SAVED ✓           │
│  - DB aggiornato         │
│  - Report generato       │
└──────────────────────────┘
```

## 1️⃣ Dashboard (Home Screen)

### Cosa Vedrai
- **Titolo**: "Volleyball Scout - Dashboard"
- **Pulsanti Principali**:
  - "Nuovo Match" - Crea un nuovo match
  - "Match Recenti" - Riprendi match precedenti
  - "Statistiche" - Visualizza dati aggregati

### Azioni Disponibili
- Clicca **"Nuovo Match"** per iniziare

### File Correlati
- `main_window.py` → classe `VolleyballScoutMainWindow`
- Stato: ✅ Implementato

---

## 2️⃣ Match Management (Creazione Match)

### Cosa Vedrai
Una schermata con i seguenti campi:

```
┌────────────────────────────────┐
│  CREA NUOVO MATCH              │
├────────────────────────────────┤
│                                │
│  Data:     [________]          │
│  Ora:      [________]          │
│                                │
│  Squadra 1: [Dropdown ▼]       │
│  Squadra 2: [Dropdown ▼]       │
│                                │
│  Note:     [_________________] │
│                                │
│  [Avanti →]                    │
│                                │
└────────────────────────────────┘
```

### Input Richiesti
1. **Data del match** (formato: DD/MM/YYYY)
2. **Ora del match** (formato: HH:MM)
3. **Squadra 1** - Seleziona dal dropdown
4. **Squadra 2** - Seleziona dal dropdown
5. **Note** (opzionale)

### Validazione
- ✅ Almeno 2 squadre diverse
- ✅ Data e ora valide
- ✅ Le squadre devono avere giocatori nel sistema

### Azione Successiva
Clicca **"Avanti →"** per andare a **ROSTER SETUP**

### File Correlati
- `main_window.py` → metodo `show_match_management`
- Stato: ✅ Implementato

---

## 3️⃣ Roster Setup (Selezione Giocatori)

### Cosa Vedrai

Una schermata con due colonne (una per squadra):

```
┌────────────────────┬────────────────────┐
│  SQUADRA 1: ATTACO │ SQUADRA 2: CIHSO   │
├────────────────────┼────────────────────┤
│  Giocatori:        │ Giocatori:         │
│  ☑ 1 - Rossi       │ ☑ 10 - Marrone     │
│  ☐ 2 - Bianchi     │ ☐ 11 - Grigio      │
│  ☑ 3 - Verdi       │ ☑ 12 - Viola       │
│  ☐ 4 - Gialli      │ ☐ 13 - Celeste     │
│  ☑ 5 - Neri        │ ☑ 14 - Turchese    │
│  ☐ 6 - Rosa        │ ☐ 15 - Magenta     │
│  ☑ 7 - Arancione   │ ☑ 16 - Lime        │
│  ☐ 8 - Blu         │ ☐ 17 - Navy        │
│                    │                    │
│  [Selezionati: 4]  │ [Selezionati: 4]   │
└────────────────────┴────────────────────┘
     [← Indietro]           [Avanti →]
```

### Cosa Fare
1. **Seleziona i giocatori** che parteciperanno al match
2. Usa le **checkbox** per attivare/disattivare
3. Puoi selezionare **quanti giocatori vuoi** (non c'è limite)
4. Minimo consigliato: **8-10 giocatori** per squadra

### Validazione
- ⚠️ Se selezioni meno di **6 giocatori** per una squadra, vedrai un warning
- Comunque puoi procedere (l'errore sarà catturato in Formation Panel)

### Azione Successiva
Clicca **"Avanti →"** per andare a **FORMATION PANEL**

### File Correlati
- `main_window.py` → metodo `show_roster_setup`
- `roster_view.py` → classe `RosterSetupView`
- Stato: ✅ Implementato

---

## 4️⃣ Formation Panel (Selezione Formazione) ✨ **NEW**

### Cosa Vedrai

Un'interfaccia intuitiva con **drag & drop** per assegnare i titolari e i liberi:

```
┌─────────────────────────────────────────────────────────────────┐
│ Squadra: Attacco                                                │
├──────────┬──────────────────────────┬──────────────────────────┤
│  LIBERI  │  GIOCATORI DISPONIBILI   │  FORMAZIONE (6 TITOLARI) │
│          │                          │                          │
│  ┌─────┐ │  ◉ 1  ◉ 2  ◉ 3  ◉ 4 ◉ 5  │  ┌────┬────┬────┐      │
│  │  -  │ │  (Blu, Draggabili)      │  │ 1  │ 2  │ 3  │      │
│  └─────┘ │  ◉ 6  ◉ 7  ◉ 8  ◉ 9 ◉10  │  ├────┼────┼────┤      │
│  ┌─────┐ │                          │  │ 4  │ 5  │ 6  │      │
│  │ 12  │ │ (Drag here → Slot yellow)│  └────┴────┴────┘      │
│  └─────┘ │                          │                          │
└──────────┴──────────────────────────┴──────────────────────────┘
```

### Cosa Fare

**Passo 1: Selezionare i Titolari (6 giocatori)**
1. Guarda i **bottoni blu** al centro (Giocatori Disponibili)
2. **Trascina un bottone** verso uno dei **6 slot gialli** a destra
3. Ripeti fino ad avere **6 numeri** nei 6 slot

**Passo 2: Selezionare i Liberi (almeno 1 giocatore)**
1. **Trascina un bottone** verso uno dei **2 slot beige** a sinistra
2. Assegna **almeno 1 libero**

**Passo 3: Validazione**
1. Il pannello controlla automaticamente:
   - ✅ Esattamente **6 titolari**
   - ✅ Almeno **1 libero**
2. Se manca qualcosa, vedrai un **popup di errore**

**Passo 4: Conferma**
1. Quando tutto è corretto, clicca **"Conferma Formazione"**
2. I dati vengono salvati nel DB
3. Procedi al **SCOUT PANEL**

### Funzionalità Avanzate

**Click per Pulire**
- Clicca su un numero in uno slot per **rimuoverlo**
- Lo slot torna vuoto, il bottone è ancora disponibile

**Reset Totale**
- Clicca il bottone **"Reset"** per pulire tutto

### File Correlati
- `formation_panel.py` → classi `FormationPanel`, `TeamFormationWidget`, `PlayerButton`, `FormationSlot`, `LiberoSlot`
- `main_window.py` → metodo `show_formation_panel`, `on_formation_confirmed`
- Stato: ✅ **Appena Implementato** - Drag & Drop funzionante

### 📖 Documentazione Completa
→ Vedi: **FORMATION_PANEL.md**

---

## 5️⃣ Scout Panel (Analisi Azioni)

### Cosa Vedrai

Una schermata live per registrare le azioni durante il match:

```
┌──────────────────────────────────────────┐
│          SCOUT PANEL                     │
├──────────────────────────────────────────┤
│                                          │
│  Set: 1/3  |  Punteggio: 12-8           │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ VIDEO FEED (in tempo reale)         ││
│  │ [Video con giocatori detected]      ││
│  │                                     ││
│  │                                     ││
│  └─────────────────────────────────────┘│
│                                          │
│  Azione da registrare:                   │
│  [Giocatore: #1 ▼] [Azione: Schiaccio ▼]│
│                                          │
│  [Registra Azione]  [Cambia Set]         │
│                                          │
└──────────────────────────────────────────┘
```

### Cosa Fare

1. **Seleziona il Giocatore**: Numero dal dropout
2. **Seleziona l'Azione**: Tipo di giocata (Schiaccio, Alzata, Ricezione, ecc.)
3. **Registra**: Clicca "Registra Azione"
4. **Ripeti**: Per ogni azione del match
5. **Cambia Set**: Quando finisce il set, seleziona il prossimo

### Dati Registrati
- ✅ Giocatore (ID, numero, nome)
- ✅ Azione (tipo)
- ✅ Timestamp (momento esatto)
- ✅ Set (quale set)
- ✅ Punteggio al momento dell'azione

### File Correlati
- `scout_panel.py` → classe `ScoutPanel`
- Stato: ✅ Implementato

---

## 📊 Database Integration

### Cosa Viene Salvato

**Quando Crei un Match:**
- ID match, data, ora, squadre, note

**Quando Selezioni Roster:**
- MatchPlayer entries (giocatore + match)

**Quando Selezioni Formazione:**
- MatchPlayer.is_starter = True (6 titolari)
- MatchPlayer.is_libero = True (1 libero)

**Quando Registri Azioni:**
- ScoutAction entries (giocatore, azione, timestamp, set)

### Struttura DB

```
Match
├── id
├── date
├── time
├── home_team_id → Team
├── away_team_id → Team
└── notes

MatchPlayer
├── id
├── match_id → Match
├── team_id → Team
├── player_id → Player
├── is_starter (True/False) ← Impostato in Formation Panel
├── is_libero (True/False)  ← Impostato in Formation Panel
└── ...

ScoutAction
├── id
├── match_id → Match
├── player_id → Player
├── action_type (str: "Schiaccio", "Alzata", ecc.)
├── timestamp
├── set_number
└── ...
```

### Migrazioni

Le migrazioni Alembic gestiscono:
- ✅ Aggiunta colonne `is_starter`, `is_libero` a `match_players`
- ✅ Creazione tabella `scout_actions`

→ Setup: `python setup.py dev_setup`

---

## 🎮 Navigazione tra Pannelli

| Da | A | Metodo | Condizione |
|---|---|---|---|
| Dashboard | Match Management | Click "Nuovo Match" | Sempre |
| Match Management | Roster Setup | Click "Avanti" | Match valido |
| Roster Setup | Formation Panel | Click "Avanti" | Giocatori selezionati |
| Formation Panel | Scout Panel | Click "Conferma" | 6 titolari + 1 libero |
| Scout Panel | Fine | Click "Salva Match" | Tutte le azioni registrate |
| Qualsiasi | Dashboard | Click "Home" | Sempre |

---

## 🔄 Workflow Completo: Esempio Pratico

### Scenario: Analizzare un match Attacco vs Cihsosla Volley

**Step 1: Dashboard**
- Apri l'app
- Clicca "Nuovo Match"

**Step 2: Match Management**
- Data: 08/05/2024
- Ora: 19:00
- Squadra 1: Attacco
- Squadra 2: Cihsosla Volley
- Clicca "Avanti"

**Step 3: Roster Setup**
- Squadra 1 (Attacco):
  - Seleziona: 1, 2, 3, 4, 5, 6, 7, 8 (8 giocatori)
- Squadra 2 (Cihsosla):
  - Seleziona: 10, 11, 12, 13, 14, 15, 16, 17 (8 giocatori)
- Clicca "Avanti"

**Step 4: Formation Panel**
- **Attacco**:
  - Titolari: Trascina 1, 2, 3, 4, 5, 6 nei 6 slot
  - Libero: Trascina 8 nello slot L1
- **Cihsosla Volley**:
  - Titolari: Trascina 10, 11, 12, 13, 14, 15 nei 6 slot
  - Libero: Trascina 17 nello slot L1
- Clicca "Conferma Formazione"

**Step 5: Scout Panel**
- Inizia il match
- Per ogni azione:
  - Seleziona giocatore (es: #1)
  - Seleziona azione (es: Schiaccio)
  - Clicca "Registra"
- Al cambio set: Clicca "Cambia Set"
- Alla fine: Clicca "Salva Match"

**Step 6: Risultato**
- Match salvato nel DB
- Report generato
- Statistiche disponibili nel Dashboard

---

## 📱 Interfaccia Utente Dettagli

### Bottoni e Colori

| Elemento | Colore | Azione |
|----------|--------|--------|
| Bottone Principale | Verde (#27ae60) | Avanza nel flusso |
| Bottone Secondario | Azzurro | Indietro/Altre azioni |
| Bottone Annulla | Rosso | Cancella operazione |
| Giocatore (Formation) | Blu (#4a90e2) | Draggabile |
| Giocatore Selezionato | Giallo (#f4c430) | Rilasciare qui |
| Slot Titolari | Giallo (#f4c430) | Drop zone |
| Slot Liberi | Beige (#e8d4a2) | Drop zone |

### Messaggi di Feedback

- **Errore**: Popup rosso con dettagli
- **Successo**: Toast verde con conferma
- **Warning**: Giallo per avvisi
- **Info**: Azzurro per informazioni

---

## 🔧 Troubleshooting

### Il Formation Panel mostra errore "0 titolari"
**Causa**: Non hai completato il Roster Setup correttamente
**Soluzione**: Torna indietro, seleziona almeno 6 giocatori per squadra

### Non riesco a trascinare i giocatori
**Causa**: Drag-Drop potrebbe non essere abilitato
**Soluzione**: 
- Prova a cliccare sui bottoni blu (dovrebbe iniziare il drag)
- Se non funziona, verifica PyQt6 è installato: `pip install PyQt6`

### "Seleziona 6 titolari per Attacco. Attualmente: 3"
**Causa**: Non hai completato la formazione
**Soluzione**: Continua a trascinare giocatori finché non hai 6

### Il punteggio non si aggiorna
**Causa**: Possibile errore nel caricamento dati
**Soluzione**: Salva il match e riapri

---

## 📚 File e Moduli

| File | Classe/Funzione | Scopo |
|------|---|---|
| `main_window.py` | `VolleyballScoutMainWindow` | Finestra principale, navigazione |
| `formation_panel.py` | `FormationPanel` | Pannello formazione con drag-drop |
| `scout_panel.py` | `ScoutPanel` | Pannello analisi azioni |
| `roster_view.py` | `RosterSetupView` | Selezione giocatori |
| `models.py` | `Match`, `MatchPlayer`, `ScoutAction` | Modelli DB |
| `db_manager.py` | `DatabaseManager` | Gestione database |

---

## 🎓 Workflow Summary

```
START
  ↓
[Dashboard] Clicca "Nuovo Match"
  ↓
[Match Management] Inserisci dettagli match
  ↓
[Roster Setup] Seleziona giocatori convocati
  ↓
[Formation Panel] 🆕 Assegna 6 titolari + 1 libero (Drag & Drop)
  ↓
[Scout Panel] Registra azioni durante il match
  ↓
[Report] Visualizza statistiche e analisi
  ↓
END
```

---

## ✅ Checklist per Nuovo Utente

- [ ] Ho letto il flusso completo sopra
- [ ] Ho capito i 5 step principali
- [ ] So come usare il Formation Panel con drag-drop
- [ ] Ho eseguito il test: `python tests/test_formation_panel_ui.py`
- [ ] Ho provato a creare un match di prova
- [ ] Ho completato una formazione
- [ ] Ho registrato alcune azioni scout

---

## 📖 Documentazione Collegata

- **FORMATION_PANEL.md** - Guida dettagliata al nuevo pannello drag-drop
- **GESTIONE_SQUADRE.md** - Gestione anagrafica squadre e giocatori
- **DATABASE_MANAGEMENT.md** - Gestione database e migrazioni
- **ADVANCED_DETECTION_README.md** - Sistema di rilevamento giocatori

---

**Versione**: 1.0
**Ultimo Aggiornamento**: Maggio 2024
**Status**: ✅ Production Ready con Formation Panel Drag-Drop
