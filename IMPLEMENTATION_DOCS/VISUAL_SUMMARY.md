# Visual Summary - Roster Setup Flow

## 🎬 Scenario Principale: Crea Partita → Setup Roster

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Formation Setup Widget                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🏐 Selezione Partita per Formazione                               │
│                                                                     │
│  [➕ Nuova Partita]  [🔄 Aggiorna]                                │
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐       │
│  │ Home    │ Away    │ Data         │ Status      │       │       │
│  ├────────────────────────────────────────────────────────┤       │
│  │ Team A  │ Team B  │ 2024-01-15   │ in_progress │       │       │
│  │         │         │              │             │       │       │
│  └────────────────────────────────────────────────────────┘       │
│                                                                     │
│  [Clicca "Nuova Partita"]                                          │
│         ↓                                                           │
│         │                                                           │
└─────────│───────────────────────────────────────────────────────────┘
          │
          ↓
┌──────────────────────────────────────────┐
│   NewMatchDialog apre                   │
├──────────────────────────────────────────┤
│                                          │
│  Squadra A (Home):  [Team A ▼]          │
│  Squadra B (Away):  [Team B ▼]          │
│  Data e Ora:        [2024-01-15 14:30]  │
│  Luogo:             [Palasport di...]   │
│  Note:              [Optional...]       │
│                                          │
│  [✅ Salva]  [❌ Annulla]               │
│                                          │
│  [Clicca "Salva"]                       │
│         ↓                                 │
└──────────────────────────────────────────┘
          │
          ├─→ Salva Match nel DB
          │   INSERT INTO matches ...
          │   FLUSH per ottenere ID
          │
          ├─→ Emetti Signal: match_created(123)
          │
          ├─→ FormationSetupMatches._on_new_match_created(123)
          │
          ├─→ FormationSetupComplete._open_roster_setup(123)
          │
          ↓
┌────────────────────────────────────────────────────────────────┐
│              RosterSetupWidget - QDialog                       │
├────────────────────────────────────────────────────────────────┤
│                   🏐 Setup Roster Partita                      │
│                                                                │
│  Team A vs Team B (2024-01-15 14:30)                          │
│                                                                │
│ ┌──────────────────────┐ │ ┌──────────────────────────────┐  │
│ │ Selezione Giocatori  │ │ │    Roster Partita            │  │
│ ├──────────────────────┤ │ ├──────────────────────────────┤  │
│ │ Squadra: [Team A ▼]  │ │ │ Nome     │Mag│Ruolo│Mod│Rim  │  │
│ │                      │ │ ├──────────────────────────────┤  │
│ │ Giocatori Disp:      │ │ │ Mario    │ 3 │ C   │ ▼ │ ✕  │  │
│ │ ☑ #3 - Mario Rossi  │ │ │ Giovanni │12 │ PL  │ ▼ │ ✕  │  │
│ │ ☐ #5 - Luigi Bianch│ │ │ Francesco│ 8 │ O   │ ▼ │ ✕  │  │
│ │ ☑ #12 - Francesco V│ │ │          │   │     │   │    │  │
│ │ ☐ #7 - Giorgio Neri│ │ └──────────────────────────────┘  │
│ │                      │ │                                    │
│ └──────────────────────┘ │   [✅ Salva Roster]              │
│                          │                                    │
└──────────────────────────────────────────────────────────────┘
          │
          ├─→ [Spunta checkbox "Mario"]
          │   ↓
          ├─→ [Clicca "Modifica" su Mario]
          │   ↓
          │
┌──────────────────────────────────────────┐
│   Dialog Modifica - Mario Rossi         │
├──────────────────────────────────────────┤
│                                          │
│  Numero Maglia:  [3]  (SpinBox 0-99)    │
│  Ruolo:          [Palleggiatore ▼]      │
│                 (Centrale, Opposto...)  │
│                                          │
│  [OK]  [Annulla]                        │
│                                          │
│  [Clicca "OK"]                          │
│         ↓                                 │
└──────────────────────────────────────────┘
          │
          ├─→ selected_players[mario_id] = {
          │     number: 13,
          │     role: "Centrale"
          │   }
          │
          ├─→ _update_roster_table()
          │   ↓
          │   Tabella aggiornata
          │
          ├─→ [Spunta altri checkbox]
          │
          ├─→ [Clicca "✅ Salva Roster"]
          │
          ↓
┌──────────────────────────────────────────┐
│   DB Operations                         │
├──────────────────────────────────────────┤
│                                          │
│  DELETE FROM match_players              │
│  WHERE match_id = 123                   │
│                                          │
│  INSERT INTO match_players VALUES      │
│  (match_id=123, player_id=1, ...)      │
│  (match_id=123, player_id=2, ...)      │
│  (match_id=123, player_id=3, ...)      │
│                                          │
│  COMMIT                                 │
│                                          │
│  ✅ Roster salvato con successo!       │
│         ↓                                 │
└──────────────────────────────────────────┘
          │
          ├─→ roster_completed.emit()
          │
          ├─→ Dialog chiude
          │
          ├─→ matches_widget._load_matches()
          │
          ├─→ match_selected.emit(match_dict)
          │
          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    FormationPanel Apre                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                     🏐 Campo Volley                               │
│                                                                     │
│              [Mario #13]  [Giovanni #12]                         │
│                                                                   │
│                    [Francesco #8]                                │
│                                                                   │
│                 [Libero Backup]  [Riserva]                       │
│                                                                   │
│  ✅ FORMAZIONE COMPLETATA!                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

[FINE FLUSSO]
```

---

## 🔀 Architettura QStackedWidget

```
┌─────────────────────────────────┐
│    RosterSetupWidget            │
│  (Parent Container)             │
├─────────────────────────────────┤
│                                 │
│  ┌──────────────────────────┐   │
│  │ QStackedWidget Index: 0  │   │
│  ├──────────────────────────┤   │
│  │                          │   │
│  │ Selezione Partita Page  │   │ ← Visibile se match_id è None
│  │                          │   │
│  │ Matches List + Select    │   │
│  │                          │   │
│  └──────────────────────────┘   │
│                                 │
│  ┌──────────────────────────┐   │
│  │ QStackedWidget Index: 1  │   │
│  ├──────────────────────────┤   │
│  │                          │   │
│  │ Setup Roster Page        │   │ ← Visibile se match_id è fornito
│  │                          │   │
│  │ Team Selection + Roster  │   │
│  │                          │   │
│  └──────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

---

## 📊 Signal Flow Diagram

```
                    ┌──────────────────────┐
                    │  NewMatchDialog      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ match_created(int)   │ ← Signal
                    └──────────┬───────────┘
                               │
                    ┌──────────▼─────────────────────────┐
                    │ FormationSetupMatches              │
                    │ ._on_new_match_created(match_id)   │
                    └──────────┬─────────────────────────┘
                               │
                    ┌──────────▼─────────────────────────┐
                    │ FormationSetupComplete              │
                    │ ._open_roster_setup(match_id)       │
                    └──────────┬─────────────────────────┘
                               │
                    ┌──────────▼─────────────────────────┐
                    │ RosterSetupWidget (Dialog)          │
                    │ - Load match                        │
                    │ - Load players                      │
                    │ - Select/Modify roster             │
                    └──────────┬─────────────────────────┘
                               │
                    ┌──────────▼─────────────────────────┐
                    │ roster_completed()                  │ ← Signal
                    │ (al click "Salva Roster")           │
                    └──────────┬─────────────────────────┘
                               │
                    ┌──────────▼─────────────────────────┐
                    │ FormationSetupComplete              │
                    │ .on_roster_completed()              │
                    │ - Load matches                      │
                    │ - Emit match_selected               │
                    └──────────┬─────────────────────────┘
                               │
                    ┌──────────▼─────────────────────────┐
                    │ FormationPanel                      │
                    │ (Mostra il court con i giocatori)  │
                    └─────────────────────────────────────┘
```

---

## 🗂️ Data Structure: selected_players

```python
self.selected_players = {
    player_id_1: {
        "number": 3,           # Numero maglia per questo match
        "role": "Centrale",    # Ruolo nel match
        "team_id": 1          # Per sapere a quale squadra appartiene
    },
    player_id_2: {
        "number": 12,
        "role": "Palleggiatore",
        "team_id": 1
    },
    player_id_3: {
        "number": 8,
        "role": "Opposto",
        "team_id": 2           # Può essere da squadra diversa
    }
}

# Esempio JSON da salvare nel DB:
# INSERT INTO match_players
# (match_id, player_id, team_id, number, role, is_libero, is_starter)
# VALUES
# (123, 1, 1, 3, 'Centrale', False, False),
# (123, 2, 1, 12, 'Palleggiatore', False, False),
# (123, 3, 2, 8, 'Opposto', False, False)
```

---

## 🔄 Sincronizzazione Checkbox ↔ Dict

```
AZIONE UTENTE                    STATO INTERNO
──────────────────────────────────────────────────

[☑ Spunta Mario]                selected_players[1] = {default}
    ↓
_sync_roster_with_checkboxes()
    ↓
_update_roster_table()           Tabella mostra Mario
    ↓
_update_roster_table() ricrea la tabella con i dati attuali
    

[Clicca "Modifica" su Mario]     Dialog apre
    ↓
[Cambia numero 3→13, ruolo]      Dialog attende OK
    ↓
[Clicca OK]                      selected_players[1]["number"] = 13
    ↓
_update_roster_table()           Tabella aggiornata con 13
    

[☐ Uncheck Mario]                Mario rimosso dalla selected_players
    ↓
_sync_roster_with_checkboxes()
    ↓
_update_roster_table()           Tabella rimuove Mario
    

[Clicca "Rimuovi" su Mario]      selected_players.delete(1)
    ↓
_update_roster_table()           Tabella rimuove Mario
    ↓
Checkbox a sinistra unchecked    Sincronizzazione bidirezionale!
```

---

## 🎨 UI Layout Dettagliato

```
┌────────────────────────────────────────────────────────────────┐
│                   RosterSetupWidget Dialog                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌─ HEADER ─────────────────────────────────────────────────┐ │
│ │ Team A vs Team B (2024-01-15 14:30)      [← Indietro]   │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                │
│ ┌─ BODY ────────────────────────────────────────────────────┐ │
│ │                                                           │ │
│ │ ┌─ SINISTRA ─────────┐ │ ┌─ DESTRA ──────────────────┐ │ │
│ │ │ Selezione Giocatori│ │ │  Roster Partita           │ │ │
│ │ ├────────────────────┤ │ ├──────────────────────────┤ │ │
│ │ │                    │ │ │ Nome    │Mag │Ruolo     │ │ │
│ │ │ Squadra: [A ▼ B]  │ │ ├──────────────────────────┤ │ │
│ │ │                    │ │ │ Mario   │ 3  │Centrale  │ │ │
│ │ │ Giocatori:         │ │ │ Giovanni│ 12 │Palleggio │ │ │
│ │ │                    │ │ │ Francesco│ 8 │Opposto   │ │ │
│ │ │ ☑ #3 - Mario      │ │ │          │    │          │ │ │
│ │ │ ☐ #5 - Luigi      │ │ │    Azioni (Modifica/Rimuovi) │ │
│ │ │ ☑ #12 - Francesco│ │ │                          │ │ │
│ │ │ ☐ #7 - Giorgio   │ │ │                          │ │ │
│ │ │ ☐ #9 - Marco     │ │ │                          │ │ │
│ │ │                    │ │ │                          │ │ │
│ │ └────────────────────┘ │ └──────────────────────────┘ │ │
│ │                                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                                │
│ ┌─ FOOTER ─────────────────────────────────────────────────┐ │
│ │                              [✅ Salva]  [❌ Annulla]   │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘

SIZE: 1000x600 pixels (minimo)
MODE: Modal dialog (blocca la finestra principale)
```

---

## 📈 State Machine

```
START
  │
  ├─→ match_id è None?
  │   │
  │   ├─ YES → Pagina 0: Match Selection
  │   │        ↓
  │   │        [Seleziona match da lista]
  │   │        ↓
  │   │        _load_match(id)
  │   │
  │   └─ NO  → Pagina 1: Roster Setup (diretto!)
  │
  ├─→ Load match data
  │   ├─ Match info
  │   ├─ Teams (home + away)
  │   └─ Existing roster (se presente)
  │
  ├─→ Mostra pagina Roster Setup
  │   │
  │   ├─→ Load team players
  │   │   ├─ Popola lista checkbox
  │   │   └─ Pre-seleziona giocatori di roster esistente
  │   │
  │   ├─→ Attendi azione utente
  │   │   ├─ Spunta checkbox → Aggiungi a selected_players
  │   │   ├─ Clicca "Modifica" → Dialog numero/ruolo
  │   │   ├─ Clicca "Rimuovi" → Elimina da selected_players
  │   │   └─ Clicca "Salva" → Procedi a save
  │   │
  │   └─→ _save_roster()
  │       ├─ Sincronizza checkbox ↔ dict
  │       ├─ Valida: min 1 giocatore
  │       ├─ DELETE vecchio roster
  │       ├─ INSERT nuovi MatchPlayer
  │       ├─ COMMIT
  │       ├─ Mostra messaggio successo
  │       ├─ Emetti roster_completed()
  │       └─ Dialog chiude
  │
  └─→ END (torna a FormationSetupComplete)
```

---

## 🧪 Test Coverage Matrix

```
┌──────────────────────┬──────────────────────┬──────────────────┐
│ Feature              │ Unit Test            │ Integration Test │
├──────────────────────┼──────────────────────┼──────────────────┤
│ Load Match           │ ⏳ TODO              │ ⏳ TODO          │
│ Load Players         │ ⏳ TODO              │ ⏳ TODO          │
│ Checkbox Sync        │ ⏳ TODO              │ ⏳ TODO          │
│ Modify Player        │ ⏳ TODO              │ ⏳ TODO          │
│ Save Roster          │ ⏳ TODO              │ ⏳ TODO          │
│ Validate Min/Max     │ ⏳ TODO              │ ⏳ TODO          │
│ Full Flow            │ N/A                  │ ⏳ TODO          │
│ Error Handling       │ ⏳ TODO              │ ⏳ TODO          │
│ Signal Emission      │ ⏳ TODO              │ ⏳ TODO          │
└──────────────────────┴──────────────────────┴──────────────────┘

Manual Tests:
✅ Scenario 1: Create Match → Setup Roster (da eseguire)
✅ Scenario 2: Modify Existing Roster (future)
✅ Scenario 3: Reload Match with Roster (da eseguire)
✅ Scenario 4: Checkbox Sync (da eseguire)
✅ Scenario 5: Error Handling (da eseguire)
```

---

## 🎯 Implementation Checklist

```
CODE CHANGES:
✅ new_match_dialog.py - Signal type change
✅ roster_setup.py - Complete rewrite
✅ formation_setup_complete.py - Integration
✅ No database schema changes needed (MatchPlayer already exists)

DOCUMENTATION:
✅ ROSTER_SETUP_FLOW.md - Main documentation
✅ CHANGES_SUMMARY.md - Detailed changelog
✅ TESTING_GUIDE.md - Testing scenarios
✅ README.md - Overview and quick start
✅ VISUAL_SUMMARY.md - This file

TESTING:
⏳ Manual testing (see TESTING_GUIDE.md)
⏳ Unit tests
⏳ Integration tests
⏳ Edge cases

DEPLOYMENT:
⏳ Code review
⏳ QA approval
⏳ Production deployment
```

---

**This visual guide should help you understand the entire flow at a glance!**
