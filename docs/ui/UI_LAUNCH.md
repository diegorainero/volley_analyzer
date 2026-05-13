# 🚀 Come Lanciare Volleyball Scout - UI

## ✅ L'Interfaccia Grafica è Pronta!

Ora quando clicchi su "Volleyball Scout" da `setup.sh`, vedrai direttamente l'interfaccia grafica.

---

## 🎯 Modo 1: Da setup.sh (Consigliato)

```bash
./setup.sh
```

Poi:
1. Scegli **"Volleyball Scout"** dal dialog
2. Aspetta l'avvio (2-3 secondi)
3. Vedi la finestra PyQt6

---

## 🎯 Modo 2: Comando Diretto

```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
venv/bin/python -m volleyball_scout.main
```

Oppure:

```bash
venv/bin/python run_desktop.py
```

---

## 📋 Cosa Succede all'Avvio

```
1. 🏐 Volleyball Scout v0.1 - avvio...
   └─ Inizializza il database

2. 📦 Database: SQLite | Connected: True
   └─ Connette il database locale

3. 📝 Creazione dati demo...
   ├─ Crea squadre (Cuneo vs Modena)
   ├─ Crea giocatori
   └─ Crea una partita demo

4. 🚀 Avvio interfaccia grafica PyQt6...
   └─ Si apre la finestra principale
```

---

## 🖥️ Interfaccia Principale

### Menu in Alto
```
🏐 Volleyball Scout | 📋 Dashboard | 👥 Squadre | 🎯 Matches | ❌ Esci
```

**Bottoni:**
- **📋 Dashboard** - Mostra match e sessioni (pagina iniziale)
- **👥 Squadre** - Gestisci squadre e giocatori
- **🎯 Matches** - Gestisci le partite
- **❌ Esci** - Chiude l'applicazione (con conferma)

### Dashboard (Default)
```
┌──────────────────────┬─────────────────────────────┐
│ 📋 Match Disponibili │ 📝 Sessioni in Bozza       │
├──────────────────────┼─────────────────────────────┤
│                      │                             │
│ • ID                 │ • Sessioni salvate          │
│ • Squadre            │ • Ultimi scout              │
│ • Data               │ • Stato                     │
│ • Stato              │                             │
│                      │                             │
│ [Clicca per aprire]  │ [Riprendi sessione]         │
│                      │                             │
└──────────────────────┴─────────────────────────────┘
```

---

## 👥 Pagina Squadre

**Panel Sinistro: Squadre Disponibili**
```
Nome          | Città      | Categoria
──────────────────────────────────────
Cuneo Volley  | Cuneo      | Serie A2
Modena Volley | Modena     | Serie A2
```

**Panel Destro: Aggiungi Squadra**
```
Nome:        [________________]
Città:       [________________]
Categoria:   [________________]

[➕ Aggiungi Squadra]
[🗑️ Elimina Selezionata]
```

**Panel Inferiore: Giocatori**
```
Numero | Cognome
───────────────
1      | Rossi
5      | Ferrari
9      | Bianchi
```

---

## 🎯 Pagina Matches

**Tabella Match Registrati**
```
ID | Home  | Away          | Data       | Stato
──────────────────────────────────────────────
1  | Cuneo | Modena        | 2026-05-08 | Programmato
```

**Form Crea Match**
```
Home Team ID:     [__]
Away Team ID:     [__]
Luogo:            [________________]
Competizione:     [________________]

[🔄 Aggiorna] [➕ Nuovo Match] [🗑️ Elimina]
```

---

## 🎨 Comportamento dei Bottoni

### Bottoni di Navigazione
- **Attivo (pagina corrente)**: Verde (#4CAF50) con testo bianco
- **Inattivo**: Bianco con bordo grigio
- **Hover**: Grigio chiaro
- **Click**: Grigio scuro

### Bottoni di Azione
- **Aggiungi**: Bottone azzurro
- **Elimina**: Bottone rosso (con conferma)
- **Aggiorna**: Bottone grigio
- **Esci**: Bottone rosso (con conferma)

---

## 💾 Database

**Posizione**: `~/.volleyball_scout/data/scout.db`

**Creato automaticamente con:**
- Tabelle SQLAlchemy
- Dati demo iniziali (Cuneo vs Modena)
- Logging su `~/.volleyball_scout/scout.log`

---

## 🔧 Primo Utilizzo

1. **Aggiungi una squadra** (👥 Squadre)
   - Compila nome, città, categoria
   - Clicca "Aggiungi"

2. **Aggiungi giocatori** (👥 Squadre)
   - Seleziona una squadra
   - Clicca "Aggiungi Giocatore"
   - Inserisci numero maglia e cognome

3. **Crea un match** (🎯 Matches)
   - Inserisci Home Team ID
   - Inserisci Away Team ID
   - Inserisci Luogo e Competizione
   - Clicca "Crea Match"

4. **Visualizza sulla dashboard** (📋 Dashboard)
   - Torna a Dashboard
   - Vedi i match creati
   - Seleziona per ulteriori azioni

---

## ⚙️ Configurazione

### Database Custom

Se vuoi usare un database diverso da SQLite:

```bash
export DATABASE_URL=postgresql://user:pass@host/dbname
venv/bin/python -m volleyball_scout.main
```

### Logging

I log sono salvati in: `~/.volleyball_scout/scout.log`

Livello: INFO (modifiable in `main.py`)

---

## 🐛 Troubleshooting

### Problema: "No module named 'PyQt6'"
**Soluzione:**
```bash
pip install PyQt6
```

### Problema: Database error
**Soluzione:**
```bash
# Rimuovi il database corrotto
rm -rf ~/.volleyball_scout/data/scout.db

# Riavvia l'app (ricrea il database)
venv/bin/python -m volleyball_scout.main
```

### Problema: Interfaccia non appare
**Soluzione:**
1. Controlla console per errori
2. Assicurati che il database sia connesso
3. Prova con:
   ```bash
   venv/bin/python -c "from volleyball_scout.ui.app import VolleyballScoutApp; print('✅ OK')"
   ```

### Problema: Non vedo i dati
**Soluzione:**
1. Clicca "🔄 Aggiorna" (ogni pagina)
2. Controlla di avere creato almeno una squadra
3. Verifica il database:
   ```bash
   sqlite3 ~/.volleyball_scout/data/scout.db ".tables"
   ```

---

## 📊 Componenti Utilizzati

| Componente | Ruolo |
|-----------|-------|
| **VolleyballScoutApp** | Finestra principale |
| **Menu Bar** | Navigazione in alto |
| **DashboardView** | Dashboard con match |
| **TeamManagementWidget** | Gestione squadre |
| **MatchManagementWidget** | Gestione match |
| **MatchesGridWidget** | Griglia match |
| **DraftListWidget** | Sessioni salvate |

---

## 🎯 Flusso di Utilizzo Completo

```
Start (setup.sh) → Choose "Volleyball Scout"
         ↓
main.py avvia
         ↓
Database inizializzato
         ↓
UI PyQt6 aperta
         ↓
Dashboard (Match + Draft)
         ├─→ Clicca su Squadre
         │     ├─ Aggiungi squadra
         │     └─ Aggiungi giocatori
         │
         ├─→ Clicca su Matches
         │     ├─ Crea match
         │     └─ Visualizza match
         │
         └─→ Torna a Dashboard
               └─ Vedi i match creati
```

---

## ✨ Pronto!

L'interfaccia grafica è completamente integrata. Quando clicchi su "Volleyball Scout" da setup.sh:

```
setup.sh → Volleyball Scout → ✨ Interfaccia PyQt6 aperta!
```

Buon scouting! 🏐

---

*Last Updated: 2024*
*Version: 1.0 - UI Launch Ready*
