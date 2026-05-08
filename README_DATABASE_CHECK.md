# 🏐 Verifica Database - Guida Rapida

Hai chiesto di **verificare dal database le squadre inserite e mostrare le varie squadre**.

Ecco come fare in pochi secondi!

---

## 🚀 Quick Start (30 secondi)

### Opzione 1️⃣ - Interfaccia Grafica (Consigliato)

```bash
cd volley_analizer
python3 check_database_ui.py
```

Si apre una finestra con **3 tab**:
- 📊 **Squadre** - Elenco di tutte le squadre
- 👥 **Giocatori** - Tutti i giocatori per squadra
- 🏐 **Partite** - Tutte le partite registrate

**Perfetto per:** Visualizzazione rapida e intuitiva

---

### Opzione 2️⃣ - Riga di Comando (Veloce)

```bash
cd volley_analizer
python3 check_database.py
```

Mostra nel terminale:
```
✅ Connessione al database riuscita!
   Database: SQLite (~/.volleyball_scout/data/scout.db)
   Connesso: True

================================================================================
  📊 SQUADRE (2)
================================================================================

ID    Nome                           Categoria            Impianto             Giocatori 
-------------------------------------------------------------------------------------
1     Attacco                        Test                 Palazzetto           7
2     Cihsosla Volley                Test                 Palazzetto           14

================================================================================
  👥 GIOCATORI PER SQUADRA
================================================================================

🔹 Attacco (7 giocatori)
  #     Nome                 Cognome              Ruolo                Libero     Capitano  
  1     Marco                Rossi                Palleggiatore        -          -         
  2     Andrea               Bianchi              Schiacciatore        -          -         
  ...
```

**Perfetto per:** Output rapido, log, script

---

## 📊 Cosa Vedi

### Tab Squadre
Una tabella con:
- **ID** - Numero identificativo
- **Nome** - Nome della squadra (es. "Attacco", "Cihsosla Volley")
- **Categoria** - Categoria (es. "Serie A1", "Under 18")
- **Impianto** - Impianto di gioco
- **Giocatori** - Quanti giocatori ha la squadra

### Tab Giocatori
Una tabella con:
- **Squadra** - A quale squadra appartiene
- **#** - Numero di maglia
- **Nome** - Nome del giocatore
- **Cognome** - Cognome del giocatore
- **Ruolo** - Palleggiatore, Schiacciatore, Centrale, etc.
- **Libero** - ✓ se è libero, altrimenti -
- **Capitano** - ✓ se è capitano, altrimenti -

### Tab Partite
Una tabella con:
- **ID** - Numero identificativo della partita
- **Casa** - Squadra in casa
- **Trasferta** - Squadra in trasferta
- **Data** - Data e ora della partita
- **Stato** - draft, in_progress, completed

---

## 📝 Esempio Dati

Se hai caricato i dati di test, vedrai:

**Squadre:**
```
ID | Nome              | Categoria | Impianto   | Giocatori
1  | Attacco           | Test      | Palazzetto | 7
2  | Cihsosla Volley   | Test      | Palazzetto | 14
```

**Giocatori (Attacco):**
```
# | Nome    | Cognome | Ruolo             | Libero | Capitano
1 | Marco   | Rossi   | Palleggiatore     | -      | -
2 | Andrea  | Bianchi | Schiacciatore     | -      | -
3 | Luca    | Verdi   | Centrale          | -      | -
...
```

---

## 🛠️ Setup Iniziale (Solo una volta)

Se è la prima volta, installa le dipendenze:

```bash
# Posizionati nella cartella del progetto
cd volley_analizer

# Installa dipendenze
pip install -r requirements.txt

# Inizializza il database
alembic upgrade head

# (Opzionale) Carica dati di test
alembic upgrade 20260508_add_status_match_test
```

Fatto! Ora puoi usare i comandi di verifica.

---

## 🎯 Casi d'Uso

### "Voglio solo vedere velocemente le squadre"
```bash
python3 check_database.py
```
→ Output nel terminale in pochi secondi

---

### "Voglio una visualizzazione grafica"
```bash
python3 check_database_ui.py
```
→ Si apre una finestra con tabelle ben formattate

---

### "Voglio esportare i dati a file"
```bash
python3 check_database.py > squadre_e_giocatori.txt
```
→ Salva l'output in un file di testo

---

### "Voglio aggiungere nuove squadre"
1. Avvia l'app principale:
   ```bash
   python3 volleyball_scout/run_ui.py
   ```

2. Vai al tab **"👥 Team & Players"**

3. Clicca **"➕ Aggiungi Squadra"**

4. Compila il form e salva

---

## 🆘 Problemi?

### Errore: "No module named 'sqlalchemy'"
```bash
pip install -r requirements.txt
```

### Errore: "Impossibile connettere il database"
Il database è vuoto o non inizializzato. Esegui:
```bash
alembic upgrade head
alembic upgrade 20260508_add_status_match_test
```

### Nessun dato visibile
Il database è vuoto. Aggiungi squadre tramite l'UI principale o carica i dati di test (comando sopra).

---

## 📚 Approfondimenti

Per informazioni più dettagliate, consulta:
- **DATABASE_CHECK_GUIDE.md** - Guida completa
- **TOOLS_SUMMARY.md** - Tutti gli strumenti disponibili
- **volleyball_scout/core/models.py** - Struttura dei dati

---

## 💡 Pro Tips

### Aggiorna i dati in tempo reale
Nella GUI, clicca il pulsante **🔄 Aggiorna Dati**

### Controlla quale database usi
Nel tab Squadre o Giocatori, leggi l'header in alto:
```
✅ Database connesso: SQLite (~/.volleyball_scout/data/scout.db)
```
oppure
```
✅ Database connesso: PostgreSQL (cloud.railway.app)
```

### Integra nel tuo codice
```python
from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Team

db = DatabaseManager()
with db.session_scope() as session:
    teams = session.query(Team).all()
    for team in teams:
        print(f"{team.name}: {len(team.players)} giocatori")
```

---

## 🎓 Prossimi Passi

Dopo aver verificato i dati:

1. **Formation Panel** - Scegli i titolari e il libero
   ```bash
   python3 volleyball_scout/run_ui.py
   # → Vai su "🏐 Formation"
   ```

2. **Scout & Video** - Registra gli eventi della partita
   ```bash
   python3 volleyball_scout/run_ui.py
   # → Vai su "📝 Scout & Video"
   ```

3. **Statistiche** - Visualizza i dati della partita
   ```bash
   python3 volleyball_scout/run_ui.py
   # → Vai su "📈 Statistics"
   ```

---

**Fatto!** ✅

Ora hai due modi per verificare le squadre nel database. Scegli quello che preferisci!

**Domande?** Consulta la documentazione dettagliata nei file `.md`.

---

*Ultima modifica: 2025-01-15*
