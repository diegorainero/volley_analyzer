# 🚀 Quick Start - Setup Completo

## 1️⃣ Setup Iniziale

```bash
cd volley_analizer

# Installa dipendenze e applica migrazioni
python setup.py dev_setup
```

Oppure **manualmente**:

```bash
# Installa dipendenze
pip install -r requirements.txt

# Applica le migrazioni Alembic
alembic upgrade head
```

## 2️⃣ Verifica i Dati di Test

```bash
# Apri il database con sqlite3
sqlite3 volleyball_scout_data.db

# Query per verificare squadre
.mode column
SELECT * FROM teams;

# Query per verificare giocatori
SELECT * FROM players LIMIT 5;

# Query per verificare la migrazione
SELECT * FROM matches;
PRAGMA table_info(matches);
```

Dovresti vedere:
- ✅ 2 squadre: "Attacco" e "Cihsosla Volley"
- ✅ 28 giocatori (14 per squadra)
- ✅ Colonne `status` e `updated_at` in matches

Esci con `.quit`

## 3️⃣ Test FormationPanel

```bash
python tests/test_formation_panel_ui.py
```

Questo apre una GUI interattiva dove puoi testare il drag-drop.

## 4️⃣ Avvia l'App Principale

```bash
python run_desktop.py
```

Oppure:

```bash
python main.py
```

---

## 🧪 Test del Sistema di Bozze

Una volta avviata l'app:

1. **Dashboard** → Clicca "Nuovo Incontro"
2. **Match Management** → Seleziona "Attacco" vs "Cihsosla Volley"
3. **Roster Setup** → Seleziona giocatori
4. **Formation Panel** → Trascina i giocatori (drag-drop):
   - 6 numeri nei slot gialli (titolari)
   - 1 numero nello slot beige (libero)
5. **Scout Panel** → Registra alcuni eventi
6. **ESCI SENZA COMPLETARE** (simula crash)
7. **Riapri l'app** → Dashboard → Vedrai "Sessioni in Bozza"
8. **Clicca "▶ Riprendi"** → Torna allo scout con i dati salvati!

---

## 🔧 Troubleshooting

### "Colonna status non esiste"
```bash
# Forza l'applicazione della migrazione
alembic stamp head
alembic upgrade head
```

### "Database locato"
```bash
# Elimina il vecchio database
rm volleyball_scout_data.db

# Ricrea tutto da zero
python setup.py dev_setup
```

### "Errore di importazione PyQt6"
```bash
pip install PyQt6
```

### "AttributeError: 'NoneType' object"
Assicurati che il database sia stato creato correttamente:
```bash
alembic current  # Mostra la versione attuale
alembic history  # Mostra la storia delle migrazioni
```

---

## 📋 Checklist Finale

- [ ] Database creato (`volleyball_scout_data.db` presente)
- [ ] Squadre di test presenti (Attacco, Cihsosla Volley)
- [ ] Giocatori di test presenti (28 totali)
- [ ] Colonne `status` e `updated_at` presenti in matches
- [ ] FormationPanel funziona (drag-drop ok)
- [ ] App avvia senza errori
- [ ] Sistema di bozze funziona (salva e riprende)

---

## 📚 Documentazione

Dopo il setup, leggi:

1. **`docs/DRAFT_AND_TEST_DATA_UPDATES.md`** - Cosa è stato implementato
2. **`docs/FORMATION_PANEL.md`** - Come usare il pannello formazione
3. **`docs/DRAFT_SYSTEM.md`** - Come funziona il salvataggio automatico
4. **`docs/SCOUTING_FLOW.md`** - Flusso completo di scouting

---

## 💡 Comandi Utili

```bash
# Visualizza le bozze attuali
sqlite3 volleyball_scout_data.db "SELECT * FROM matches WHERE status='in_progress';"

# Conta i giocatori
sqlite3 volleyball_scout_data.db "SELECT team_id, COUNT(*) FROM players GROUP BY team_id;"

# Azzera tutto (ATTENZIONE!)
rm volleyball_scout_data.db
python setup.py dev_setup
```

---

**Sei pronto! Buon sviluppo! 🎉**
