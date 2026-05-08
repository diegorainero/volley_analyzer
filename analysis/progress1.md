
---

# SUMMARY TECNICO (per modelli AI o onboarding)

```/dev/null/PROJECT_SUMMARY.md#L1-40
## Stato e processi implementati

- **Database**: SQLite, gestito con SQLAlchemy e Alembic. Tutte le tabelle sono create tramite migrazione autogenerata.
- **Migrazioni**: Se si cambia il modello, si genera una nuova migrazione con `alembic revision --autogenerate -m "msg"`, poi si applica con `alembic upgrade head`.
- **Reset sviluppo**: Per evitare errori di schema, si elimina il file `.db` e si rilanciano tutte le migrazioni.
- **Modello MatchPlayer**: ora ha i campi `is_starter` (Boolean) e `is_libero` (Boolean) per tracciare titolari e libero della formazione.
- **Flusso UI**:
  1. Dashboard
  2. Gestione Match
  3. Roster Setup (scelta giocatori)
  4. Formation Panel (scelta titolari/libero, salvataggio su DB)
  5. Scout Panel (inserimento eventi)

---

**Questo summary può essere usato per istruire un modello AI o un nuovo sviluppatore sullo stato attuale del progetto e sulle best practice adottate.**
