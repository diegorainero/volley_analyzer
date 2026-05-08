# 📚 Indice - Database Check Tools

Guida per navigare la documentazione e gli strumenti di verifica del database.

---

## 🚀 Inizio Rapido (Leggi Questo Primo!)

### Per utenti che vogliono verificare subito i dati

📖 **Leggi:** [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md)  
⏱️ **Tempo:** 5 minuti  
🎯 **Contiene:** Quick start, esempi, troubleshooting semplice

```bash
python3 check_database_ui.py
```

---

## 📖 Documentazione Completa

### 1. **Quick Start** - Primo approccio
📖 [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md)

- Opzioni di esecuzione (CLI vs GUI)
- Cosa vedi in ogni tab
- Esempi di dati
- Setup iniziale (dipendenze, migrazione DB)
- Casi d'uso comuni
- Troubleshooting rapido
- Pro tips
- Prossimi passi

**Per chi:** Utenti finali che vogliono subito dei risultati

---

### 2. **Guida Completa** - Approfondimento
📖 [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md)

- Requisiti e dipendenze (nel dettaglio)
- CLI - Come eseguire e interpretare output
- GUI - Tutte le funzionalità
- Struttura database (schema SQL completo)
- Posizioni database (SQLite locale vs PostgreSQL cloud)
- Troubleshooting dettagliato con soluzioni
- Tips avanzati
- Integrazione nel proprio codice
- Riferimenti ai file sorgente

**Per chi:** Sviluppatori e power users

---

### 3. **Riepilogo Strumenti** - Panoramica
📖 [`DATABASE_CHECK_SUMMARY.md`](DATABASE_CHECK_SUMMARY.md)

- Descrizione dettagliata di ogni tool creato
- Quando usare ogni strumento
- Utilità fornite (DatabaseManager API, Models ORM)
- Struttura file
- Relazioni tra file
- Launcher entry points
- Best practices
- Checklist di utilizzo

**Per chi:** Chi vuole capire cosa è stato creato e come funziona

---

### 4. **Panoramica Totale** - Tutti gli strumenti
📖 [`TOOLS_SUMMARY.md`](TOOLS_SUMMARY.md)

- Launcher principali (Volleyball Scout UI)
- Database Check Tools (CLI e GUI)
- Database Manager API (utilizzazione programmatitica)
- Alembic Migrations
- SQLAlchemy Models
- Use cases completi con codice
- File structure completa
- Data flow diagram
- Configuration
- Documentazione aggiuntiva

**Per chi:** Sviluppatori che vogliono una visione d'insieme del progetto

---

### 5. **Questo File** - Navigazione
📖 [`DATABASE_TOOLS_INDEX.md`](DATABASE_TOOLS_INDEX.md)

Guida per trovare la documentazione giusta.

---

## 🖥️ Strumenti Disponibili

### CLI Tool - Riga di Comando
📄 **File:** `check_database.py`

**Esecuzione:**
```bash
python3 check_database.py
```

**Vantaggi:**
- ✅ Veloce e leggero
- ✅ Nessuna GUI
- ✅ Output copiabile
- ✅ Perfetto per script

**Documentazione:** [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md#opzione-2️⃣---riga-di-comando-veloce) → [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md#opzione-1-cli-command-line-interface)

---

### GUI Tool - Interfaccia Grafica
📄 **File:** `check_database_ui.py`

**Esecuzione:**
```bash
python3 check_database_ui.py
```

**Vantaggi:**
- ✅ Interfaccia intuitiva
- ✅ Tabelle ben formattate
- ✅ Refresh in tempo reale
- ✅ 3 tab organizzati

**Documentazione:** [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md#opzione-1️⃣---interfaccia-grafica-consigliato) → [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md#opzione-2-gui-graphical-user-interface)

---

### Launcher Script
📄 **File:** `launch_database_check.py`

**Esecuzione:**
```bash
python3 launch_database_check.py
```

**Scopo:** Entry point conveniente per la GUI

---

## 🎯 Navigazione per Caso d'Uso

### "Voglio verificare velocemente le squadre"
1. Leggi: [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md) (5 min)
2. Esegui: `python3 check_database_ui.py`
3. ✅ Fatto!

---

### "Voglio capire come funziona tutto"
1. Leggi: [`DATABASE_CHECK_SUMMARY.md`](DATABASE_CHECK_SUMMARY.md) (10 min)
2. Leggi: [`TOOLS_SUMMARY.md`](TOOLS_SUMMARY.md) (15 min)
3. Esplora il codice in `volleyball_scout/core/`

---

### "Ricevo un errore, come lo risolvo?"
1. Leggi: [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md#-problemi) (quick fix)
2. Se non risolve: [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md#-troubleshooting) (soluzioni dettagliate)

---

### "Voglio integrare i dati nel mio script"
1. Leggi: [`TOOLS_SUMMARY.md`](TOOLS_SUMMARY.md#-database-management) (Use Cases)
2. Cerca l'esempio che ti serve
3. Copia il codice e adatta

---

### "Voglio aggiungere nuove squadre"
1. Leggi: [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md#voglio-aggiungere-nuove-squadre)
2. Segui le istruzioni (GUI o script)

---

### "Voglio approfondire la struttura database"
1. Leggi: [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md#️-struttura-database) (Schema SQL)
2. Consulta: `volleyball_scout/core/models.py` (Modelli ORM)

---

## 📊 Gerarchia di Lettura

### Livello 1 - Inizio
Leggi in questo ordine per iniziare:
```
1. README_DATABASE_CHECK.md        (5 min)  - Quick Start
2. check_database_ui.py             (30 sec) - Esegui!
```

### Livello 2 - Intermedio
Approfondisci:
```
3. DATABASE_CHECK_GUIDE.md          (15 min) - Dettagli
4. DATABASE_CHECK_SUMMARY.md        (10 min) - Panoramica strumenti
```

### Livello 3 - Avanzato
Sviluppa e integra:
```
5. TOOLS_SUMMARY.md                 (20 min) - Tutti gli strumenti
6. volleyball_scout/core/           (--) - Leggi il codice
```

---

## 📚 Mappa Veloce

| Documento | Lunghezza | Target | Per Cosa |
|-----------|-----------|--------|---------|
| README_DATABASE_CHECK.md | 5-10 min | **Tutti** | Start veloce |
| DATABASE_CHECK_GUIDE.md | 20 min | Sviluppatori | Approfondimento |
| DATABASE_CHECK_SUMMARY.md | 15 min | Sviluppatori | Cosa è stato creato |
| TOOLS_SUMMARY.md | 25 min | Sviluppatori | Panoramica totale |
| DATABASE_TOOLS_INDEX.md | 5 min | **Tutti** | Questa guida |

---

## 🔗 Cross-Reference

### Voglio sapere di...

**...come eseguire la CLI**
→ [`README_DATABASE_CHECK.md#opzione-2️⃣`](README_DATABASE_CHECK.md#opzione-2️⃣---riga-di-comando-veloce)  
→ [`DATABASE_CHECK_GUIDE.md#opzione-1-cli`](DATABASE_CHECK_GUIDE.md#opzione-1-cli-command-line-interface)

**...come usare la GUI**
→ [`README_DATABASE_CHECK.md#opzione-1️⃣`](README_DATABASE_CHECK.md#opzione-1️⃣---interfaccia-grafica-consigliato)  
→ [`DATABASE_CHECK_GUIDE.md#opzione-2-gui`](DATABASE_CHECK_GUIDE.md#opzione-2-gui-graphical-user-interface)

**...la struttura del database**
→ [`DATABASE_CHECK_GUIDE.md#️-struttura-database`](DATABASE_CHECK_GUIDE.md#️-struttura-database)  
→ `volleyball_scout/core/models.py` (codice)

**...l'API DatabaseManager**
→ [`TOOLS_SUMMARY.md#-database-management`](TOOLS_SUMMARY.md#-database-management)  
→ `volleyball_scout/core/database.py` (codice)

**...integrazione nel codice**
→ [`TOOLS_SUMMARY.md#-database-management`](TOOLS_SUMMARY.md#-database-management)  
→ [`TOOLS_SUMMARY.md#case-4-integrare-nel-formation-panel`](TOOLS_SUMMARY.md#case-4-integrare-nel-formation-panel)

**...setup iniziale**
→ [`README_DATABASE_CHECK.md#-setup-iniziale`](README_DATABASE_CHECK.md#-setup-iniziale-solo-una-volta)  
→ [`DATABASE_CHECK_GUIDE.md#-requisiti`](DATABASE_CHECK_GUIDE.md#-requisiti)

**...troubleshooting**
→ [`README_DATABASE_CHECK.md#-problemi`](README_DATABASE_CHECK.md#-problemi)  
→ [`DATABASE_CHECK_GUIDE.md#-troubleshooting`](DATABASE_CHECK_GUIDE.md#-troubleshooting)

---

## ✅ Checklist Rapida

- [ ] Leggi [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md) (quick start)
- [ ] Installa dipendenze: `pip install -r requirements.txt`
- [ ] Esegui uno dei check tools: `python3 check_database_ui.py`
- [ ] Verifica che vedi i dati
- [ ] Leggi [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md) per approfondire (opzionale)

---

## 🎓 Prossimi Passi

Dopo aver verificato il database:

1. **Formation Panel** - Scegli titolari e libero
2. **Scout & Video** - Registra gli eventi
3. **Statistics** - Visualizza i dati

Vedi [`TOOLS_SUMMARY.md`](TOOLS_SUMMARY.md#case-4-integrare-nel-formation-panel) per dettagli.

---

## 📞 Need Help?

1. **Quick question?** → Leggi [`README_DATABASE_CHECK.md`](README_DATABASE_CHECK.md#-problemi)
2. **Technical problem?** → Consulta [`DATABASE_CHECK_GUIDE.md`](DATABASE_CHECK_GUIDE.md#-troubleshooting)
3. **Want to learn everything?** → Leggi [`TOOLS_SUMMARY.md`](TOOLS_SUMMARY.md)
4. **Code reference?** → Vedi `volleyball_scout/core/models.py` e `database.py`

---

## 📝 File Structure

```
📚 Database Check Documentation:
├── README_DATABASE_CHECK.md          📖 Quick Start (LEGGI QUESTO PRIMA)
├── DATABASE_CHECK_GUIDE.md           📙 Guida Completa
├── DATABASE_CHECK_SUMMARY.md         📘 Riepilogo Strumenti
├── TOOLS_SUMMARY.md                  📕 Panoramica Totale
└── DATABASE_TOOLS_INDEX.md           📑 Questo File (Navigazione)

🛠️ Strumenti Eseguibili:
├── check_database.py                 🖥️ CLI Tool
├── check_database_ui.py              🎨 GUI Tool
└── launch_database_check.py          🚀 Launcher

💾 Source Code:
└── volleyball_scout/
    └── core/
        ├── database.py               🗄️ DatabaseManager
        └── models.py                 📊 ORM Models
```

---

## 🔄 Versioning

**Versione:** 1.0  
**Data:** 2025-01-15  
**Stato:** ✅ Completo

---

**Suggerimento:** Bookmark questa pagina per facile accesso a tutta la documentazione! 📌

