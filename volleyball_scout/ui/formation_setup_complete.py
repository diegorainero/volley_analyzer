"""
Formation Setup Complete - Widget con Match Selector integrato
Gestisce la navigazione tra lista di partite e dettagli della formazione
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .formation_panel import FormationPanel
from .new_match_dialog import NewMatchDialog
from .roster_setup import RosterSetupWidget


class FormationSetupMatches(QWidget):
    """
    Widget per la selezione delle partite da elaborare.
    Emette un signal quando l'utente seleziona una partita.
    """

    # Signal emesso quando viene selezionato un match per la formazione
    match_selected = pyqtSignal(dict)  # Emette il match dict

    def __init__(self, db_manager, parent=None):
        """Inizializza widget selezione partite."""
        super().__init__(parent)
        self.db = db_manager
        self.matches = []
        self.parent_formation = parent  # Riferimento al FormationSetupComplete

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Titolo
        title = QLabel("Selezione Partita per Formazione")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Sottotitolo
        subtitle = QLabel("Clicca su una partita per inserire la formazione")
        subtitle.setStyleSheet("color: #D8C8D5; font-size: 12px;")
        layout.addWidget(subtitle)

        # Pulsante "Nuova Partita"
        btn_new_match = QPushButton("Nuova Partita")
        btn_new_match.setMaximumWidth(170)
        btn_new_match.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        btn_new_match.clicked.connect(self._on_new_match_clicked)
        layout.addWidget(btn_new_match)

        # Tabella match
        self.matches_table = QTableWidget()
        self.matches_table.setColumnCount(4)
        self.matches_table.setHorizontalHeaderLabels(["Home", "Away", "Data", "Status"])
        self.matches_table.setColumnWidth(0, 200)
        self.matches_table.setColumnWidth(1, 200)
        self.matches_table.setColumnWidth(2, 150)
        self.matches_table.setColumnWidth(3, 150)

        # Double-click per aprire formazione
        self.matches_table.itemDoubleClicked.connect(self._on_match_double_clicked)

        layout.addWidget(self.matches_table, 1)

        # Bottone refresh
        btn_refresh = QPushButton("Aggiorna")
        btn_refresh.setMaximumWidth(170)
        btn_refresh.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        btn_refresh.clicked.connect(self._load_matches)
        layout.addWidget(btn_refresh)

        self.setLayout(layout)

        # Carica i match
        self._load_matches()

    def _load_matches(self):
        """Carica i match incompleti dal database"""
        try:
            self.matches = []
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Match

                matches_data = (
                    session.query(Match)
                    .filter(Match.status.in_(["draft", "in_progress"]))
                    .order_by(Match.date.desc())
                    .all()
                )

                for match in matches_data:
                    home_name = match.home_team.name if match.home_team else "TBD"
                    away_name = match.away_team.name if match.away_team else "TBD"
                    self.matches.append(
                        {
                            "id": match.id,
                            "home_team": home_name,
                            "away_team": away_name,
                            "date": match.date,
                            "status": match.status,
                            "home_team_id": match.home_team_id,
                            "away_team_id": match.away_team_id,
                        }
                    )

            # Popola la tabella
            self.matches_table.setRowCount(len(self.matches))
            for idx, match in enumerate(self.matches):
                home_item = QTableWidgetItem(match["home_team"])
                away_item = QTableWidgetItem(match["away_team"])
                date_item = QTableWidgetItem(
                    match["date"].strftime("%Y-%m-%d %H:%M") if match["date"] else ""
                )
                status_item = QTableWidgetItem(match["status"])

                self.matches_table.setItem(idx, 0, home_item)
                self.matches_table.setItem(idx, 1, away_item)
                self.matches_table.setItem(idx, 2, date_item)
                self.matches_table.setItem(idx, 3, status_item)

            if len(self.matches) == 0:
                self.matches_table.setRowCount(1)
                msg_item = QTableWidgetItem(
                    "Nessuna partita da completare. Crea una nuova partita per iniziare."
                )
                self.matches_table.setItem(0, 0, msg_item)

        except Exception as e:
            print(f"⚠️ Error loading matches: {e}")
            import traceback

            traceback.print_exc()

    def _on_match_double_clicked(self, item):
        """Quando l'utente double-clicca su un match, emetti il signal"""
        current_row = self.matches_table.currentRow()
        if current_row >= 0 and current_row < len(self.matches):
            match = self.matches[current_row]
            self.match_selected.emit(match)

    def _on_new_match_clicked(self):
        """Apri il dialog per creare una nuova partita"""
        dialog = NewMatchDialog(self.db, self)
        dialog.match_created.connect(self._on_new_match_created)
        dialog.exec()

    def _on_new_match_created(self, match_id: int):
        """Quando una nuova partita è stata creata, apri il RosterSetup"""
        if self.parent_formation:
            self.parent_formation._open_roster_setup(match_id)


class FormationSetupComplete(QWidget):
    """
    Widget principale per la gestione della formazione.
    Utilizza QStackedWidget per navigare tra lista match e dettagli della formazione.

    Index 0: FormationSetupMatches (lista partite)
    Index 1: FormationPanel (dettagli formazione)
    """

    # Emesso quando la formazione è confermata e pronta per avviare lo scouting live
    scout_ready = pyqtSignal(dict)

    def __init__(self, db_manager, parent=None):
        """Inizializza widget formazione completo."""
        super().__init__(parent)
        self.db = db_manager
        self.current_match = None
        self.current_formation_panel = None
        self.target_set_number = 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QStackedWidget per navigare tra le pagine
        self.stacked_widget = QStackedWidget()

        # Index 0: Lista di match
        self.matches_widget = FormationSetupMatches(self.db, parent=self)
        self.matches_widget.match_selected.connect(self._on_match_selected)
        self.stacked_widget.addWidget(self.matches_widget)

        # Index 1: FormationPanel (sarà aggiunto dinamicamente)
        self.stacked_widget.addWidget(QWidget())  # Placeholder per ora

        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Mostra la lista di match all'inizio
        self.stacked_widget.setCurrentIndex(0)

    def _guess_next_set_number(self, match_id: int) -> int:
        """Stima il set da caricare in base allo stato corrente del match."""
        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchSet, ScoutEvent

                sets = (
                    session.query(MatchSet)
                    .filter(MatchSet.match_id == match_id)
                    .order_by(MatchSet.set_number.desc())
                    .all()
                )

                if not sets:
                    return 1

                for set_obj in sets:
                    event_count = (
                        session.query(ScoutEvent.id)
                        .filter(ScoutEvent.set_id == set_obj.id)
                        .count()
                    )
                    if event_count > 0:
                        return max(1, int(set_obj.set_number or 1))

                # Se esiste un set senza winner e ancora a 0-0, considera quello come attivo
                for set_obj in sets:
                    if (
                        set_obj.winner is None
                        and (set_obj.score_home or 0) == 0
                        and (set_obj.score_away or 0) == 0
                    ):
                        return max(1, int(set_obj.set_number or 1))

                last_set_number = int(sets[0].set_number or 1)
                return min(last_set_number + 1, 5)
        except Exception:
            return 1

    def _on_match_selected(self, match):
        """
        Quando l'utente seleziona una partita, carica la formazione e naviga
        """
        self.current_match = match
        self.target_set_number = self._guess_next_set_number(match["id"])
        self._load_and_show_formation(match)

    def _load_and_show_formation(self, match):
        """
        Carica la FormationPanel per il match selezionato e la mostra
        """
        try:
            teams = []
            players_by_team = {}

            with self.db.session_scope() as session:
                from volleyball_scout.core.models import MatchPlayer, Player, Team

                # Carica tutti i giocatori del roster match (fonte primaria)
                roster_entries = (
                    session.query(MatchPlayer)
                    .filter(MatchPlayer.match_id == match["id"])
                    .all()
                )

                roster_by_team = {}
                for entry in roster_entries:
                    team_id = entry.team_id
                    roster_by_team.setdefault(team_id, []).append(
                        {
                            "id": entry.player_id,
                            "number": entry.number,
                            "first_name": entry.player.first_name
                            if entry.player
                            else "",
                            "last_name": entry.player.last_name if entry.player else "",
                            "role": entry.role
                            or (entry.player.role if entry.player else ""),
                            "photo": entry.player.photo if entry.player else None,
                        }
                    )

                # Carica home team
                if match["home_team_id"]:
                    home_team = (
                        session.query(Team).filter_by(id=match["home_team_id"]).first()
                    )
                    if home_team:
                        teams.append({"id": home_team.id, "name": home_team.name})

                        # Usa roster match se presente, altrimenti fallback ai player della squadra
                        if (
                            home_team.id in roster_by_team
                            and roster_by_team[home_team.id]
                        ):
                            players_by_team[home_team.id] = roster_by_team[home_team.id]
                        else:
                            players = (
                                session.query(Player)
                                .filter_by(team_id=home_team.id)
                                .all()
                            )
                            players_by_team[home_team.id] = [
                                {
                                    "id": p.id,
                                    "number": p.number,
                                    "first_name": p.first_name,
                                    "last_name": p.last_name,
                                    "role": p.role,
                                    "photo": p.photo,
                                }
                                for p in players
                            ]

                # Carica away team
                if match["away_team_id"]:
                    away_team = (
                        session.query(Team).filter_by(id=match["away_team_id"]).first()
                    )
                    if away_team:
                        teams.append({"id": away_team.id, "name": away_team.name})

                        # Usa roster match se presente, altrimenti fallback ai player della squadra
                        if (
                            away_team.id in roster_by_team
                            and roster_by_team[away_team.id]
                        ):
                            players_by_team[away_team.id] = roster_by_team[away_team.id]
                        else:
                            players = (
                                session.query(Player)
                                .filter_by(team_id=away_team.id)
                                .all()
                            )
                            players_by_team[away_team.id] = [
                                {
                                    "id": p.id,
                                    "number": p.number,
                                    "first_name": p.first_name,
                                    "last_name": p.last_name,
                                    "role": p.role,
                                    "photo": p.photo,
                                }
                                for p in players
                            ]

            # Crea la FormationPanel
            if teams:
                # Rimuovi sempre il widget presente in index 1 (placeholder o vecchia formation)
                existing_widget = self.stacked_widget.widget(1)
                if existing_widget is not None:
                    self.stacked_widget.removeWidget(existing_widget)
                    existing_widget.deleteLater()

                # Crea e configura la nuova FormationPanel
                self.current_formation_panel = FormationPanel(
                    teams,
                    players_by_team,
                    matches=self.matches_widget.matches,
                )
                self.current_formation_panel.match_id = match["id"]

                # Connetti i segnali della formation panel
                self.current_formation_panel.back_requested.connect(
                    self._on_back_to_matches
                )
                self.current_formation_panel.formation_confirmed.connect(
                    self._on_formation_confirmed
                )

                # Inserisci il widget in index 1 e mostralo
                self.stacked_widget.insertWidget(1, self.current_formation_panel)
                self.stacked_widget.setCurrentWidget(self.current_formation_panel)
            else:
                print(f"⚠️ Match {match['id']} non ha squadre associate")

        except Exception as e:
            print(f"⚠️ Error loading formation: {e}")
            import traceback

            traceback.print_exc()

    def _extract_team_lineup(self, team_id: int) -> dict:
        """Estrae la formazione in campo (P1..P6 + libero) per una squadra."""
        if not self.current_formation_panel:
            return {"positions": {}, "libero": None}

        team_widget = self.current_formation_panel.team_widgets.get(team_id)
        if team_widget is None:
            return {"positions": {}, "libero": None}

        positions = {}
        for idx in range(6):
            slot = team_widget.formation_slots.get(idx)
            position_code = f"P{idx + 1}"
            positions[position_code] = slot.player_number if slot else None

        libero_number = None
        for slot in team_widget.libero_slots.values():
            if slot.player_number is not None:
                libero_number = slot.player_number
                break

        return {"positions": positions, "libero": libero_number}

    def _persist_confirmed_formation(self, formation_data: dict):
        """Persisti la formazione confermata come line-up iniziale del set target."""
        if not self.current_match:
            raise ValueError("Nessun match selezionato")

        match_id = self.current_match["id"]
        set_number = max(1, int(self.target_set_number or 1))
        titolari_by_team = formation_data.get("titolari", {})

        with self.db.session_scope() as session:
            from volleyball_scout.core.models import Match, MatchPlayer, MatchSet

            match_obj = session.query(Match).filter_by(id=match_id).first()
            if match_obj is None:
                raise ValueError(f"Match {match_id} non trovato")

            # Reset titolari sul roster del match e applica i nuovi titolari
            for team_id, starter_ids in titolari_by_team.items():
                session.query(MatchPlayer).filter_by(
                    match_id=match_id, team_id=team_id
                ).update({MatchPlayer.is_starter: False}, synchronize_session=False)

                if starter_ids:
                    session.query(MatchPlayer).filter(
                        MatchPlayer.match_id == match_id,
                        MatchPlayer.team_id == team_id,
                        MatchPlayer.player_id.in_(starter_ids),
                    ).update({MatchPlayer.is_starter: True}, synchronize_session=False)

            # Garantisce l'esistenza del set target
            target_set = (
                session.query(MatchSet)
                .filter_by(match_id=match_id, set_number=set_number)
                .first()
            )
            if target_set is None:
                target_set = MatchSet(
                    match_id=match_id,
                    set_number=set_number,
                    score_home=0,
                    score_away=0,
                )
                session.add(target_set)
            else:
                # Reset stato set quando si reimposta la formazione iniziale
                target_set.score_home = 0
                target_set.score_away = 0
                target_set.duration = None
                target_set.winner = None

            # Aggiorna stato match e metodo di gioco
            match_obj.status = "in_progress"
            match_obj.game_method = formation_data.get("game_method", "P-S-C")

    def _build_scout_payload(self, formation_data: dict) -> dict:
        """Costruisce il payload da inviare alla schermata Scouting Live."""
        if not self.current_match:
            return {}

        home_team_id = self.current_match.get("home_team_id")
        away_team_id = self.current_match.get("away_team_id")
        match_id = self.current_match.get("id")
        set_number = max(1, int(self.target_set_number or 1))
        score_home = 0
        score_away = 0
        video_offset_seconds = 0.0
        video_path = None

        def build_number_map(session, team_id: int | None) -> dict:
            """Mappa numeri maglia a ID giocatori."""
            if team_id is None or match_id is None:
                return {}

            from volleyball_scout.core.models import MatchPlayer

            mapping = {}
            rows = (
                session.query(MatchPlayer)
                .filter_by(match_id=match_id, team_id=team_id)
                .all()
            )
            for row in rows:
                if row.number is None or row.player_id is None:
                    continue
                num = str(int(row.number))
                mapping[num] = int(row.player_id)
                mapping[num.zfill(2)] = int(row.player_id)
            return mapping

        try:
            with self.db.session_scope() as session:
                from volleyball_scout.core.models import Match, MatchSet

                target_set = (
                    session.query(MatchSet)
                    .filter_by(match_id=match_id, set_number=set_number)
                    .first()
                )
                if target_set is not None:
                    score_home = int(target_set.score_home or 0)
                    score_away = int(target_set.score_away or 0)

                match_obj = session.query(Match).filter_by(id=match_id).first()
                if match_obj is not None:
                    video_offset_seconds = float(match_obj.video_offset or 0.0)
                    video_path = match_obj.video_path

                home_number_to_player_id = build_number_map(session, home_team_id)
                away_number_to_player_id = build_number_map(session, away_team_id)
        except Exception:
            score_home = 0
            score_away = 0
            video_offset_seconds = 0.0
            video_path = None
            home_number_to_player_id = {}
            away_number_to_player_id = {}

        home_lineup = self._extract_team_lineup(home_team_id) if home_team_id else {}
        away_lineup = self._extract_team_lineup(away_team_id) if away_team_id else {}

        return {
            "match_id": match_id,
            "set_number": set_number,
            "score_home": score_home,
            "score_away": score_away,
            "video_offset_seconds": video_offset_seconds,
            "video_path": video_path,
            "game_method": formation_data.get("game_method", "P-S-C"),
            "game_method_by_team": formation_data.get("game_method_by_team", {}),
            "home_team": {
                "id": home_team_id,
                "name": self.current_match.get("home_team", "Home"),
                "lineup": home_lineup.get("positions", {}),
                "libero": home_lineup.get("libero"),
                "number_to_player_id": home_number_to_player_id,
            },
            "away_team": {
                "id": away_team_id,
                "name": self.current_match.get("away_team", "Away"),
                "lineup": away_lineup.get("positions", {}),
                "libero": away_lineup.get("libero"),
                "number_to_player_id": away_number_to_player_id,
            },
            # Default: squadra di casa al servizio a inizio set
            "serving_team_id": home_team_id,
        }

    def _on_formation_confirmed(self, formation_data: dict):
        """Persisti la formazione confermata e avvia il flusso di scouting live."""
        try:
            self._persist_confirmed_formation(formation_data)
            scout_payload = self._build_scout_payload(formation_data)
            self.scout_ready.emit(scout_payload)
        except Exception as e:
            print(f"⚠️ Error confirming formation: {e}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Errore salvataggio formazione",
                f"Impossibile salvare la formazione confermata: {e}",
            )

    def _on_back_to_matches(self):
        """
        Quando l'utente clicca il pulsante "Indietro", torna alla lista di match
        """
        self.stacked_widget.setCurrentIndex(0)
        # Aggiorna la lista
        self.matches_widget._load_matches()

    def open_match_by_id(self, match_id: int, set_number: int | None = None) -> bool:
        """Apre la formation panel per un match_id specifico se disponibile."""
        self.matches_widget._load_matches()
        for match in self.matches_widget.matches:
            if match["id"] == match_id:
                self.current_match = match
                if set_number is not None:
                    self.target_set_number = max(1, int(set_number))
                else:
                    self.target_set_number = self._guess_next_set_number(match_id)
                self._load_and_show_formation(match)
                return True
        return False

    def _open_roster_setup(self, match_id: int):
        """
        Apri il dialog RosterSetup per il match_id specificato.
        Dopo il completamento del roster, caricherà automaticamente la formazione.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🧾 Gestione Squadre Partita")
        dialog.setModal(True)
        dialog.setMinimumSize(1000, 600)

        layout = QVBoxLayout(dialog)
        roster_widget = RosterSetupWidget(self.db, match_id=match_id, parent=dialog)

        layout.addWidget(roster_widget)
        dialog.setLayout(layout)

        # Quando il roster è completato, carica la formazione
        def on_roster_completed():
            """Callback completamento roster."""
            # Ricarica i match e apri direttamente la formation del match appena configurato
            opened = self.open_match_by_id(match_id)
            if not opened:
                print(f"⚠️ Match {match_id} non trovato dopo il salvataggio roster")

        roster_widget.roster_completed.connect(on_roster_completed)

        # Mostra il dialog
        dialog.exec()
