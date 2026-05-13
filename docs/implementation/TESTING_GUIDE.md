# Testing Guide - Roster Setup Flow

## Prerequisiti

### Database Setup
```bash
# Assicurati di avere almeno:
# - 2 squadre (es. "Team A", "Team B")
# - Ogni squadra con almeno 5 giocatori
```

### Environment
```bash
cd /home/diegorainero/Documenti/personalDev/volley_analizer
python3 -m volleyball_scout  # Avvia l'applicazione
```

---

## Scenario 1: Crea Nuova Partita → Setup Roster

### Step 1: Apri Formation Setup
1. Naviga a "Formation Setup" nella UI principale
2. Dovresti vedere:
   - Pulsante "➕ Nuova Partita"
   - Tabella "Partite Disponibili" (probabilmente vuota)

### Step 2: Crea Nuova Partita
1. Clicca su "➕ Nuova Partita"
2. Dialog "Nuova Partita" apre con form:
   - Squadra A (Home) - dropdown
   - Squadra B (Away) - dropdown
   - Data e Ora - datepicker
   - Luogo - text field
   - Note - text area

3. Compila il form:
   - Squadra A: seleziona "Team A"
   - Squadra B: seleziona "Team B"
   - Data/Ora: default (now)
   - Luogo: es. "Palasport Milano"
   - Note: es. "Test match"

4. Clicca "✅ Salva"

### Step 3: Verifica che RosterSetup Apre
**ASPETTATO:** Dopo il salvataggio, dovrebbe aprirsi automaticamente un dialog "Setup Roster Partita"

**Verificare:**
- [ ] Dialog title: "🏐 Setup Roster Partita"
- [ ] Header mostra: "Team A vs Team B (data)"
- [ ] SINISTRA: "Selezione Giocatori"
- [ ] Dropdown squadra con Team A selezionato
- [ ] Lista di giocatori con checkbox

### Step 4: Seleziona Giocatori
1. Nella lista a sinistra "Giocatori Disponibili", spunta 3-5 checkbox
2. **ASPETTATO:** I giocatori compaiono nella tabella a DESTRA
3. Verifica che nella tabella appaiano:
   - Nome del giocatore
   - Numero maglia (default dal player)
   - Ruolo (default dal player)
   - Pulsante "Modifica"
   - Pulsante "Rimuovi"

### Step 5: Modifica un Giocatore
1. Clicca "Modifica" su uno dei giocatori selezionati
2. Dialog "Modifica - [Nome Giocatore]" apre con:
   - SpinBox "Numero Maglia" (0-99)
   - Dropdown "Ruolo" (Palleggiatore, Opposto, ecc.)
   - Bottoni OK/Annulla

3. Cambia il numero: es. da 3 a 13
4. Cambia il ruolo: es. da "Schiacciatore" a "Centrale"
5. Clicca "OK"

**ASPETTATO:** La tabella si aggiorna e mostra i nuovi valori

### Step 6: Cambia Team (Opzionale)
1. Nel dropdown "Squadra" cambia a "Team B"
2. **ASPETTATO:** La lista a sinistra mostra i giocatori di Team B
3. Eventualmente spunta alcuni giocatori di Team B
4. **ASPETTATO:** Compaiono nella tabella destra (insieme a quelli di Team A)

### Step 7: Salva Roster
1. Quando hai selezionato almeno 1-2 giocatori
2. Clicca "✅ Salva Roster"

**ASPETTATO:**
- [ ] Messaggio: "Roster salvato con successo! ✅"
- [ ] Dialog chiude
- [ ] Tabella "Partite Disponibili" aggiornata
- [ ] La partita appena creata dovrebbe aparire nella lista

### Step 8: Verifica Caricamento Formazione
**ASPETTATO:** Dopo la chiusura del dialog, il widget dovrebbe mostrare la FormationPanel per il match appena creato

**Verificare:**
- [ ] I giocatori del roster selezionato compaiono nel court/formazione
- [ ] Il campo mostra gli 6 giocatori in formazione

---

## Scenario 2: Modifica Roster Esistente (Futuro)

*Questa feature sarà implementata in una fase successiva con un pulsante "Modifica Roster" nella lista match.*

---

## Scenario 3: Ricarica Match con Roster

### Setup Prerequisiti
1. Hai già creato una partita con roster (da Scenario 1)

### Test
1. Chiudi completamente la UI e riapri l'applicazione
2. Torna a "Formation Setup"
3. La lista match dovrebbe mostrare la partita creata

4. Double-click sulla partita
5. **ASPETTATO:** FormationPanel si apre
6. **ASPETTATO:** I giocatori del roster salvato compaiono in formazione

---

## Scenario 4: Sincronizzazione Checkbox

### Setup
1. Nel RosterSetup con un match caricato
2. Già hai 3 giocatori selezionati nella tabella

### Test A: Uncheck un giocatore
1. Nella lista a sinistra, uncheck un giocatore che è nella tabella
2. **ASPETTATO:** Il giocatore è rimosso dalla tabella destra

### Test B: Check un nuovo giocatore
1. Nella lista a sinistra, check un nuovo giocatore
2. **ASPETTATO:** Appare nella tabella destra con numero/ruolo di default

### Test C: Rimuovi un giocatore
1. Clicca "Rimuovi" su un giocatore nella tabella
2. **ASPETTATO:** 
   - Giocatore scomparso dalla tabella
   - Checkbox a sinistra è unchecked

---

## Scenario 5: Error Handling

### Test A: Salva senza giocatori
1. Seleziona 0 giocatori
2. Clicca "✅ Salva Roster"
3. **ASPETTATO:** Messaggio warning: "Seleziona almeno un giocatore"

### Test B: Team non trovato
1. Nel database, elimina una squadra mentre RosterSetup è aperto
2. Cambia il dropdown squadra
3. **ASPETTATO:** Gestione graceful, nessun crash

### Test C: Match non trovato
1. Nel database, elimina il match mentre RosterSetup è aperto
2. Prova a salvare
3. **ASPETTATO:** Messaggio di errore, nessun crash

---

## Checklist di Verifica Finale

### Frontend
- [ ] NewMatchDialog ha signal `match_created(int)`
- [ ] RosterSetupWidget si apre automaticamente dopo creazione match
- [ ] Checkbox sincronizzati con tabella
- [ ] Dialog modifica numero/ruolo funziona
- [ ] Salvataggio emoji ✅ mostra messaggio di successo
- [ ] Dialog si chiude dopo salvataggio
- [ ] FormationPanel si apre automaticamente

### Database
- [ ] MatchPlayer records creati correttamente
- [ ] Numero e ruolo salvati come specificato
- [ ] Roster persistente tra sessioni
- [ ] DELETE + INSERT al salvataggio

### Edge Cases
- [ ] Giocatore rimosso dopo selezione
- [ ] Match cancellato durante setup
- [ ] Squadra con 0 giocatori
- [ ] Numero non valido (< 0 o > 99)
- [ ] Role vuoto

---

## Debug Tips

### Logs
Se qualcosa non funziona, controlla i logs:
```bash
# Usa print statements oppure logging module
# I prints appaiono nella console dove hai lanciato l'app
```

### Database Inspection
```bash
# Apri il database SQLite
sqlite3 ~/.volleyball_scout/data/scout.db

# Verifica MatchPlayer records
SELECT * FROM match_players WHERE match_id = <match_id>;

# Verifica Match records
SELECT * FROM matches ORDER BY created_at DESC LIMIT 5;
```

### PyQt Debugging
```python
# Aggiungi prints negli slot per tracciare:
print(f"DEBUG: _on_team_changed called with index={index}")
print(f"DEBUG: selected_players = {self.selected_players}")
```

---

## Expected Performance

### UI Responsiveness
- **Dialog apre:** < 500ms
- **Cambia team:** < 200ms
- **Seleziona giocatore:** Istantaneo
- **Salva roster:** < 1000ms

### Database Operations
- **Load match:** 1 query
- **Load team players:** 1 query
- **Save roster:** ~2 queries (DELETE + INSERT)

### Memory
- Non dovrebbe crescere indefinitamente
- Dialog chiude → memoria liberata

---

## Known Issues & Limitations

### Attuali
1. **Nessun bottone "Modifica Roster"** dalla lista match
   - *Soluzione:* Implementare bottone nella lista match che apre RosterSetup

2. **Nessuna validazione** su numero giocatori minimo/massimo
   - *Soluzione:* Aggiungere validazione nel _save_roster()

3. **Nessun template** di roster
   - *Soluzione:* Feature per salvare template per squadra

### Future Improvements
- [ ] Bulk edit numero/ruolo
- [ ] Drag-drop tra team
- [ ] Storico versioni roster
- [ ] Export roster (PDF, Excel)

---

## Test Report Template

```markdown
## Test Report - Roster Setup

**Date:** [data]
**Tester:** [nome]
**Build:** [versione]

### Test Cases Executed
- [ ] Scenario 1: Crea Nuova Partita → Setup Roster
- [ ] Scenario 2: Modifica Roster Esistente
- [ ] Scenario 3: Ricarica Match con Roster
- [ ] Scenario 4: Sincronizzazione Checkbox
- [ ] Scenario 5: Error Handling

### Issues Found
1. [Descrizione issue]
   - Severity: [Critical/High/Medium/Low]
   - Steps to Reproduce: [...]
   - Expected: [...]
   - Actual: [...]
   - Environment: [...]

### Conclusion
[PASSED / FAILED / PARTIAL]

**Signature:** ________________
```

---

## Contact & Support

Per domande o problemi durante il testing:
1. Controlla i logs nell'applicazione
2. Usa il database inspector per verificare i dati
3. Aggiungi prints nel codice per tracciare il flusso
