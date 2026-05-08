   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Esegui il setup di sviluppo**:
   ```bash
   python setup.py dev_setup
   ```
   Questo comando eseguirà automaticamente:
   - `pip install -r requirements.txt`
   - `alembic upgrade head` (per creare/aggiornare le tabelle)

---

## 🛠️ Gestione Migrazioni (Alembic)

Le migrazioni permettono di aggiornare lo schema del database senza perdere i dati (dove possibile) e di mantenere sincronizzati i modelli Python con le tabelle SQL.

### Comandi comuni:

- **Aggiorna il database all'ultima versione**:
  ```bash
  alembic upgrade head
  ```

- **Crea una nuova migrazione (autogenerata)**:
  Se hai modificato i modelli in `core/models.py`, lancia:
  ```bash
  alembic revision --autogenerate -m "descrizione modifica"
  ```

- **Torna indietro di una versione**:
  ```bash
  alembic downgrade -1
  ```

---

## 📊 Schema Database - Novità

### Tabella `match_players`
Recentemente sono stati aggiunti i seguenti campi per supportare la gestione delle formazioni:
- `is_starter` (Boolean): Indica se il giocatore fa parte dei 6 titolari iniziali del set.
- `is_libero` (Boolean): Indica se il giocatore è il libero scelto per il set.

Questi campi vengono popolati tramite il **Formation Panel** prima dell'inizio dello scouting.

---

## 🔍 Troubleshooting Comune

### 1. Errore `OperationalError: table match_players has no column named is_starter`
**Causa**: Il database non è aggiornato con l'ultima migrazione.
**Soluzione**: Esegui `alembic upgrade head`.

### 2. Errore `DetachedInstanceError`
**Causa**: Si sta tentando di accedere a un attributo di un oggetto SQLAlchemy al di fuori della sessione in cui è stato caricato.
**Soluzione**: Passare tra i widget della UI solo dizionari semplici (`dict`) o ID, invece degli oggetti ORM completi.

### 3. Errore `Target database is not up to date`
**Causa**: Il database e le migrazioni Alembic sono fuori sincrono.
**Soluzione**: 
```bash
alembic stamp head
alembic upgrade head
```

### 4. Reset completo del database (Sviluppo)
Se vuoi ricreare tutto da zero e non ti interessano i dati attuali:
```bash
rm volleyball_scout_data.db
alembic upgrade head
```

---

## ⚙️ Configurazione (alembic.ini)

Il file `alembic.ini` nella root del progetto contiene la stringa di connessione:
```ini
sqlalchemy.url = sqlite:///volleyball_scout_data.db
```
Assicurati che questo path corrisponda a quello utilizzato dall'applicazione in `core/database.py`.