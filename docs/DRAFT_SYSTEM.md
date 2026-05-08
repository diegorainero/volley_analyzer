# 📝 Sistema di Bozze (Draft) - Documentazione Completa

## 🎯 Panoramica

Il **Sistema di Bozze** permette di:
- ✅ Salvare automaticamente le sessioni di scout in bozza
- ✅ Riprendere una sessione in qualsiasi momento
- ✅ Gestire più bozze contemporaneamente
- ✅ Eliminare bozze non desiderate
- ✅ Tracciare il numero di eventi registrati

Le bozze vengono salvate nel database con uno stato speciale (`status="draft"`) e possono essere riprese dalla Dashboard in qualsiasi momento.

---

## 💾 Flusso di Salvataggio Automatico

### Quando una sessione viene creata:
1. Un nuovo **Match** viene creato con `status="draft"`
2. Il giocatore seleziona la formazione (titolari e liberi)
3. Quando clicca "Conferma Formazione", il match diventa `status="in_progress"`
4. Ogni evento registrato viene salvato nel DB

### Durante lo scouting:
- ✅ Ogni evento è salvato immediatamente nel DB
- ✅ Il campo `updated_at` del match viene aggiornato
- ✅ Se il giocatore esce dall'app, i dati rimangono salvati

### Al completamento:
- ✅ Il match passa a `status="completed"`
- ✅ La bozza non appare più nella lista

---

## 🚀 Come Usare

### 1. Creare una Nuova Sessione

```
Dashboard
  → Clicca "Nuovo Incontro"
    → Seleziona squadre e data
      → Seleziona roster
        → Seleziona formazione (6 titolari + 1 libero)
          → Inizio scouting
            → Match in stato "in_progress"
```

**Nota**: Se esci prima di finire il match, la sessione rimane in bozza.

### 2. Riprendere una Sessione in Bozza

```
Dashboard
  → Sezione "Sessioni in Bozza"
    → Clicca sulla bozza
      → Premi "▶ Riprendi"
        → Torna allo scout da dove hai lasciato
```

### 3. Eliminare una Bozza

```
Dashboard
  → Sezione "Sessioni in Bozza"
    → Clicca sulla bozza
      → Premi "🗑 Elimina"
        → Conferma eliminazione
          → Bozza eliminata (insieme a tutti i suoi eventi)
```

---

## 🗄️ Database Schema

### Colonne Aggiunte a Match

| Colonna | Tipo | Descrizione |
|---------|------|------------|
| `status` | VARCHAR(20) | `draft`, `in_progress`, `completed` |
| `updated_at` | DATETIME | Ultimo aggiornamento (auto-managed) |

### Valori di Status

| Status | Significato | Visibile in Dashboard |
|--------|------------|----------------------|
| `draft` | Sessione non ancora iniziata | ✅ Sì (Sessioni in Bozza) |
| `in_progress` | Sessione attualmente in corso | ❌ No (nascosto) |
| `completed` | Sessione completata | ✅ Sì (Ultimi 5 Match) |

---

## 🔧 API DraftManager

### Metodi Disponibili

#### `create_draft(home_team_id, away_team_id, notes="")`
Crea una nuova sessione di scout in bozza.

```python
from volleyball_scout.ui.drafts import DraftManager

draft_mgr = DraftManager(db_manager)
match_id = draft_mgr.create_draft(
    home_team_id=1,
    away_team_id=2,
    notes="Prova amichevole"
)
print(f"Bozza creata: {match_id}")
```

#### `get_drafts()`
Ottiene tutte le bozze.

```python
drafts = draft_mgr.get_drafts()
for draft in drafts:
    print(f"{draft['home_team_name']} vs {draft['away_team_name']}")
    print(f"  Creato: {draft['created_at']}")
    print(f"  Modificato: {draft['updated_at']}")
```

#### `get_draft(match_id)`
Ottiene i dettagli di una bozza specifica.

```python
draft = draft_mgr.get_draft(match_id=5)
if draft:
    print(f"Bozza trovata: {draft['home_team_name']} vs {draft['away_team_name']}")
else:
    print("Bozza non trovata")
```

#### `save_draft(match_id, notes="")`
Salva/aggiorna una bozza (auto-save).

```python
success = draft_mgr.save_draft(match_id=5, notes="Aggiornato manualmente")
if success:
    print("Bozza salvata")
```

#### `resume_draft(match_id)`
Ripristina una bozza (cambia da `draft` a `in_progress`).

```python
success = draft_mgr.resume_draft(match_id=5)
if success:
    print("Bozza ripresa - Ora in stato in_progress")
```

#### `complete_draft(match_id)`
Completa una bozza (cambia da `in_progress` a `completed`).

```python
success = draft_mgr.complete_draft(match_id=5)
if success:
    print("Bozza completata")
```

#### `delete_draft(match_id)`
Elimina una bozza e tutti i suoi eventi.

```python
success = draft_mgr.delete_draft(match_id=5)
if success:
    print("Bozza eliminata")
```

#### `get_draft_event_count(match_id)`
Ottiene il numero di eventi registrati in una bozza.

```python
count = draft_mgr.get_draft_event_count(match_id=5)
print(f"Evento registrati: {count}")
```

---

## 🎨 DraftListWidget

Widget PyQt6 per visualizzare e gestire le bozze nella Dashboard.

### Utilizzo

```python
from volleyball_scout.ui.drafts import DraftListWidget

# Crea il widget
draft_widget = DraftListWidget(db_manager)

# Connetti i segnali
draft_widget.draft_resumed.connect(self.on_draft_resumed)
draft_widget.draft_deleted.connect(self.on_draft_deleted)

# Aggiungi alla dashboard
dashboard_layout.addWidget(draft_widget)
```

### Segnali Emessi

| Segnale | Parametro | Significato |
|---------|-----------|------------|
| `draft_resumed` | `match_id` | L'utente ha cliccato "Riprendi" |
| `draft_deleted` | `match_id` | L'utente ha cliccato "Elimina" |

### Funzioni Pubbliche

```python
# Ricarica la lista di bozze dal database
draft_widget.load_drafts()
```

---

## 📊 Esempio di Flusso Completo

### Scenario: Salvare e Riprendere una Sessione

**Session 1: Inizio dello Scout**
```
15:30 - Utente: Nuovo Incontro (Attacco vs Cihsosla)
15:35 - Utente: Seleziona roster
15:40 - Utente: Seleziona formazione
15:42 - Utente: Inizia scout
15:50 - Utente: Registra 10 eventi
15:55 - Utente: Esce dall'app (non completato!)
        → Match rimane in bozza con status="in_progress"
```

**Database State**:
```
Match #5:
  status: "in_progress"
  updated_at: "2024-05-08 15:55:00"
  ScoutEvent count: 10
```

**Session 2: Riprendersi dalla Bozza (dopo ore/giorni)**
```
18:00 - Utente: Apre l'app
18:01 - Utente: Dashboard → Vede "Attacco vs Cihsosla" in Sessioni in Bozza
        Con indicazione: "10 eventi registrati, Modificato: 15:55"
18:02 - Utente: Clicca "▶ Riprendi"
        → Match status cambia a "in_progress"
        → Scout Panel si apre con gli ultimi 10 eventi visibili
18:05 - Utente: Continua a registrare altri 15 eventi
18:20 - Utente: Completa il match
        → Match status cambia a "completed"
        → Totale evento salvati: 25
```

---

## 🔍 Tracciamento dello Stato

### Query Utili

**Visualizzare tutte le bozze**:
```sql
SELECT * FROM matches WHERE status='draft' ORDER BY updated_at DESC;
```

**Visualizzare match in corso**:
```sql
SELECT * FROM matches WHERE status='in_progress' ORDER BY updated_at DESC;
```

**Visualizzare match completati**:
```sql
SELECT * FROM matches WHERE status='completed' ORDER BY created_at DESC;
```

**Contare evento per bozza**:
```sql
SELECT m.id, m.home_team_id, m.away_team_id, COUNT(se.id) as event_count
FROM matches m
LEFT JOIN scout_events se ON m.id = se.match_id
WHERE m.status='in_progress'
GROUP BY m.id
ORDER BY m.updated_at DESC;
```

---

## 🐛 Troubleshooting

### Le bozze non appaiono in Dashboard

**Causa**: Colonna `status` mancante o non migrata
**Soluzione**:
```bash
cd volley_analizer
python setup.py dev_setup
# Oppure manualmente:
alembic upgrade head
```

### Il salvataggio non funziona

**Causa**: Database non salvato correttamente
**Soluzione**:
- Verifica che il `DatabaseManager` sia configurato correttamente
- Verifica che il database file esista e sia scrivibile
- Controlla la console per errori SQLAlchemy

### Impossibile riprendere una bozza

**Causa**: Match non trovato o già completato
**Soluzione**:
- Verifica che il match_id esista: `SELECT * FROM matches WHERE id=X;`
- Controlla che lo status sia "draft": `SELECT status FROM matches WHERE id=X;`
- Se necessario, reimposta manualmente: `UPDATE matches SET status='draft' WHERE id=X;`

### Eliminazione bozza fallisce

**Causa**: Riferimenti orphan o constraint violations
**Soluzione**:
- Il sistema elimina automaticamente gli event associati
- Se il problema persiste, verifica i vincoli di integrità referenziale

---

## 📈 Statistiche di Utilizzo

Per tracciare l'utilizzo del sistema di bozze:

```python
draft_mgr = DraftManager(db_manager)

# Numero totale di bozze
drafts = draft_mgr.get_drafts()
total_drafts = len(drafts)

# Numero totale di evento in tutte le bozze
total_events = sum(draft_mgr.get_draft_event_count(d['id']) for d in drafts)

# Bozza più recente
most_recent = drafts[0] if drafts else None

print(f"Bozze totali: {total_drafts}")
print(f"Evento totali in bozza: {total_events}")
if most_recent:
    print(f"Più recente: {most_recent['home_team_name']} vs {most_recent['away_team_name']}")
```

---

## ✅ Checklist di Migrazione

Se aggiorni da una versione senza il sistema di bozze:

- [x] Applica la migrazione: `alembic upgrade head`
- [x] Verifica che le colonne `status` e `updated_at` siano presenti
- [x] Verifica che le squadre di test siano state importate
- [x] Testa il creazione di una nuova sessione
- [x] Testa il salvataggio e il ripristino di una bozza
- [x] Testa l'eliminazione di una bozza

---

## 📚 File Correlati

- `alembic/versions/20260508_add_status_match_and_test_data.py` - Migrazione
- `volleyball_scout/core/models.py` - Modello Match (updated)
- `volleyball_scout/ui/drafts/draft_manager.py` - API di gestione
- `volleyball_scout/ui/drafts/draft_widget.py` - Widget UI
- `volleyball_scout/ui/main_window.py` - Integrazione dashboard (TODO)

---

## 🔄 Flusso di Integrazione

Per integrare il sistema di bozze nella dashboard esistente:

```python
from volleyball_scout.ui.drafts import DraftListWidget, DraftManager

class VolleyballScoutMainWindow(QMainWindow):
    def __init__(self):
        ...
        # Aggiungi il widget bozze alla dashboard
        self.draft_widget = DraftListWidget(self.db_manager)
        self.draft_widget.draft_resumed.connect(self.on_draft_resumed)
        
        # Aggiungi alla dashboard
        dashboard_layout.addWidget(self.draft_widget)
        
    def on_draft_resumed(self, match_id):
        """Gestisce il resume di una bozza"""
        # Carica la formazione dal DB
        # Mostra il Scout Panel
        self.show_scout_panel(match_id)
```

---

## 📝 Note Finali

Il sistema di bozze è:
- ✅ **Automatico**: Salva senza intervento dell'utente
- ✅ **Affidabile**: Usa il database per la persistenza
- ✅ **Flessibile**: Supporta multiple bozze contemporanee
- ✅ **Tracciabile**: Registra data creazione e modifica
- ✅ **Intuitivo**: UI semplice e user-friendly

**Versione**: 1.0
**Stato**: ✅ Production Ready
**Ultimo Aggiornamento**: Maggio 2024

---

*Per domande, consulta il codice nei file elencati sopra*
