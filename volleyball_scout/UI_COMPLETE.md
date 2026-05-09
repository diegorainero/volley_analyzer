# 🏐 Volleyball Scout - Interfaccia Utente Completa

## ✅ L'Interfaccia è Pronta!

L'applicazione Volleyball Scout ha ora un'interfaccia completa con:

```
┌─────────────────────────────────────────────────────────────────┐
│  🏐 Volleyball Scout | 📋 Dashboard | 👥 Squadre | 🎯 Matches   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Dashboard                                                        │
│  ┌─────────────────────────┬──────────────────────────────────┐ │
│  │ 📋 Match Disponibili    │ 📝 Sessioni in Bozza            │ │
│  │                         │                                  │ │
│  │ • Match precedenti      │ • Sessioni salvate              │ │
│  │ • Stato match           │ • Ultime modifiche              │ │
│  │ • Informazioni gare     │                                  │ │
│  └─────────────────────────┴──────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Come Avviare

```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.ui
```

L'applicazione si aprirà in una finestra PyQt6 con:
- **Risoluzione**: 1600x900 (ridimensionabile)
- **Menu in alto**: Dashboard | Squadre | Matches | Esci
- **Database**: SQLite locale (creato automaticamente)

---

## 📋 Pagine Disponibili

### 1. **Dashboard** (Pagina di Avvio)
La pagina principale mostra:

**Panel Sinistro: 📋 Match Disponibili**
- Griglia di match registrati
- Mostra: ID, Squadre, Data, Stato
- Cliccabile per selezionare un match
- Pulsante refresh per aggiornare

**Panel Destro: 📝 Sessioni in Bozza**
- Lista di sessioni di scouting non completate
- Permette di riprendere una sessione
- Sincronizzazione con il database

---

### 2. **👥 Squadre**
Gestione completa delle squadre.

**Panel Sinistro: Squadre Registrate**
- Tabella con tutte le squadre
- Colonne: Nome, Città, Categoria
- Selezionare una squadra per vedere i giocatori
- Pulsante refresh

**Panel Destro: Aggiungi Squadra**
- Form per inserire:
  - Nome (obbligatorio)
  - Città
  - Categoria
- Bottone "➕ Aggiungi Squadra"
- Bottone "🗑️ Elimina Selezionata"

**Panel Inferiore: Giocatori Squadra**
- Tabella giocatori della squadra selezionata
- Colonne: Numero, Cognome
- Bottone "➕ Aggiungi Giocatore"

**Funzionalità:**
- Aggiungere squadre al database
- Eliminare squadre
- Gestire giocatori per squadra
- Numero maglia e cognome per ogni giocatore

---

### 3. **🎯 Matches**
Gestione dei match/partite.

**Panel Superiore: Match Registrati**
- Tabella con tutti i match
- Colonne: ID, Home, Away, Data, Stato
- Selezionare per operazioni

**Bottoni di Controllo:**
- 🔄 Aggiorna (ricarica la lista)
- ➕ Nuovo Match (aggiunge match)
- 🗑️ Elimina Selezionato

**Form di Creazione:**
- Home Team ID (ID della squadra)
- Away Team ID
- Luogo (venue)
- Competizione
- Pulsante "Crea Match"

**Funzionalità:**
- Creare nuovi match
- Visualizzare match storici
- Eliminare match
- Tracciare stato match

---

## 🎨 Menu di Navigazione

### Barra in Alto
```
🏐 Volleyball Scout | 📋 Dashboard | 👥 Squadre | 🎯 Matches | ... | ❌ Esci
```

**Comportamento:**
- Bottone attivo: verde (#4CAF50) con scritte bianche
- Bottoni inattivi: bianchi con bordo grigio
- Hover: grigio chiarissimo
- Click: grigio scuro
- Esci: Richiede conferma prima di chiudere

---

## 💾 Database

**Locazione**: `~/.volleyball_scout/data/scout.db`

**Tabelle:**
- `team` - Squadre
- `player` - Giocatori
- `match` - Partite
- `match_player` - Formazioni
- `scout_event` - Eventi di scouting

**Accesso:**
- Automatico SQLite locale
- Opzionale PostgreSQL via `DATABASE_URL` env var

---

## 🔄 Flusso di Lavoro Tipico

### 1. **Preparare le Squadre**
```
Squadre → Aggiungi Squadra → Inserisci Nome/Città/Categoria
       → Aggiungi Giocatori → Numero + Cognome
```

### 2. **Creare un Match**
```
Matches → Nuovo Match → Home Team ID + Away Team ID + Venue + Competition
```

### 3. **Scegliere dalla Dashboard**
```
Dashboard → Clicca su un Match → Apri la formazione
         → O riprendi una sessione in bozza
```

---

## 🎛️ Componenti UI Disponibili

### Integrati nell'App
- **VolleyballScoutApp** - Finestra principale
- **DashboardView** - Dashboard con match e draft
- **MatchesGridWidget** - Griglia di match
- **DraftListWidget** - Lista sessioni
- **TeamManagementWidget** - Gestione squadre
- **MatchManagementWidget** - Gestione match
- **FormationPanel** - Visualizzazione formazione
- **ScoutPanel** - Scouting in tempo reale

---

## ⌨️ Scorciatoie e Comandi

| Azione | Come |
|--------|------|
| Cambiar pagina | Clicca bottone nel menu in alto |
| Refresh dati | Clicca bottone "🔄 Aggiorna" |
| Aggiungere | Compila form e clicca "➕ Aggiungi" |
| Eliminare | Seleziona elemento, clicca "🗑️ Elimina" |
| Uscire | Clicca "❌ Esci" (richiede conferma) |

---

## 🐛 Troubleshooting UI

### Problema: Non vedo i dati
**Soluzione**: 
1. Clicca il bottone "🔄 Aggiorna"
2. Controlla che il database sia connesso (vedi console)
3. Aggiungi alcuni dati dalla pagina Squadre

### Problema: Non si carica una pagina
**Soluzione**:
1. Controlla console per errori
2. Prova a refreshare i dati
3. Riavvia l'applicazione

### Problema: Database error
**Soluzione**:
```bash
# Controlla permessi
ls -la ~/.volleyball_scout/data/

# O usa un database custom
export DATABASE_URL=sqlite:///path/to/custom.db
venv/bin/python -m volleyball_scout.ui
```

---

## 📊 Architettura UI

```
VolleyballScoutApp (Main Window)
├── Menu Bar (Top Navigation)
│   ├── 📋 Dashboard Button
│   ├── 👥 Squadre Button
│   ├── 🎯 Matches Button
│   └── ❌ Esci Button
│
└── Stacked Widget (Content Area)
    ├── DashboardView
    │   ├── MatchesGridWidget
    │   └── DraftListWidget
    │
    ├── TeamManagementWidget
    │   ├── Team List Table
    │   ├── Add Team Form
    │   └── Player List Table
    │
    └── MatchManagementWidget
        ├── Match List Table
        ├── Create Match Form
        └── Control Buttons
```

---

## 🔗 File Principali

| File | Responsabilità |
|------|----------------|
| `app.py` | Applicazione principale, menu, navigazione |
| `management_widgets.py` | Widget squadre e match |
| `matches_grid.py` | Griglia di match |
| `formation_panel.py` | Visualizzazione formazione |
| `scout_panel.py` | Interfaccia scouting |
| `drafts/draft_widget.py` | Liste sessioni |

---

## 🎯 Prossimi Passi

Una volta che accedi all'app:

1. **Aggiungi Squadre** (👥 Squadre)
   - Crea le tue squadre
   - Aggiungi i giocatori

2. **Crea Match** (🎯 Matches)
   - Seleziona Home e Away team
   - Inserisci luogo e competizione

3. **Scegli dalla Dashboard** (📋 Dashboard)
   - Clicca su un match
   - Seleziona una sessione salvata

4. **Scout in Tempo Reale**
   - FormationPanel mostra il campo
   - ScoutPanel registra gli eventi

---

## 📚 Documentazione Correlata

- `QUICK_START.md` - Come avviare l'app
- `STRUCTURE.md` - Architettura del progetto
- `FORMATION_QUICK_START.md` - Dettagli FormationPanel
- `VOLLEYBALL_SCOUT_SUMMARY.md` - Overview completo

---

## ✨ Pronto all'uso!

L'interfaccia è completa e funzionante. Avvia con:

```bash
venv/bin/python -m volleyball_scout.ui
```

Buon scouting! 🏐

---

*Last Updated: 2024*
*Version: 1.0 (UI Complete)*
