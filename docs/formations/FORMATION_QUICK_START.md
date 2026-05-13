# Formation Panel Enhancements - Quick Start Guide

## 🚀 Quick Deployment

### Step 1: Eseguire la migrazione database

```bash
cd volley_analizer
alembic upgrade head
```

### Step 2: Verificare il database

```bash
# Verifica che il campo game_method sia stato aggiunto
sqlite3 volley.db ".schema matches"
```

Dovresti vedere una riga simile:
```
game_method TEXT DEFAULT 'P-S-C'
```

### Step 3: Avviare l'applicazione

```bash
python run_desktop.py
```

---

## ✅ Quick Test Checklist

### Test 1: Indicatore "P" sul palleggiatore
- [ ] Apri Formation Panel
- [ ] Verifica che i bottoni dei palleggiatori mostrino "P" accanto al numero (es. "1P")
- [ ] I non-palleggiatori mostrano solo il numero (es. "5")

### Test 2: Validazione duplicati
- [ ] Trascina giocatore #10 in slot P1
- [ ] Tenta di trascinare #10 in slot P2
- [ ] Avviso apparirà: "Il giocatore #10 è già posizionato in campo"
- [ ] Drop è rifiutato

### Test 3: Palleggiatore obbligatorio
- [ ] Seleziona 6 titolari SENZA palleggiatore
- [ ] Seleziona un metodo di gioco
- [ ] Clicca "Conferma Formazione"
- [ ] Avviso apparirà: "Seleziona almeno un palleggiatore tra i titolari"

### Test 4: Metodo di gioco
- [ ] NON selezionare nessun metodo di gioco
- [ ] Clicca "Conferma Formazione"
- [ ] Avviso apparirà: "Seleziona un metodo di gioco (P-S-C o P-C-S)"
- [ ] Seleziona "P-S-C"
- [ ] Clicca "Conferma Formazione" → ✅ Passaggio al Scout Panel

### Test 5: Persistenza nel database
- [ ] Seleziona "P-C-S" come metodo di gioco
- [ ] Completa la formazione
- [ ] Apri il database: `sqlite3 volley.db`
- [ ] Esegui: `SELECT id, game_method FROM matches LIMIT 1;`
- [ ] Verifica che `game_method` = "P-C-S"

---

## 📝 File Modificati

| File | Modifiche |
|------|-----------|
| `volleyball_scout/ui/formation_panel.py` | Indicatore "P", validazione duplicati, palleggiatore obbligatorio, metodo di gioco |
| `volleyball_scout/core/models.py` | Campo `game_method` nella classe `Match` |
| `alembic/versions/20260509_add_game_method.py` | Nuova migrazione Alembic |
| `volleyball_scout/ui/main_window.py` | Salvataggio `game_method` nel database |

---

## 🔍 Verifica Veloce

### Verificare che il codice sia corretto:

```bash
# Cercarea tutti i references a game_method
grep -r "game_method" volley_analizer/
```

Dovresti vedere:
- `models.py` - Definizione del campo
- `formation_panel.py` - Selezione e validazione
- `main_window.py` - Salvataggio nel DB
- `20260509_add_game_method.py` - Migrazione

---

## 🐛 Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| "P" non appare sui palleggiatori | Verifica che `role == "Palleggiatore"` nel DB |
| Validazione duplicati non funziona | Verifica che `formation_widget` sia assegnato agli slot |
| `game_method` non salvato | Esegui `alembic upgrade head` e ricrea il match |
| Metodo di gioco non visibile | Ricarca il Formation Panel |

---

## 📊 Dati di Test (Pre-loaded)

Le seguenti squadre e giocatori sono pre-caricati nella migrazione:

### Attacco (Team ID: 1)
- #1: Marco Rossi - **Palleggiatore**
- #2: Andrea Bianchi - Schiacciatore
- #3: Luca Verdi - Centrale
- ... (altri giocatori)
- #13, #14: Liberi

### Cihsosla Volley (Team ID: 2)
- #10: Davide Verde - **Palleggiatore**
- #11: Simone Azzurro - Schiacciatore
- ... (altri giocatori)
- #22, #23: Liberi

---

## 🎯 Casi d'uso tipici

### Caso 1: Setup completo

```
1. Seleziona "P-S-C" o "P-C-S"
2. Trascina 6 titolari (incluso almeno 1 palleggiatore)
3. Trascina 1 libero
4. Clicca "Conferma Formazione"
5. ✅ Passa al Scout Panel
```

### Caso 2: Errore - Nessun palleggiatore

```
1. Trascina 6 titolari SENZA palleggiatore
2. Clicca "Conferma Formazione"
3. ❌ Messaggio: "Seleziona almeno un palleggiatore"
4. Rimuovi un titolare, aggiungi il palleggiatore
5. ✅ Ora funziona
```

### Caso 3: Errore - Giocatore duplicato

```
1. Trascina #5 in P1
2. Tenta di trascinare #5 in P2
3. ❌ Messaggio: "Il giocatore #5 è già posizionato in campo"
4. Trascinalo in uno slot diverso
5. ✅ Adesso funziona
```

---

## 📞 Contatti

Se hai problemi:
1. Verifica i log nella console
2. Controlla il file `FORMATION_ENHANCEMENTS_SUMMARY.md` per dettagli completi
3. Verifica la sezione Troubleshooting di questo documento

---

**Status**: ✅ Implementazione Completa  
**Versione**: 1.0  
**Data**: 2024-05-09
