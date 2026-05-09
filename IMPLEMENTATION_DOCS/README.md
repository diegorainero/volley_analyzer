# Documentazione Implementazione - Roster Setup Flow

Benvenuto! Questa cartella contiene la documentazione completa del flusso di **Roster Setup** implementato per Volleyball Scout.

## 📋 Indice della Documentazione

### 1. **ROSTER_SETUP_FLOW.md** 📖
**Il documento principale** che spiega:
- Come funziona il flusso utente step by step
- Architecture del sistema (QStackedWidget, signals, etc.)
- Layout UI dettagliato
- Funzionalità principali di RosterSetupWidget
- Data model MatchPlayer
- Signal flow tra i componenti
- 3 casi d'uso principali
- Testing e improvements futuri

**Quando leggere:** Primo approccio al sistema
**Tempo lettura:** ~15 minuti

### 2. **CHANGES_SUMMARY.md** 📝
**Sommario delle modifiche** che contiene:
- Liste dettagliate di tutti i file modificati
- Cosa è stato cambiato (linea per linea)
- Breaking changes e migration path
- Database changes (nessuno in questo caso)
- Performance considerations
- Rollback plan

**Quando leggere:** Per capire esattamente cosa è stato fatto
**Tempo lettura:** ~10 minuti

### 3. **TESTING_GUIDE.md** 🧪
**Guida al testing manuale** con:
- 5 scenari di test completi (step by step)
- Checklist di verifica finale
- Debug tips e database inspection
- Expected performance
- Known issues
- Test report template

**Quando leggere:** Prima di testare il sistema
**Tempo lettura:** ~20 minuti (esecuzione dei test: ~30 minuti)

---

## 🚀 Quick Start

### Per lo Sviluppatore che vuole capire il sistema:

1. **Leggi** `ROSTER_SETUP_FLOW.md` → Capisci il concetto globale
2. **Leggi** `CHANGES_SUMMARY.md` → Vedi cosa è stato cambiato
3. **Esegui** test da `TESTING_GUIDE.md` → Verifica che tutto funziona
4. **Modifica il codice** con fiducia!

### Per il QA/Tester:

1. **Leggi** la sezione "Prerequisiti" di `TESTING_GUIDE.md`
2. **Esegui** i 5 scenari nella guida
3. **Compila** il test report template
4. **Segnala** issues usando il formato suggerito

### Per il PM/Product Manager:

1. **Leggi** "Flusso Utente" di `ROSTER_SETUP_FLOW.md`
2. **Leggi** "Casi d'uso" di `ROSTER_SETUP_FLOW.md`
3. **Mira** ai "Possibili Miglioramenti Futuri"

---

## 📚 File Documentati

### Modificati in `volleyball_scout/ui/`:

#### 1. `new_match_dialog.py`
- **Modifiche:** Signal change from `object` to `int`
- **Linee cambiate:** 2 (linee 31, 212)
- **Breaking:** Sì, ma già gestito in formation_setup_complete.py

#### 2. `roster_setup.py`
- **Modifiche:** Complete rewrite da zero
- **Linee di codice:** ~500 (era ~50)
- **Nuove funzionalità:** 15+ metodi, doppia modalità, dialog modifica, etc.

#### 3. `formation_setup_complete.py`
- **Modifiche:** Integrazione RosterSetupWidget
- **Linee cambiate:** ~20
- **Nuova funzione:** `_open_roster_setup(match_id)`

### Non modificati:
- `database.py` - Nessuna modifica al schema
- `models.py` - MatchPlayer già existente, usato as-is
- Tutti gli altri file UI

---

## 🔄 Flusso Semplificato

```
UTENTE CLICCA "NUOVA PARTITA"
    ↓
NewMatchDialog apre
    ↓
UTENTE COMPILA DATI E CLICCA "SALVA"
    ↓
Partita salvata nel DB
Signal match_created(id) emesso
    ↓
RosterSetupWidget dialog apre automaticamente
    ↓
UTENTE SELEZIONA GIOCATORI + IMPOSTA NUMERO/RUOLO
    ↓
UTENTE CLICCA "SALVA ROSTER"
    ↓
MatchPlayer records creati/aggiornati
Signal roster_completed() emesso
    ↓
Dialog chiude
Lista match aggiornata
FormationPanel apre automaticamente
    ↓
UTENTE VEDE LA FORMAZIONE
```

---

## 🎯 Key Features Implementate

✅ **Doppia Modalità UI**
- "Selezione Partita": seleziona manualmente quale match
- "Setup per Partita": aperta automaticamente dopo creazione

✅ **Gestione Giocatori**
- Checkbox per selezione rapida
- Dialog per modifica numero/ruolo per giocatore
- Tabella live per visualizzazione roster

✅ **Sincronizzazione Dati**
- Checkbox ↔ Tabella sincronizzati
- Persistenza roster nel DB
- Caricamento roster esistente

✅ **Signal Flow**
- NewMatchDialog → RosterSetup
- RosterSetup → FormationPanel
- Tutto fully connected

✅ **Error Handling**
- Validazione giocatori minimo 1
- Graceful error messages
- No crashes

---

## 🐛 Debugging & Support

### Problema: RosterSetup non apre dopo creazione match

**Soluzione:**
1. Controlla che il signal è connesso in `formation_setup_complete.py`
2. Verifica che `_open_roster_setup()` è definito
3. Aggiungi print per tracciare:
   ```python
   print(f"DEBUG: match_id={match_id}")
   print(f"DEBUG: _open_roster_setup called")
   ```

### Problema: Giocatori non compaiono nella tabella

**Soluzione:**
1. Verifica che team ha almeno 1 giocatore nel DB
2. Aggiungi print in `_load_team_players()`:
   ```python
   print(f"DEBUG: loaded {len(players)} players")
   ```
3. Verifica il checkbox è spuntato

### Problema: Salvataggio non funziona

**Soluzione:**
1. Controlla il database con:
   ```bash
   sqlite3 ~/.volleyball_scout/data/scout.db
   SELECT * FROM match_players WHERE match_id = X;
   ```
2. Verifica che almeno un giocatore è selezionato
3. Aggiungi print in `_save_roster()`

---

## 📊 Statistics

| Metrica | Valore |
|---------|--------|
| File Modificati | 3 |
| Linee Aggiunte | ~600 |
| Linee Rimosse | ~50 |
| Nuovi Metodi | 15+ |
| Nuovi Signals | 1 |
| Query DB Cambiate | 0 (reuse MatchPlayer) |
| Breaking Changes | 1 (signal type) |

---

## 🔮 Prossimi Passi (Futuro)

### Short Term (1-2 settimane)
1. ✅ Test manuale completo (vedi TESTING_GUIDE.md)
2. ⏳ Unit tests per RosterSetupWidget
3. ⏳ Integration tests per il flusso completo

### Medium Term (1-2 mesi)
1. ⏳ Bottone "Modifica Roster" nella lista match
2. ⏳ Validazione min/max giocatori per match
3. ⏳ Template roster per squadra

### Long Term (3+ mesi)
1. ⏳ Storico versioni roster
2. ⏳ Export roster (PDF, Excel)
3. ⏳ Bulk edit numero/ruolo
4. ⏳ Drag-drop tra team

---

## 🤝 Contributing

Se trovi un bug o vuoi suggerire un miglioramento:

1. **Segnala il bug** con:
   - Passi per riprodurre
   - Behavior atteso
   - Behavior reale
   - Screenshot (se possibile)

2. **Proponi un miglioramento** con:
   - Descrizione della feature
   - Benefici per l'utente
   - Effort stimato

3. **Implementa** seguendo:
   - Code style del progetto (PyQt6, with statements)
   - Aggiungi docstrings
   - Aggiungi tests
   - Aggiorna la documentazione

---

## 📞 Contatti & Support

**Per domande sulla documentazione:**
- Controlla prima se la risposta è in uno dei 3 documenti principali
- Se no, segnala l'issue in modo che la documentazione sia migliorata

**Per domande sull'implementazione:**
- Leggi i commenti nel codice
- Aggiungi prints per tracciare il flusso
- Usa il database inspector per verificare i dati

---

## 📜 License

Come il resto del progetto Volleyball Scout.

---

## 🙏 Ringraziamenti

Implementazione completata con cura e attenzione ai dettagli!

---

**Ultima modifica:** [Data]
**Versione:** 1.0
**Status:** Production Ready
