from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.volley_analizer.core.dv_codes import (
    DV_CODES,
    SKILL_CATEGORIES,
    find_attack_combo,
    find_dv_code,
    describe_trajectory,
)
from src.volley_analizer.core.dvw_importer import DvwImporter
from src.volley_analizer.ui.widgets.dv_code_legend import DvSkillTable
from src.volley_analizer.ui.widgets.formation_widget import FormationWidget


class DvwImportDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Importa DataVolley (.dvw)")
        self.resize(1100, 750)
        self._importer = DvwImporter()
        self._current_path: str | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Importazione file DataVolley (.dvw)")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        header.setFont(f)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        btn_layout = QHBoxLayout()
        self._import_btn = QPushButton("Apri file DVW...")
        self._import_btn.clicked.connect(self._open_file)
        btn_layout.addWidget(self._import_btn)

        self._status_label = QLabel("Nessun file caricato")
        btn_layout.addWidget(self._status_label, 1)
        layout.addLayout(btn_layout)

        self._tabs = QTabWidget()
        self._tabs.setEnabled(False)
        layout.addWidget(self._tabs, 1)

        self._build_match_tab()
        self._build_actions_tab()
        self._build_formation_tab()
        self._build_codes_tab()

    def _build_match_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        info_layout = QVBoxLayout(content)

        self._match_info = QLabel("Info partita")
        self._match_info.setWordWrap(True)
        info_layout.addWidget(self._match_info)

        self._players_table = QTableWidget()
        self._players_table.setColumnCount(6)
        self._players_table.setHorizontalHeaderLabels(
            ["#", "Cognome", "Nome", "Ruolo", "Libero", "Squadra"]
        )
        self._players_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._players_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        info_layout.addWidget(self._players_table)

        self._sets_table = QTableWidget()
        self._sets_table.setColumnCount(3)
        self._sets_table.setHorizontalHeaderLabels(["Set", "Casa", "Trasferta"])
        self._sets_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        info_layout.addWidget(self._sets_table)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        self._tabs.addTab(tab, "Partita")

    def _build_actions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._actions_table = QTableWidget()
        self._actions_table.setColumnCount(12)
        self._actions_table.setHorizontalHeaderLabels(
            [
                "Set", "Sq", "N°", "Skill", "Cod.", "Val.",
                "Zona P", "Zona A", "Combo", "Traiettoria", "Rot.", "Punteggio",
            ]
        )
        self._actions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._actions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._actions_table.setAlternatingRowColors(True)

        layout.addWidget(self._actions_table)
        self._tabs.addTab(tab, "Azioni")

    def _build_formation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self._formation_widget = FormationWidget()
        layout.addWidget(self._formation_widget)
        self._tabs.addTab(tab, "Sestetto / Rotazioni")

    def _build_codes_tab(self):
        tab = DvSkillTable()
        self._tabs.addTab(tab, "Legenda Codici")

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file DataVolley",
            str(Path.home()),
            "File DataVolley (*.dvw);;Tutti i file (*)",
        )
        if not path:
            return
        self._load_file(path)

    def load_path(self, path: str):
        self._load_file(path)

    def _load_file(self, path: str):
        self._current_path = path
        self._status_label.setText(f"Caricamento: {Path(path).name}...")
        self._status_label.repaint()

        try:
            result = self._importer.parse_file(path)
            self._display_result(result)
            self._status_label.setText(
                f"OK: {Path(path).name} — "
                f"{len(result.actions)} azioni, "
                f"{len(result.home_players)}+{len(result.away_players)} giocatori"
            )
            self._tabs.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile parsare il file:\n{e}")
            self._status_label.setText("Errore durante il caricamento")

    def _display_result(self, result):
        m = result.match
        home_name = m.home_team_name or m.home_team_code or "Casa"
        away_name = m.away_team_name or m.away_team_code or "Trasferta"
        date_str = m.date.strftime("%d/%m/%Y %H:%M") if m.date else "N/D"

        info = (
            f"<b>{home_name}</b> vs <b>{away_name}</b><br>"
            f"Data: {date_str}<br>"
            f"Competizione: {m.competition}<br>"
            f"Luogo: {m.venue}<br>"
            f"Video: {m.video_path or 'N/D'}"
        )
        self._match_info.setText(info)

        players = result.home_players + result.away_players
        self._players_table.setRowCount(len(players))
        for i, p in enumerate(players):
            self._players_table.setItem(i, 0, QTableWidgetItem(str(p.number)))
            self._players_table.setItem(i, 1, QTableWidgetItem(p.last_name))
            self._players_table.setItem(i, 2, QTableWidgetItem(p.first_name))
            self._players_table.setItem(i, 3, QTableWidgetItem(p.role))
            self._players_table.setItem(
                i, 4, QTableWidgetItem("Sì" if p.is_libero else "No")
            )
            side = "CASA" if p.team_side == "home" else "TRASFERTA"
            self._players_table.setItem(i, 5, QTableWidgetItem(side))

        self._sets_table.setRowCount(len(result.sets))
        for i, s in enumerate(result.sets):
            self._sets_table.setItem(i, 0, QTableWidgetItem(str(s.set_number)))
            self._sets_table.setItem(i, 1, QTableWidgetItem(str(s.score_home)))
            self._sets_table.setItem(i, 2, QTableWidgetItem(str(s.score_away)))

        actions = [a for a in result.actions if a.kind == "action"]
        self._actions_table.setRowCount(len(actions))
        for i, a in enumerate(actions):
            side_str = "C" if a.team_side == "home" else "T"
            dv_info = find_dv_code(a.skill_raw)
            cat_info = SKILL_CATEGORIES.get(a.skill, {})
            cat_label = cat_info.get("label", a.skill)

            traj = describe_trajectory(a.zone_start, a.zone_end, a.skill)
            combo_desc = ""
            if a.attack_combo:
                ac = find_attack_combo(a.attack_combo)
                if ac:
                    combo_desc = ac.label

            self._actions_table.setItem(
                i, 0, QTableWidgetItem(str(a.set_number))
            )
            self._actions_table.setItem(i, 1, QTableWidgetItem(side_str))
            self._actions_table.setItem(
                i, 2,
                QTableWidgetItem(str(a.player_number) if a.player_number else ""),
            )
            self._actions_table.setItem(i, 3, QTableWidgetItem(cat_label))
            self._actions_table.setItem(i, 4, QTableWidgetItem(a.skill_raw))
            self._actions_table.setItem(i, 5, QTableWidgetItem(a.evaluation or ""))
            self._actions_table.setItem(i, 6, QTableWidgetItem(a.zone_start or ""))
            self._actions_table.setItem(i, 7, QTableWidgetItem(a.zone_end or ""))
            self._actions_table.setItem(i, 8, QTableWidgetItem(combo_desc))
            self._actions_table.setItem(i, 9, QTableWidgetItem(traj))
            self._actions_table.setItem(
                i, 10, QTableWidgetItem(str(a.rotation))
            )
            self._actions_table.setItem(
                i, 11,
                QTableWidgetItem(f"{a.score_home}-{a.score_away}"),
            )

            for col in range(12):
                item = self._actions_table.item(i, col)
                if item and a.team_side == "home":
                    item.setBackground(
                        self._actions_table.palette().color(
                            self._actions_table.foregroundRole()
                        ).lighter(180)
                    )

        self._actions_table.resizeColumnsToContents()

        last_lineup_home = {}
        last_lineup_away = {}
        for a in reversed(result.actions):
            if a.kind == "action" and a.home_lineup and a.away_lineup:
                last_lineup_home = a.home_lineup
                last_lineup_away = a.away_lineup
                break

        if not last_lineup_home:
            lineup_action = next(
                (a for a in result.actions if a.kind == "lineup"), None
            )
            if lineup_action:
                last_lineup_home = lineup_action.home_lineup
                last_lineup_away = lineup_action.away_lineup

        self._formation_widget.update_lineups(
            last_lineup_home, last_lineup_away, rotation=1
        )
