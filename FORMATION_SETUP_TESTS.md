# Formation Setup - Guida ai Test

## 📋 Test della Logica (Senza Dipendenze)

Esegui il test di logica pura per verificare le strutture dati:

```bash
cd volley_analizer
python3 test_formation_logic.py
```

**Output atteso**:
```
============================================================
🧪 TEST DATA STRUCTURES FOR FORMATION PANEL
============================================================

✅ Strutture dati simulate:
  Teams: [{'id': 1, 'name': 'Team A'}, {'id': 2, 'name': 'Team B'}]
  Players by team:
    Team 1: 3 giocatori
      - #1 Rossi (Palleggiatore)
      - #2 Bianchi (Schiacciatore)
      - #3 Verdi (Centrale)
    Team 2: 2 giocatori
      - #1 Neri (Palleggiatore)
      - #2 Blu (Schiacciatore)

✅ Validazione strutture dati:
  ✓ teams è una lista
  ✓ Ogni team ha 'id' e 'name'
  ✓ players_by_team è un dict
  ✓ players_by_team è correttamente strutturato

============================================================
✅ TUTTE LE VERIFICHE PASSATE
============================================================

🧪 TEST APPLICAZIONE LOGIC
============================================================

📝 Simulazione _refresh_formation_panel():
  1. Carico teams e players dal DB
     ✓ Teams caricati: 2
     ✓ Players caricati: 2
  2. Verifico se ci sono squadre
     ✓ Ci sono 2 squadre, creerò FormationPanel
     ✓ Parametri: teams=[...], players_by_team=2 teams

  3. Sostituisco il widget nella stack
     ✓ Widget old rimosso
     ✓ Widget new inserito all'indice 3

✅ Logica corretta!

🎉 TUTTI I TEST PASSATI!
```

## 🔍 Test di Sintassi

Verifica che il codice Python sia valido:

```bash
cd volley_analizer

# Test app.py
python3 -m py_compile volleyball_scout/ui/app.py
echo "✅ app.py sintassi OK"

# Test formation_panel.py
python3 -m py_compile volleyball_scout/ui/formation_panel.py
echo "✅ formation_panel.py sintassi OK"
```

## 🧪 Test di Integrazione (Richiede Dipendenze)

### Prerequisito: Installazione Dipendenze

```bash
# Opzione 1: In un ambiente virtuale (CONSIGLIATO)
cd volley_analizer
python3 -m venv venv
source venv/bin/activate  # su Windows: venv\Scripts\activate
pip install -r requirements.txt

# Opzione 2: Installazione minimale (solo per test)
pip install SQLAlchemy==2.0.36 PyQt6==6.7.1
```

### Test di Database e FormationPanel

```bash
# Se hai installato le dipendenze
cd volley_analizer
python3 test_formation_setup.py
```

**Output atteso**:
```
============================================================
🧪 TEST FORMATION SETUP
============================================================

🔍 Testando connessione al database...
✅ Database connesso

🔍 Testando caricamento squadre e giocatori...
  📊 Squadre trovate: 0  # (0 se database vuoto)
  
✅ Dati caricati con successo
  Teams: 0
  Players by team: []

🧪 TEST COMPLETATO
```

## 🎮 Test Manuale Completo

### Step 1: Prepara l'Ambiente

```bash
cd volley_analizer

# Crea venv e installa dipendenze
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Avvia l'Applicazione

```bash
python3 -m volleyball_scout.ui.app
```

L'app dovrebbe avviarsi mostrando il Dashboard.

### Step 3: Aggiungi Dati di Test

1. Clicca su **"👥 Teams & Players"** nel menu a sinistra
2. Clicca su **"➕ Aggiungi Squadra"** (se il pulsante esiste)
3. Compila il form:
   - **Nome Squadra**: "Team A"
   - **Short Name**: "TA"
   - **Categoria**: "A1"
   - Clicca **"Salva"**
4. Ripeti per aggiungere "Team B"
5. Per ogni squadra, aggiungi giocatori:
   - Clicca su una squadra
   - Clicca **"➕ Aggiungi Giocatore"**
   - Compila:
     - **Numero**: 1
     - **Cognome**: "Rossi"
     - **Ruolo**: "Palleggiatore"
   - Aggiungi altri 11 giocatori (totale 12 per squadra)

### Step 4: Testa Formation Setup

1. Clicca su **"🏐 Formation Setup"** nel menu
2. **Verifica che appaia**:
   - Titolo: "Inserisci la Formazione Iniziale"
   - Due sezioni laterali (Team A e Team B)
   - Lista di giocatori per ogni squadra
   - Campi per posizionare i giocatori in campo

3. **Testa le funzionalità**:
   - Drag & drop di giocatori nei slot
   - Bottone "🔄 Ruota" per la rotazione
   - Selezione del metodo di gioco (P-S-C vs P-C-S)
   - Bottone "✅ Conferma Formazione"

### Step 5: Verifica Comportamento Dopo Refresh

1. Torna a "👥 Teams & Players"
2. Aggiungi un nuovo giocatore
3. Torna a "🏐 Formation Setup"
4. **Verifica che il nuovo giocatore appaia** nella lista

## 📊 Checklist di Verifica

- [ ] Sintassi di `app.py` è corretta
- [ ] Sintassi di `formation_panel.py` è corretta
- [ ] Test di logica passa
- [ ] Nessun metodo `_refresh_formation_panel()` duplicato
- [ ] Database si connette correttamente
- [ ] Teams vengono caricati dal database
- [ ] Giocatori vengono caricati dal database
- [ ] FormationPanel si mostra con i dati corretti
- [ ] Clicking su "Formation" ricarica i dati
- [ ] Nuovo giocatore appare dopo aggiunta

## 🐛 Se Qualcosa Non Funziona

### Problema: "No teams in database" persiste

**Soluzione**:
1. Verifica che hai aggiunto almeno una squadra in "Teams & Players"
2. Controlla che il database sia salvato (file in `~/.volleyball_scout/data/scout.db`)
3. Aggiungi debug print in `_refresh_formation_panel()`:

```python
print(f"DEBUG: Teams loaded: {teams}")
print(f"DEBUG: Players by team: {players_by_team}")
```

### Problema: Errore "FormationPanel non riceve dati"

**Soluzione**:
1. Verifica che `_refresh_formation_panel()` venga chiamato
2. Controlla che i dati siano nel formato corretto:
   - `teams`: lista di dict con "id" e "name"
   - `players_by_team`: dict con team_id come chiave

### Problema: Click su "Formation" non fa nulla

**Soluzione**:
1. Controlla i log nella console per errori
2. Verifica che `_on_section_selected()` venga chiamato:
   ```python
   print(f"Section selected: {section_id}")
   ```
3. Verifica che `self.db` sia disponibile

## 📝 Note di Implementazione

- Formation Panel è **ricaricato ogni volta che clicchi su "Formation"**
- Questo garantisce che i dati siano sempre sincronizzati con il database
- Se il database è vuoto, mostra un placeholder

## 🎯 Stato Finale

La fix è **completa** quando:
1. ✅ No duplicazione di `_refresh_formation_panel()`
2. ✅ Singola chiamata in `_on_section_selected()`
3. ✅ FormationPanel si carica con dati dal database
4. ✅ Nessun errore in console
5. ✅ I giocatori vengono mostrati correttamente
