# Formation Panel - Architecture & Data Flow Diagram

## 🏗️ Architettura Componenti

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN WINDOW (main_window.py)                 │
│                                                                      │
│  show_formation_panel()                                              │
│       ↓                                                              │
│  Recupera teams e players dal DB                                    │
│       ↓                                                              │
│  Crea FormationPanel                                                │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ .formation_confirmed.connect()
                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│             FORMATION PANEL (formation_panel.py)                    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ FormationPanel                                                 │ │
│  │  - teams: List[Team]                                          │ │
│  │  - players_by_team: Dict[team_id, List[Player]]              │ │
│  │  - game_method: str (P-S-C | P-C-S)                         │ │
│  │  - radio_psc: QRadioButton                                   │ │
│  │  - radio_pcs: QRadioButton                                   │ │
│  │                                                                │ │
│  │  Methods:                                                      │ │
│  │  - confirm_formation() → validates & emits signal            │ │
│  │  - reset_all()                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│       │                                                              │
│       └── Per ogni team: crea TeamFormationWidget                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ TeamFormationWidget                                            │ │
│  │  - team: Team                                                  │ │
│  │  - players: List[Player]                                      │ │
│  │  - player_buttons: Dict[player_id, PlayerButton]             │ │
│  │  - formation_slots: Dict[idx, FormationSlot]                 │ │
│  │  - libero_slots: Dict[idx, LiberoSlot]                       │ │
│  │  - used_players: Set[player_id]  ← NUOVO                     │ │
│  │                                                                │ │
│  │  Methods:                                                      │ │
│  │  - register_player(player_id)  ← NUOVO                       │ │
│  │  - unregister_player(player_id)  ← NUOVO                     │ │
│  │  - get_formation() → {titolari, liberi}                      │ │
│  │  - reset_formation()                                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│       │                                                              │
│       ├── Contiene N PlayerButtons (6x2 griglia)                    │
│       │                                                              │
│       ├── Contiene FormationSlots (3x2 griglia)                     │
│       │                                                              │
│       └── Contiene LiberoSlots (2 slot laterali)                    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ PlayerButton                        ← MODIFICATO               │ │
│  │  - number: int                                                 │ │
│  │  - player_id: int                                              │ │
│  │  - role: str  ← NUOVO                                          │ │
│  │  - is_selected: bool                                           │ │
│  │                                                                │ │
│  │  _update_style(): Se "palleggiatore" in role.lower()         │ │
│  │    → button text = "10P" (aggiunge "P")                       │ │
│  │                                                                │ │
│  │  mousePressEvent(): Avvia drag                                │ │
│  │    → mime_data = "player_id|number"                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ FormationSlot                      ← MODIFICATO               │ │
│  │  - position_name: str                                          │ │
│  │  - player_id: int | None                                       │ │
│  │  - formation_widget: TeamFormationWidget  ← NUOVO             │ │
│  │                                                                │ │
│  │  dropEvent():                                                  │ │
│  │    1. Estrae player_id dal mime_data                          │ │
│  │    2. NUOVO: Valida se già in used_players                   │ │
│  │       → Se sì e diverso da self: QMessageBox.warning()      │ │
│  │       → Ritorna (drop rifiutato)                              │ │
│  │    3. Chiama set_player(player_id)                            │ │
│  │                                                                │ │
│  │  set_player():                                                │ │
│  │    1. Se player_id precedente: unregister                    │ │
│  │    2. Assegna player_id e numero                              │ │
│  │    3. NUOVO: Registra in used_players                        │ │
│  │                                                                │ │
│  │  clear():                                                      │ │
│  │    1. NUOVO: Deregistra da used_players                      │ │
│  │    2. Svuota slot                                             │ │
│  │                                                                │ │
│  │  mousePressEvent():                                           │ │
│  │    Se contiene giocatore → clear()                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ LiberoSlot                         ← MODIFICATO               │ │
│  │  (Same as FormationSlot, but smaller)                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Signal emitted:                                                     │
│  formation_confirmed({                                              │
│    "titolari": {team_id: [player_ids]},                           │
│    "libero": {team_id: player_id},                                │
│    "game_method": "P-S-C"  ← NUOVO                               │
│  })                                                                  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ on_formation_confirmed()
                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  MAIN WINDOW: on_formation_confirmed()              │
│                                                                      │
│  1. Estrae game_method = formation_data.get("game_method")         │
│  2. Carica match dal DB                                             │
│  3. Imposta match.game_method = game_method  ← NUOVO              │
│  4. Salva titolari e liberi                                         │
│  5. session.commit()  ← Persiste al DB                             │
│  6. Mostra ScoutPanel                                               │
└──────────────────────────────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite / PostgreSQL)                   │
│                                                                      │
│  matches table:                                                      │
│  ├─ id                                                               │
│  ├─ home_team_id                                                     │
│  ├─ away_team_id                                                     │
│  ├─ status                                                           │
│  ├─ updated_at                                                       │
│  └─ game_method = "P-S-C"  ← NUOVO CAMPO                           │
│                                                                      │
│  match_players table:                                                │
│  ├─ match_id                                                         │
│  ├─ player_id                                                        │
│  ├─ team_id                                                          │
│  ├─ is_starter (Boolean)                                            │
│  └─ is_libero (Boolean)                                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Completo

### Scenario: Utente completa una formazione

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INIZIO: FormationPanel aperto                                │
│    - UI mostra: Player buttons + Formation slots                │
│    - Radio buttons per metodo di gioco (nessuno selezionato)   │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. UTENTE: Seleziona metodo di gioco                            │
│    - Clicca radio button "P-S-C"                               │
│    - FormationPanel.game_method = "P-S-C"                      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. UTENTE: Trascina giocatore #1 (Palleggiatore) in P1          │
│                                                                  │
│    a) PlayerButton.__init__(1, player_id, role="Palleggiatore")│
│       → button text = "1P" (indicatore P visibile)             │
│                                                                  │
│    b) Utente clicca e trascina #1                              │
│       → QDrag invia mime_data = "player_id|1"                 │
│                                                                  │
│    c) FormationSlot P1.dragEnterEvent()                        │
│       → Accetta (hasText() = true)                             │
│                                                                  │
│    d) FormationSlot P1.dropEvent()                             │
│       → data = "123|1" (player_id=123, number=1)              │
│       → Controlla: used_players.contains(123)? → No           │
│       → Chiama set_player(1, 123)                             │
│       → registration_widget.register_player(123)              │
│       → used_players = {123}                                   │
│       → P1.label = "1"                                         │
│       → Accept drop                                             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. UTENTE: Tenta di trascinare #1 in P2 (ERRORE)               │
│                                                                  │
│    a) FormationSlot P2.dropEvent()                             │
│       → data = "123|1"                                          │
│       → Controlla: used_players.contains(123)? → YES!         │
│       → if self.player_id (P2) != 123 (drag)? → True         │
│       → QMessageBox.warning("Il giocatore #1 è già...")       │
│       → event.ignore()  (drop rifiutato)                       │
│       → P2 rimane vuoto                                        │
│       → used_players rimane = {123}                            │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. UTENTE: Continua con altri giocatori                         │
│    - Trascina #2 (Schiacciatore) in P2 → OK                    │
│    - Trascina #3 (Centrale) in P3 → OK                         │
│    - Trascina #4, #5, #6 → OK                                  │
│    - Trascina libero #7 in LiberoSlot → OK                     │
│                                                                  │
│    Risultato: used_players = {123, 124, 125, 126, 127, 128, 129}│
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. UTENTE: Clicca "Conferma Formazione"                         │
│                                                                  │
│    FormationPanel.confirm_formation():                          │
│                                                                  │
│    A) Valida metodo di gioco:                                  │
│       - radio_psc.isChecked()? → True                         │
│       - game_method = "P-S-C"                                  │
│                                                                  │
│    B) Per ogni team:                                            │
│       - Valida 6 titolari → ✓                                  │
│       - Valida >= 1 libero → ✓                                 │
│       - Valida >= 1 palleggiatore:                             │
│         * has_setter_available = any(p["role"] == "Palleggiatore")  
│         * YES → Controlla in titolari                          │
│         * has_setter_in_field = True  (player #1 è setter)    │
│         * ✓ PASSED                                             │
│                                                                  │
│    C) Emetti signal:                                            │
│       formation_confirmed.emit({                                │
│         "titolari": {team_id: [123, 124, 125, 126, 127, 128]}, │
│         "libero": {team_id: 129},                              │
│         "game_method": "P-S-C"  ← NUOVO                        │
│       })                                                         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. MAIN WINDOW: on_formation_confirmed(formation_data)          │
│                                                                  │
│    - Estrae: game_method = "P-S-C"                             │
│    - Carica match dal DB                                        │
│    - Itera per ogni team_id in formation_data["titolari"]:    │
│      * Per ogni player_id:                                     │
│        - MatchPlayer.is_starter = True                        │
│      * Per libero:                                             │
│        - MatchPlayer.is_libero = True                         │
│    - Imposta match.game_method = "P-S-C"  ← NUOVO            │
│    - session.commit()  ← Salva al DB                           │
│    - Mostra ScoutPanel                                         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. DATABASE: Inserimento/Aggiornamento                          │
│                                                                  │
│    UPDATE matches SET game_method = "P-S-C" WHERE id = ?       │
│    UPDATE match_players SET is_starter = 1 WHERE ...           │
│    UPDATE match_players SET is_libero = 1 WHERE ...            │
│                                                                  │
│    Risultato DB:                                                │
│    matches:                                                      │
│    ├─ id: 1                                                     │
│    ├─ game_method: "P-S-C"  ← NUOVO                           │
│    └─ ...                                                       │
│                                                                  │
│    match_players:                                               │
│    ├─ player_id 123: is_starter=1, is_libero=0               │
│    ├─ player_id 124: is_starter=1, is_libero=0               │
│    ├─ ...                                                       │
│    └─ player_id 129: is_starter=0, is_libero=1               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. FINE: Scout Panel avviato                                    │
│    - Dati di formazione disponibili per scouting               │
│    - Metodo di gioco persistente                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Diagramma UML - Classi Coinvolte

```
┌──────────────────────┐
│   FormationPanel     │
├──────────────────────┤
│ - teams: List        │
│ - game_method: str   │ ← NUOVO
│ - radio_psc          │ ← NUOVO
│ - radio_pcs          │ ← NUOVO
├──────────────────────┤
│ + confirm_formation()│
│ + reset_all()        │
│ + formation_confirmed│ (signal)
└──────────┬───────────┘
           │ 1..N
           │ has
           ↓
┌──────────────────────────────┐
│  TeamFormationWidget         │
├──────────────────────────────┤
│ - team: Team                 │
│ - players: List              │
│ - used_players: Set          │ ← NUOVO
│ - player_buttons: Dict       │
│ - formation_slots: Dict      │
│ - libero_slots: Dict         │
├──────────────────────────────┤
│ + register_player()          │ ← NUOVO
│ + unregister_player()        │ ← NUOVO
│ + get_formation()            │
│ + reset_formation()          │
└──────────┬───────────────────┘
           │
    ┌──────┼──────┐
    │      │      │
    ↓      ↓      ↓
 ┌──────┐ ┌──────────┐ ┌──────────┐
 │Player│ │Formation │ │Libero    │
 │Button│ │Slot      │ │Slot      │
 └──────┘ └──────────┘ └──────────┘
    ↑          ↑          ↑
    │          │          │
    └──────────┼──────────┘
               │
    MODIFICATE: role param, validation

┌──────────────────────┐
│      Match           │ (models.py)
├──────────────────────┤
│ - id                 │
│ - game_method: str   │ ← NUOVO (default: "P-S-C")
│ - roster: [MP]       │
├──────────────────────┤
│ + save()             │
│ + query()            │
└──────────────────────┘
```

---

## ⚙️ Sequence Diagram - Happy Path

```
Utente        FormationPanel      TeamFW        Slot          DB
  │                │                │            │             │
  │─Seleziona P-S-C─→│                │            │             │
  │                │ (game_method="P-S-C")        │             │
  │                │                │            │             │
  │─Trascina #1───→│                │            │             │
  │                │──Crea drop─────→│            │             │
  │                │                │────check used_players    │
  │                │                │            │             │
  │                │                │←──free─────│             │
  │                │                │────set_player──→        │
  │                │                │<──register─┤             │
  │                │                │            │             │
  │─Tenta #1 in P2→│                │            │             │
  │                │                │────check used_players    │
  │                │                │←──IN_USE──┤             │
  │                │            QMessageBox       │             │
  │                │────ERROR────→  │            │             │
  │                │                │            │             │
  │─Continua...    │                │            │             │
  │                │   (insert 5,6,7)           │             │
  │                │                │            │             │
  │─Conferma───────→confirm_formation()         │             │
  │                │ validate game_method        │             │
  │                │ validate titolari           │             │
  │                │ validate setter in field    │             │
  │                │                             │             │
  │                │─emit formation_confirmed─→ MainWindow     │
  │                │                             │─DB UPDATE──→ DB
  │                │                             │ + game_method
  │                │                             │             │
```

---

## 💾 Stato Finale nel Database

```sql
-- Dopo completamento della formazione

SELECT 
    m.id,
    m.home_team_id,
    m.away_team_id,
    m.game_method  -- NUOVO: "P-S-C" o "P-C-S"
FROM matches m;

--
-- Result:
-- id | home_team_id | away_team_id | game_method
-- 1  | 1            | 2            | P-S-C       ← NUOVO VALORE

SELECT 
    mp.player_id,
    mp.number,
    mp.is_starter,
    mp.is_libero,
    p.role
FROM match_players mp
JOIN players p ON mp.player_id = p.id
WHERE mp.match_id = 1
ORDER BY mp.team_id, mp.is_starter DESC;

--
-- Result:
-- player_id | number | is_starter | is_libero | role
-- 123       | 1      | 1          | 0         | Palleggiatore  ← SETTER IN CAMPO
-- 124       | 2      | 1          | 0         | Schiacciatore
-- 125       | 3      | 1          | 0         | Centrale
-- ...
-- 129       | 7      | 0          | 1         | Libero         ← LIBERO
```

---

**Documento creato**: 2024-05-09  
**Versione**: 1.0
