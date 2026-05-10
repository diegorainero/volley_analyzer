from pathlib import Path
from typing import Any

from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class EditMatchRolesDialog(QDialog):
    """Finestra di dialogo per modificare i ruoli dei giocatori per una partita specifica"""

    def __init__(self, team_name, players, parent=None):
        super().__init__(parent)
        self.team_name = team_name
        self.players = players  # Copia della lista dei giocatori
        self.role_changes = {}  # {player_id: new_role}

        self.setWindowTitle(f"Modifica Ruoli - {team_name}")
        self.setFixedSize(640, 520)

        layout = QVBoxLayout()

        # Titolo
        title = QLabel(f"Modifica ruoli per {team_name}")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Tabella con giocatori
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["#", "Nome", "Ruolo Attuale", "Nuovo Ruolo"]
        )
        self.table.setRowCount(len(players))
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionsMovable(False)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 180)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(34)

        roles = [
            "Palleggiatore",
            "Schiacciatore",
            "Opposto",
            "Centrale",
            "Libero",
            "Universale",
        ]

        for row, player in enumerate(players):
            # Numero
            num_item = QTableWidgetItem(str(player["number"]))
            num_item.setFlags(
                num_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )  # Read-only
            self.table.setItem(row, 0, num_item)

            # Nome
            name_item = QTableWidgetItem(player["last_name"])
            name_item.setFlags(
                name_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )  # Read-only
            self.table.setItem(row, 1, name_item)

            # Ruolo attuale
            current_role_item = QTableWidgetItem(player.get("role", ""))
            current_role_item.setFlags(
                current_role_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )  # Read-only
            self.table.setItem(row, 2, current_role_item)

            # Nuovo ruolo (combobox)
            role_combo = QComboBox()
            role_combo.addItems(roles)
            role_combo.setCurrentText(player.get("role", ""))
            role_combo.setProperty("player_id", player["id"])
            role_combo.currentTextChanged.connect(self._on_role_changed)
            self.table.setCellWidget(row, 3, role_combo)

        layout.addWidget(self.table)

        # Bottoni
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Annulla")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _on_role_changed(self, new_role):
        """Registra il cambio di ruolo"""
        sender = self.sender()
        player_id = sender.property("player_id")
        self.role_changes[player_id] = new_role

    def get_role_changes(self):
        """Ritorna i cambiamenti di ruolo effettuati"""
        return self.role_changes


class PlayerButton(QPushButton):
    """- DRAGGABLE"""

    player_selected = pyqtSignal(int)  # player_id

    def __init__(
        self,
        number,
        player_id,
        role="",
        parent=None,
        is_titolare=False,
        photo_path=None,
    ):
        super().__init__(str(number), parent)
        self.player_id = player_id
        self.number = number
        self.role = role
        self.photo_path = photo_path
        self.is_selected = False
        self.is_disabled = False
        self.is_titolare = is_titolare  # True se giocatore titolare
        self.setFixedSize(56, 56)
        self.setAcceptDrops(False)  # Non accetta drop
        self._update_style()

    def mousePressEvent(self, event):
        """Inizia il drag quando si clicca"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Crea il drag
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(f"{self.player_id}|{self.number}")
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)
        super().mousePressEvent(event)

    def _resolved_photo_path(self):
        """Restituisce il path foto valido per il background, se disponibile."""
        if not self.photo_path:
            return None

        p = Path(str(self.photo_path))
        if p.exists():
            return p.as_posix()

        return None

    def _update_style(self):
        # Determina il testo del bottone
        button_text = str(self.number)
        # Aggiunge "P" se il giocatore è palleggiatore
        if self.role and "palleggiatore" in self.role.lower():
            button_text += "P"

        photo_path = self._resolved_photo_path()
        photo_css = ""
        if photo_path:
            photo_css = (
                f'background-image: url("{photo_path}"); '
                "background-position: center; "
                "background-repeat: no-repeat;"
            )

        if self.is_titolare:
            # Stile titolari: palette Ubuntu
            if self.is_selected:
                self.setStyleSheet(
                    f"""
                    QPushButton {{
                        border-radius: 24px;
                        font-weight: bold;
                        font-size: 13px;
                        background-color: #E9A06B;
                        color: #2B211C;
                        border: 2px solid #E95420;
                        cursor: move;
                        {photo_css}
                    }}
                    QPushButton:hover {{
                        background-color: #F2B284;
                    }}
                """
                )
            else:
                self.setStyleSheet(
                    f"""
                    QPushButton {{
                        border-radius: 24px;
                        font-weight: bold;
                        font-size: 13px;
                        background-color: #8A613F;
                        color: white;
                        border: 2px solid #6E4B32;
                        cursor: move;
                        {photo_css}
                    }}
                    QPushButton:hover {{
                        background-color: #A1734A;
                    }}
                """
                )
        else:
            # Stile liberi
            if self.is_selected:
                self.setStyleSheet(
                    f"""
                    QPushButton {{
                        border-radius: 24px;
                        font-weight: bold;
                        font-size: 13px;
                        background-color: #F4D29A;
                        color: #2B211C;
                        border: 2px solid #E95420;
                        cursor: move;
                        {photo_css}
                    }}
                    QPushButton:hover {{
                        background-color: #F9DEB8;
                    }}
                """
                )
            else:
                self.setStyleSheet(
                    f"""
                    QPushButton {{
                        border-radius: 24px;
                        font-weight: bold;
                        font-size: 13px;
                        background-color: #9C6F45;
                        color: white;
                        border: 2px solid #8A613F;
                        cursor: move;
                        {photo_css}
                    }}
                    QPushButton:hover {{
                        background-color: #B88757;
                    }}
                """
                )
        self.setText(button_text)

    def set_selected(self, selected):
        self.is_selected = selected
        self._update_style()

    def set_disabled(self, disabled: bool):
        """Disabilita visivamente il bottone quando il giocatore è in campo"""
        self.is_disabled = disabled
        if disabled:
            # Stile disabilitato: grigio, non-interattivo
            self.setStyleSheet(
                """
                QPushButton {
                    border-radius: 18px;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #cccccc;
                    color: #999999;
                    border: 2px solid #aaaaaa;
                    cursor: forbidden;
                }
                QPushButton:hover {
                    background-color: #cccccc;
                }
            """
            )
            self.setAcceptDrops(False)
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            # Stile abilitato: ritorna alla normalità
            self.setAcceptDrops(False)  # Non accetta drop comunque
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self._update_style()


class FormationSlot(QFrame):
    """Slot per posizionare un giocatore in campo (rettangolo giallo) - DROP ZONE. SOLO TITOLARI!"""

    def __init__(self, position_name, parent=None):
        super().__init__(parent)
        self.position_name = position_name
        self.player_id = None
        self.player_number = None
        self.player_role = None  # Ruolo del giocatore (es. "Palleggiatore")
        self.player_photo_path = None
        self.formation_widget: Any = None  # Riferimento al TeamFormationWidget padre
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(56, 56)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.label = QLabel("-")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #2B211C;")

        layout.addWidget(self.label)
        self.setLayout(layout)
        self._update_style()

    def _resolved_photo_path(self):
        if not self.player_photo_path:
            return None

        p = Path(str(self.player_photo_path))
        if p.exists():
            return p.as_posix()

        return None

    def _update_style(self):
        photo_path = self._resolved_photo_path()

        if self.player_id is None:
            self.label.setStyleSheet("color: #6B7280;")
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px dashed #B7A2B0;
                    border-radius: 12px;
                    background-color: #F7ECE8;
                }
                """
            )
        elif photo_path:
            self.label.setStyleSheet(
                "color: white; background-color: rgba(43, 33, 28, 0.55); border-radius: 8px; padding: 1px 4px;"
            )
            self.setStyleSheet(
                f"""
                QFrame {{
                    border: 2px solid #E95420;
                    border-radius: 12px;
                    background-color: #2B211C;
                    background-image: url(\"{photo_path}\");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
                """
            )
        else:
            self.label.setStyleSheet("color: #2B211C;")
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px solid #E95420;
                    border-radius: 12px;
                    background-color: #FDE8D7;
                }
                """
            )

    def dragEnterEvent(self, event):
        """Accetta il drag"""
        if event.mimeData().hasText():
            event.accept()
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px solid #E95420;
                    border-radius: 12px;
                    background-color: #FBD8C4;
                }
                """
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Ripristina lo stile quando il drag esce"""
        self._update_style()

    def dropEvent(self, event):
        """Gestisce il drop"""
        if event.mimeData().hasText():
            data = event.mimeData().text().split("|")
            if len(data) == 2:
                player_id = int(data[0])
                player_number = int(data[1])

                # Validazione: verifica se il giocatore è già in campo
                if (
                    self.formation_widget
                    and player_id in self.formation_widget.used_players
                ):
                    # Se è lo stesso giocatore già in questo slot, consenti il drop
                    if self.player_id != player_id:
                        QMessageBox.warning(
                            self,
                            "Giocatore duplicato",
                            f"Il giocatore #{player_number} è già posizionato in campo.",
                        )
                        event.ignore()
                        self._update_style()
                        return

                # Recupera il role e lo stato libero del giocatore
                player_role = None
                is_libero = False
                if self.formation_widget:
                    for p in self.formation_widget.players:
                        if p["id"] == player_id:
                            player_role = p.get("role")
                            is_libero = p.get("is_libero", False)
                            break

                # Validazione: impedisci ai liberi di entrare negli slot di formazione
                if is_libero:
                    QMessageBox.warning(
                        self,
                        "Giocatore non valido",
                        f"Il giocatore #{player_number} è un libero e non può essere posizionato nella formazione titolari.\n"
                        f"Posizionalo nello slot liberi a sinistra.",
                    )
                    event.ignore()
                    self._update_style()
                    return

                self.set_player(player_number, player_id, player_role)
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()
        self._update_style()

    def mousePressEvent(self, event):
        """Pulisce lo slot quando si clicca se contiene un giocatore"""
        if event.button() == Qt.MouseButton.LeftButton and self.player_id is not None:
            self.clear()

    def set_player(self, player_number, player_id, player_role=None):
        """Imposta il giocatore in questo slot"""
        # Se era già presente un giocatore diverso, rimuovilo dal tracciamento
        if self.player_id is not None and self.player_id != player_id:
            if self.formation_widget:
                # Riabilita il bottone del giocatore precedente
                if self.player_id in self.formation_widget.player_buttons:
                    self.formation_widget.player_buttons[self.player_id].set_disabled(
                        False
                    )
                self.formation_widget.unregister_player(self.player_id)

        self.player_id = player_id
        self.player_number = player_number
        self.player_role = player_role
        self.player_photo_path = None
        if self.formation_widget:
            self.player_photo_path = self.formation_widget.get_player_photo_path(
                player_id
            )

        # Aggiorna il testo del label per includere "P" se palleggiatore
        label_text = str(player_number)
        if player_role and "palleggiatore" in player_role.lower():
            label_text += "P"
        self.label.setText(label_text)

        # Registra il giocatore come in uso
        if self.formation_widget:
            self.formation_widget.register_player(player_id)
            # Disabilita il bottone del giocatore
            if player_id in self.formation_widget.player_buttons:
                self.formation_widget.player_buttons[player_id].set_disabled(True)

        self._update_style()

    def clear(self):
        """Pulisce lo slot"""
        # Deregistra il giocatore dal tracciamento
        if self.player_id is not None and self.formation_widget:
            # Riabilita il bottone del giocatore
            if self.player_id in self.formation_widget.player_buttons:
                self.formation_widget.player_buttons[self.player_id].set_disabled(False)
            self.formation_widget.unregister_player(self.player_id)

        self.player_id = None
        self.player_number = None
        self.player_role = None
        self.player_photo_path = None
        self.label.setText("-")
        self._update_style()


class LiberoSlot(QFrame):
    """Slot per il libero (più piccolo) - DROP ZONE"""

    def __init__(self, label_text="Libero", parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.player_id = None
        self.player_number = None
        self.player_role = None  # Ruolo del giocatore (es. "Palleggiatore")
        self.player_photo_path = None
        self.formation_widget: Any = None  # Riferimento al TeamFormationWidget padre
        self.setAcceptDrops(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)

        self.label = QLabel("-")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #2B211C;")

        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setFixedSize(76, 76)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self._update_style()

    def _resolved_photo_path(self):
        if not self.player_photo_path:
            return None

        p = Path(str(self.player_photo_path))
        if p.exists():
            return p.as_posix()

        return None

    def _update_style(self):
        photo_path = self._resolved_photo_path()

        if self.player_id is None:
            self.label.setStyleSheet("color: #6B7280;")
            self.setStyleSheet(
                """
                QFrame {
                    background-color: #FFF2E8;
                    border: 2px dashed #E3B8A3;
                    border-radius: 10px;
                }
            """
            )
        elif photo_path:
            self.label.setStyleSheet(
                "color: white; background-color: rgba(43, 33, 28, 0.55); border-radius: 8px; padding: 1px 4px;"
            )
            self.setStyleSheet(
                f"""
                QFrame {{
                    background-color: #2B211C;
                    border: 2px solid #E95420;
                    border-radius: 10px;
                    background-image: url(\"{photo_path}\");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """
            )
        else:
            self.label.setStyleSheet("color: #2B211C;")
            self.setStyleSheet(
                """
                QFrame {
                    background-color: #FBDCCB;
                    border: 2px solid #E95420;
                    border-radius: 10px;
                }
            """
            )

    def dragEnterEvent(self, event):
        """Accetta il drag"""
        if event.mimeData().hasText():
            event.accept()
            self.setStyleSheet(
                """
                QFrame {
                    background-color: #FFE8D9;
                    border: 2px solid #E95420;
                    border-radius: 10px;
                }
            """
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Ripristina lo stile quando il drag esce"""
        self._update_style()

    def dropEvent(self, event):
        """Gestisce il drop"""
        if event.mimeData().hasText():
            data = event.mimeData().text().split("|")
            if len(data) == 2:
                player_id = int(data[0])
                player_number = int(data[1])

                # Validazione: verifica se il giocatore è già in campo
                if (
                    self.formation_widget
                    and player_id in self.formation_widget.used_players
                ):
                    # Se è lo stesso giocatore già in questo slot, consenti il drop
                    if self.player_id != player_id:
                        QMessageBox.warning(
                            self,
                            "Giocatore duplicato",
                            f"Il giocatore #{player_number} è già posizionato in campo.",
                        )
                        event.ignore()
                        self._update_style()
                        return

                # Recupera il role del giocatore
                player_role = None
                if self.formation_widget:
                    for p in self.formation_widget.players:
                        if p["id"] == player_id:
                            player_role = p.get("role")
                            break

                self.set_player(player_number, player_id, player_role)
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()
        self._update_style()

    def mousePressEvent(self, event):
        """Pulisce lo slot quando si clicca se contiene un giocatore"""
        if event.button() == Qt.MouseButton.LeftButton and self.player_id is not None:
            self.clear()

    def set_player(self, player_number, player_id, player_role=None):
        """Imposta il giocatore in questo slot"""
        # Se era già presente un giocatore diverso, rimuovilo dal tracciamento
        if self.player_id is not None and self.player_id != player_id:
            if self.formation_widget:
                # Riabilita il bottone del giocatore precedente
                if self.player_id in self.formation_widget.player_buttons:
                    self.formation_widget.player_buttons[self.player_id].set_disabled(
                        False
                    )
                self.formation_widget.unregister_player(self.player_id)

        self.player_id = player_id
        self.player_number = player_number
        self.player_role = player_role
        self.player_photo_path = None
        if self.formation_widget:
            self.player_photo_path = self.formation_widget.get_player_photo_path(
                player_id
            )

        # Aggiorna il testo del label per includere "P" se palleggiatore
        label_text = str(player_number)
        if player_role and "palleggiatore" in player_role.lower():
            label_text += "P"
        self.label.setText(label_text)

        # Registra il giocatore come in uso
        if self.formation_widget:
            self.formation_widget.register_player(player_id)
            # Disabilita il bottone del giocatore
            if player_id in self.formation_widget.player_buttons:
                self.formation_widget.player_buttons[player_id].set_disabled(True)

        self._update_style()

    def clear(self):
        """Pulisce lo slot"""
        # Deregistra il giocatore dal tracciamento
        if self.player_id is not None and self.formation_widget:
            # Riabilita il bottone del giocatore
            if self.player_id in self.formation_widget.player_buttons:
                self.formation_widget.player_buttons[self.player_id].set_disabled(False)
            self.formation_widget.unregister_player(self.player_id)

        self.player_id = None
        self.player_number = None
        self.player_role = None
        self.player_photo_path = None
        self.label.setText("-")
        self._update_style()


class TeamFormationWidget(QWidget):
    """Widget per la formazione di una singola squadra"""

    def __init__(self, team, players, parent=None):
        super().__init__(parent)
        self.team = team
        self.players = players  # [{id, number, last_name, role}]
        self.players_by_id = {p.get("id"): p for p in players}
        self.player_buttons = {}
        self.formation_slots = {}
        self.libero_slots = {}
        self.selected_players = set()
        self.used_players = set()  # Tracciamento giocatori attualmente in campo

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Filtra giocatori titolari e liberi in base al ruolo
        liberi_players = [p for p in players if p.get("role", "").lower() == "libero"]
        titolari_players = [p for p in players if p.get("role", "").lower() != "libero"]

        # --- SEZIONE FORMAZIONE IN CAMPO (con bordo stile campo) ---
        formation_frame = QFrame()
        formation_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #6E4B32;
                border-radius: 12px;
                background-color: #FDF3ED;
            }
        """)
        formation_layout = QVBoxLayout()
        formation_layout.setContentsMargins(15, 15, 15, 15)
        formation_layout.setSpacing(8)

        # Layout centrale: elenco numeri a sinistra + box formazione a destra
        formation_body_layout = QHBoxLayout()
        formation_body_layout.setSpacing(12)
        formation_body_layout.setContentsMargins(0, 0, 0, 0)

        # Elenco numeri (laterale)
        elenco_frame = QFrame()
        elenco_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #6E4B32;
                border-radius: 8px;
                background-color: #2B211C;
            }
        """)
        elenco_layout = QVBoxLayout()
        elenco_layout.setContentsMargins(8, 8, 8, 8)
        elenco_layout.setSpacing(6)

        elenco_title = QLabel("ELENCO")
        elenco_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elenco_title.setStyleSheet(
            """
            background-color: #E95420;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 6px;
        """
        )
        elenco_layout.addWidget(elenco_title)

        # Grid dei giocatori titolari disponibili (più compatta)
        titolari_grid = QGridLayout()
        titolari_grid.setSpacing(6)
        titolari_grid.setContentsMargins(0, 0, 0, 0)

        row, col = 0, 0
        for player in titolari_players:
            btn = PlayerButton(
                player["number"],
                player["id"],
                role=player.get("role", ""),
                is_titolare=True,
                photo_path=player.get("photo"),
            )
            btn.player_selected.connect(self._on_player_button_clicked)
            btn.setFixedSize(48, 48)
            self.player_buttons[player["id"]] = btn
            titolari_grid.addWidget(btn, row, col)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        elenco_layout.addLayout(titolari_grid)
        elenco_layout.addStretch()
        elenco_frame.setLayout(elenco_layout)
        elenco_frame.setMaximumWidth(150)
        formation_body_layout.addWidget(elenco_frame, 0)

        # Grid della formazione in gioco (6 posizioni: P1-P6)
        formation_grid = QGridLayout()
        formation_grid.setSpacing(8)
        formation_grid.setContentsMargins(0, 0, 0, 0)

        positions = ["P1", "P2", "P3", "P4", "P5", "P6"]
        idx = 0
        for row in range(2):
            for col in range(3):
                # Crea un container per ogni posizione con bordo verde e background giallo
                position_container = QFrame()
                position_container.setStyleSheet("""
                    QFrame {
                        border: 2px solid #8A613F;
                        border-radius: 8px;
                        background-color: #FFF7F0;
                    }
                """)
                position_layout = QVBoxLayout()
                position_layout.setContentsMargins(6, 6, 6, 6)
                position_layout.setSpacing(0)

                slot = FormationSlot(positions[idx])
                slot.formation_widget = self
                self.formation_slots[idx] = slot

                position_layout.addWidget(slot, alignment=Qt.AlignmentFlag.AlignCenter)
                position_container.setLayout(position_layout)

                # Box formazione più compatti
                position_container.setMinimumSize(72, 64)

                formation_grid.addWidget(position_container, row, col)
                idx += 1

        formation_body_layout.addLayout(formation_grid, 1)

        formation_layout.addLayout(formation_body_layout)
        formation_frame.setLayout(formation_layout)
        formation_frame.setMaximumHeight(360)
        layout.addWidget(formation_frame)

        # --- SEZIONE LIBERI COMPATTA (ORIZZONTALE) ---
        libero_group = QGroupBox("Liberi")
        libero_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #E95420;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #2B211C;
                font-weight: bold;
                color: #F6EFE9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                font-weight: bold;
                font-size: 10px;
                color: #E95420;
                background-color: #2B211C;
            }
        """)
        libero_layout = QHBoxLayout()
        libero_layout.setSpacing(10)
        libero_layout.setContentsMargins(5, 3, 5, 3)

        # Sezione slot liberi (a sinistra)
        libero_slots_container = QVBoxLayout()
        libero_slots_container.setSpacing(2)
        libero_slots_container.setContentsMargins(0, 0, 0, 0)

        libero_slots_label = QLabel("Posizioni")
        libero_slots_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        libero_slots_label.setStyleSheet("color: #F6EFE9;")
        libero_slots_container.addWidget(libero_slots_label)

        libero_slots_grid = QGridLayout()
        libero_slots_grid.setSpacing(5)
        libero_slots_grid.setContentsMargins(0, 0, 0, 0)

        self.libero_slots[0] = LiberoSlot("L1")
        self.libero_slots[1] = LiberoSlot("L2")
        self.libero_slots[0].formation_widget = self
        self.libero_slots[1].formation_widget = self
        libero_slots_grid.addWidget(self.libero_slots[0], 0, 0)
        libero_slots_grid.addWidget(self.libero_slots[1], 0, 1)

        libero_slots_container.addLayout(libero_slots_grid)
        libero_layout.addLayout(libero_slots_container)

        # Separatore
        separator_v = QFrame()
        separator_v.setStyleSheet("""
            QFrame {
                background-color: #E95420;
                border: none;
            }
        """)
        separator_v.setFixedWidth(1)
        libero_layout.addWidget(separator_v)

        # Sezione giocatori liberi disponibili (a destra, in orizzontale)
        liberi_disponibili_container = QVBoxLayout()
        liberi_disponibili_container.setSpacing(2)
        liberi_disponibili_container.setContentsMargins(0, 0, 0, 0)

        liberi_disp_label = QLabel("Disponibili")
        liberi_disp_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        liberi_disp_label.setStyleSheet("color: #F6EFE9;")
        liberi_disponibili_container.addWidget(liberi_disp_label)

        # Grid dei giocatori liberi disponibili (in orizzontale)
        liberi_grid = QHBoxLayout()
        liberi_grid.setSpacing(3)
        liberi_grid.setContentsMargins(0, 0, 0, 0)

        for player in liberi_players:
            btn = PlayerButton(
                player["number"],
                player["id"],
                role=player.get("role", ""),
                photo_path=player.get("photo"),
            )
            btn.player_selected.connect(self._on_player_button_clicked)
            self.player_buttons[player["id"]] = btn
            liberi_grid.addWidget(btn)

        liberi_grid.addStretch()
        liberi_disponibili_container.addLayout(liberi_grid)
        libero_layout.addLayout(liberi_disponibili_container)

        libero_group.setLayout(libero_layout)
        libero_group.setMaximumHeight(140)
        layout.addWidget(libero_group)

        self.setLayout(layout)

    def _on_player_button_clicked(self, player_id):
        """Gestisce il click su un bottone giocatore"""
        sender = self.sender()
        if sender.is_selected:
            self.selected_players.add(player_id)
        else:
            self.selected_players.discard(player_id)

    def get_player_photo_path(self, player_id):
        """Restituisce il path foto del giocatore se disponibile."""
        player = self.players_by_id.get(player_id) if self.players_by_id else None
        return player.get("photo") if player else None

    def get_formation(self):
        """Restituisce la formazione (titolari e liberi) per questa squadra"""
        titolari = []
        liberi = []

        # Raccogli i titolari dai slot di formazione
        for slot in self.formation_slots.values():
            if slot.player_id is not None:
                titolari.append(slot.player_id)

        # Raccogli i liberi
        for slot in self.libero_slots.values():
            if slot.player_id is not None:
                liberi.append(slot.player_id)

        return {"titolari": titolari, "liberi": liberi}

    def register_player(self, player_id):
        """Registra un giocatore come in uso (in campo)"""
        self.used_players.add(player_id)

    def unregister_player(self, player_id):
        """Deregistra un giocatore (rimosso dal campo)"""
        self.used_players.discard(player_id)

    def reset_formation(self):
        """Pulisce la formazione"""
        for slot in self.formation_slots.values():
            slot.clear()
        for slot in self.libero_slots.values():
            slot.clear()
        for btn in self.player_buttons.values():
            btn.set_selected(False)
        self.selected_players.clear()

    def rotate_formation(self):
        """Ruota la formazione in senso orario"""
        # Rotazione in campo senso orario: P1→P2→P3→P4→P5→P6→P1
        # Prima:          Dopo rotazione:
        # P4 P3 P2        P5 P4 P3
        # P5 P6 P1        P6 P1 P2
        # Mapping: P1(idx0)→P6(idx5), P2(idx1)→P1(idx0), P3(idx2)→P2(idx1), etc
        # Indici: cosa che era in idx N va in idx N-1 (con wrap-around)
        # {0→5, 1→0, 2→1, 3→24→3→2→1 (senso orario in campo)
        # Layout campo attuale (4-3-2 sopra, 5-6-1 sotto):
        #                       P4 P3 P2  (anteposizione)
        #                       P5 P6 P1  (retroposizione - zona battuta)
        # Dopo rotazione oraria (P1 muove a P6, P6 a P5, etc):
        #                       P3 P2 P1  (anteposizione)
        #                       P4 P5 P6  (retroposizione - zona battuta)
        # Mapping indici slot (0=P1, 1=P2, 2=P3, 3=P4, 4=P5, 5=P6):
        # 0(P1)→5(P6), 5(P6)→4(P5), 4(P5)→3(P4),
        #                 3(P4)→2(P3), 2(P3)→1(P2), 1(P2)→0(P1)
        # Mapping corretto: P1→P6, P2→P1, P3→P2, P4→P3, P5→P4, P6→P5
        # In indici: 0→5, 1→0, 2→1, 3→2, 4→3, 5→4
        rotation_map = {0: 5, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4}

        # Salva lo stato attuale
        current_players = {}
        for idx, slot in self.formation_slots.items():
            if slot.player_id is not None:
                current_players[idx] = {
                    "player_id": slot.player_id,
                    "player_number": slot.player_number,
                    "player_role": slot.player_role,
                }
            else:
                current_players[idx] = None

        # Applica la rotazione
        for old_idx, new_idx in rotation_map.items():
            new_slot = self.formation_slots[new_idx]
            old_player = current_players[old_idx]

            if old_player is not None:
                new_slot.set_player(
                    old_player["player_number"],
                    old_player["player_id"],
                    old_player["player_role"],
                )
            else:
                new_slot.clear()

        # Avvisa il panel che la formazione è stata ruotata per aggiornare il metodo di gioco
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "detect_game_method"):
                parent.detect_game_method()
                break
            parent = parent.parent()


class FormationPanel(QWidget):
    formation_confirmed = pyqtSignal(dict)  # Emesso quando la formazione è confermata
    back_requested = pyqtSignal()  # Emesso quando l'utente clicca "Torna Indietro"

    def __init__(self, teams, players_by_team, parent=None, matches=None):
        super().__init__(parent)
        self.teams = teams  # [{id, name}]
        self.players_by_team = (
            players_by_team  # {team_id: [{id, number, last_name, role}]}
        )
        self.matches = matches or []  # Elenco dei match disponibili
        self.match_id = None  # ID del match attualmente selezionato
        self.team_widgets = {}
        self.game_method = None  # P-S-C o P-C-S
        self.left_team_header = None
        self.right_team_header = None
        self.teams_layout = None
        self.left_team_container = None
        self.right_team_container = None
        self.separator_widget = None
        self.team_containers = {}
        self.team_container_layouts = {}
        self.team_method_combos = {}
        self.team_method_auto_checkboxes = {}
        self.team_method_detected_labels = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Titolo principale
        title = QLabel("Inserisci la Formazione Iniziale")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Sezione riepilogo metodo di gioco (per entrambe le squadre)
        self.game_method_layout = QHBoxLayout()
        self.game_method_label = QLabel("Metodo di gioco:")
        self.game_method_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.game_method_layout.addWidget(self.game_method_label)
        self.game_method_layout.addStretch()

        self.game_method_display = QLabel("Metodo di gioco: -")
        self.game_method_display.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.game_method_layout.addWidget(self.game_method_display)
        layout.addLayout(self.game_method_layout)

        # NUOVO LAYOUT ORIZZONTALE: due squadre affiancate con separatore
        self.teams_layout = QHBoxLayout()
        self.teams_layout.setContentsMargins(0, 0, 0, 0)
        self.teams_layout.setSpacing(0)

        team_widgets_list = []
        for team in teams:
            team_widget = TeamFormationWidget(team, players_by_team[team["id"]])
            self.team_widgets[team["id"]] = team_widget
            team_widgets_list.append((team, team_widget))

        # TEAM A (prima squadra)
        if len(team_widgets_list) > 0:
            team_a, widget_a = team_widgets_list[0]
            team_a_container = QWidget()
            team_a_layout = QVBoxLayout()
            team_a_layout.setContentsMargins(10, 0, 10, 0)
            team_a_layout.setSpacing(10)

            # Header team A
            header_a = QLabel(f"Squadra: {team_a['name']}")
            header_a.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.left_team_header = header_a
            team_a_layout.addWidget(header_a)

            # Metodo gioco squadra A (default P-S-C, modificabile manualmente)
            team_a_method_layout = QHBoxLayout()
            team_a_method_layout.setSpacing(6)
            team_a_method_layout.addWidget(QLabel("Metodo:"))

            combo_method_a = QComboBox()
            combo_method_a.addItems(["P-S-C", "P-C-S"])
            combo_method_a.setCurrentText("P-S-C")
            combo_method_a.setMinimumWidth(90)
            combo_method_a.setEnabled(False)
            combo_method_a.currentTextChanged.connect(
                lambda _text, tid=team_a["id"]: self._refresh_game_method_summary()
            )
            self.team_method_combos[team_a["id"]] = combo_method_a
            team_a_method_layout.addWidget(combo_method_a)

            chk_auto_a = QCheckBox("Auto")
            chk_auto_a.setChecked(True)
            chk_auto_a.toggled.connect(
                lambda checked, tid=team_a["id"]: self._on_team_auto_method_toggled(
                    tid, checked
                )
            )
            self.team_method_auto_checkboxes[team_a["id"]] = chk_auto_a
            team_a_method_layout.addWidget(chk_auto_a)

            btn_detect_a = QPushButton("Rileva")
            btn_detect_a.setMaximumWidth(72)
            btn_detect_a.setIcon(
                self.style().standardIcon(
                    QStyle.StandardPixmap.SP_FileDialogContentsView
                )
            )
            btn_detect_a.clicked.connect(
                lambda checked, tid=team_a["id"]: self._detect_and_apply_team_method(
                    tid, force=True
                )
            )
            team_a_method_layout.addWidget(btn_detect_a)

            lbl_detect_a = QLabel("Rilevato: -")
            lbl_detect_a.setStyleSheet("font-size: 10px; color: #8F7D8A;")
            self.team_method_detected_labels[team_a["id"]] = lbl_detect_a
            team_a_method_layout.addWidget(lbl_detect_a)
            team_a_method_layout.addStretch()
            team_a_layout.addLayout(team_a_method_layout)

            # Widget formazione team A
            team_a_layout.addWidget(widget_a, 1)

            # Bottoni team A
            buttons_team_a = QHBoxLayout()
            buttons_team_a.setSpacing(4)

            btn_reset_a = QPushButton("Reset")
            btn_reset_a.setMaximumWidth(95)
            btn_reset_a.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
            )
            btn_reset_a.setStyleSheet(
                """
                QPushButton {
                    background-color: #6E4B32;
                    color: white;
                    font-weight: bold;
                    padding: 6px 8px;
                    border-radius: 5px;
                    border: 1px solid #5A3D2A;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #8A613F;
                }
                QPushButton:pressed {
                    background-color: #5A3D2A;
                }
            """
            )
            btn_reset_a.clicked.connect(
                lambda checked: self._reset_team_formation(team_a["id"])
            )
            buttons_team_a.addWidget(btn_reset_a)

            btn_rotate_a = QPushButton("Ruota")
            btn_rotate_a.setMaximumWidth(95)
            btn_rotate_a.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
            )
            btn_rotate_a.setStyleSheet(
                """
                QPushButton {
                    background-color: #E95420;
                    color: white;
                    font-weight: bold;
                    padding: 6px 8px;
                    border-radius: 5px;
                    border: 1px solid #C7451A;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #F06B3C;
                }
                QPushButton:pressed {
                    background-color: #C7451A;
                }
            """
            )
            btn_rotate_a.clicked.connect(
                lambda checked: self._rotate_team_formation(team_a["id"])
            )
            buttons_team_a.addWidget(btn_rotate_a)

            btn_elenco_a = QPushButton("Ruoli")
            btn_elenco_a.setMaximumWidth(95)
            btn_elenco_a.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)
            )
            btn_elenco_a.setStyleSheet(
                """
                QPushButton {
                    background-color: #8A613F;
                    color: white;
                    font-weight: bold;
                    padding: 6px 8px;
                    border-radius: 5px;
                    border: 1px solid #6E4B32;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #A5784D;
                }
                QPushButton:pressed {
                    background-color: #6E4B32;
                }
            """
            )
            btn_elenco_a.clicked.connect(
                lambda checked: self._open_team_roles_dialog(team_a["id"])
            )
            buttons_team_a.addWidget(btn_elenco_a)
            buttons_team_a.addStretch()
            team_a_layout.addLayout(buttons_team_a)

            team_a_container.setLayout(team_a_layout)
            self.left_team_container = team_a_container
            self.team_containers[team_a["id"]] = team_a_container
            self.team_container_layouts[team_a["id"]] = team_a_layout
            self.teams_layout.addWidget(team_a_container, 1)

        # SEPARATORE RETE CON SWITCH AL CENTRO
        separator_widget = QWidget()
        self.separator_widget = separator_widget
        separator_widget.setFixedWidth(70)
        separator_layout = QVBoxLayout()
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        separator_layout.addStretch()

        # Pulsante Switch al centro
        btn_switch = QPushButton("⇆")
        btn_switch.setFixedSize(50, 50)
        btn_switch.setStyleSheet(
            """
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                border-radius: 25px;
                border: 2px solid #C7451A;
                font-size: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #F06B3C;
            }
            QPushButton:pressed {
                background-color: #C7451A;
            }
        """
        )
        btn_switch.clicked.connect(self._switch_teams_formations)
        separator_layout.addWidget(btn_switch, alignment=Qt.AlignmentFlag.AlignCenter)

        separator_layout.addStretch()
        separator_widget.setLayout(separator_layout)
        self.teams_layout.addWidget(separator_widget)

        # TEAM B (seconda squadra)
        if len(team_widgets_list) > 1:
            team_b, widget_b = team_widgets_list[1]
            team_b_container = QWidget()
            team_b_layout = QVBoxLayout()
            team_b_layout.setContentsMargins(10, 0, 10, 0)
            team_b_layout.setSpacing(10)

            # Header team B
            header_b = QLabel(f"Squadra: {team_b['name']}")
            header_b.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.right_team_header = header_b
            team_b_layout.addWidget(header_b)

            # Metodo gioco squadra B (default P-S-C, modificabile manualmente)
            team_b_method_layout = QHBoxLayout()
            team_b_method_layout.setSpacing(6)
            team_b_method_layout.addWidget(QLabel("Metodo:"))

            combo_method_b = QComboBox()
            combo_method_b.addItems(["P-S-C", "P-C-S"])
            combo_method_b.setCurrentText("P-S-C")
            combo_method_b.setMinimumWidth(90)
            combo_method_b.setEnabled(False)
            combo_method_b.currentTextChanged.connect(
                lambda _text, tid=team_b["id"]: self._refresh_game_method_summary()
            )
            self.team_method_combos[team_b["id"]] = combo_method_b
            team_b_method_layout.addWidget(combo_method_b)

            chk_auto_b = QCheckBox("Auto")
            chk_auto_b.setChecked(True)
            chk_auto_b.toggled.connect(
                lambda checked, tid=team_b["id"]: self._on_team_auto_method_toggled(
                    tid, checked
                )
            )
            self.team_method_auto_checkboxes[team_b["id"]] = chk_auto_b
            team_b_method_layout.addWidget(chk_auto_b)

            btn_detect_b = QPushButton("Rileva")
            btn_detect_b.setMaximumWidth(72)
            btn_detect_b.setIcon(
                self.style().standardIcon(
                    QStyle.StandardPixmap.SP_FileDialogContentsView
                )
            )
            btn_detect_b.clicked.connect(
                lambda checked, tid=team_b["id"]: self._detect_and_apply_team_method(
                    tid, force=True
                )
            )
            team_b_method_layout.addWidget(btn_detect_b)

            lbl_detect_b = QLabel("Rilevato: -")
            lbl_detect_b.setStyleSheet("font-size: 10px; color: #8F7D8A;")
            self.team_method_detected_labels[team_b["id"]] = lbl_detect_b
            team_b_method_layout.addWidget(lbl_detect_b)
            team_b_method_layout.addStretch()
            team_b_layout.addLayout(team_b_method_layout)

            # Widget formazione team B
            team_b_layout.addWidget(widget_b, 1)

            # Bottoni team B
            buttons_team_b = QHBoxLayout()
            buttons_team_b.setSpacing(4)

            btn_reset_b = QPushButton("Reset")
            btn_reset_b.setMaximumWidth(95)
            btn_reset_b.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
            )
            btn_reset_b.setStyleSheet(
                """
                QPushButton {
                    background-color: #6E4B32;
                    color: white;
                    font-weight: bold;
                    padding: 6px 8px;
                    border-radius: 5px;
                    border: 1px solid #5A3D2A;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #8A613F;
                }
                QPushButton:pressed {
                    background-color: #5A3D2A;
                }
            """
            )
            btn_reset_b.clicked.connect(
                lambda checked: self._reset_team_formation(team_b["id"])
            )
            buttons_team_b.addWidget(btn_reset_b)

            btn_rotate_b = QPushButton("Ruota")
            btn_rotate_b.setMaximumWidth(95)
            btn_rotate_b.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
            )
            btn_rotate_b.setStyleSheet(
                """
                QPushButton {
                    background-color: #E95420;
                    color: white;
                    font-weight: bold;
                    padding: 6px 8px;
                    border-radius: 5px;
                    border: 1px solid #C7451A;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #F06B3C;
                }
                QPushButton:pressed {
                    background-color: #C7451A;
                }
            """
            )
            btn_rotate_b.clicked.connect(
                lambda checked: self._rotate_team_formation(team_b["id"])
            )
            buttons_team_b.addWidget(btn_rotate_b)

            btn_elenco_b = QPushButton("Ruoli")
            btn_elenco_b.setMaximumWidth(95)
            btn_elenco_b.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)
            )
            btn_elenco_b.setStyleSheet(
                """
                QPushButton {
                    background-color: #8A613F;
                    color: white;
                    font-weight: bold;
                    padding: 6px 8px;
                    border-radius: 5px;
                    border: 1px solid #6E4B32;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #A5784D;
                }
                QPushButton:pressed {
                    background-color: #6E4B32;
                }
            """
            )
            btn_elenco_b.clicked.connect(
                lambda checked: self._open_team_roles_dialog(team_b["id"])
            )
            buttons_team_b.addWidget(btn_elenco_b)
            buttons_team_b.addStretch()
            team_b_layout.addLayout(buttons_team_b)

            team_b_container.setLayout(team_b_layout)
            self.right_team_container = team_b_container
            self.team_containers[team_b["id"]] = team_b_container
            self.team_container_layouts[team_b["id"]] = team_b_layout
            self.teams_layout.addWidget(team_b_container, 1)

        layout.addLayout(self.teams_layout, 1)

        # Bottoni di controllo principali (sotto)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        btn_back = QPushButton("← Torna Indietro")
        btn_back.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        btn_back.setStyleSheet(
            """
            QPushButton {
                background-color: #6E4B32;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: 1px solid #5A3D2A;
            }
            QPushButton:hover {
                background-color: #8A613F;
            }
            QPushButton:pressed {
                background-color: #5A3D2A;
            }
        """
        )
        btn_back.clicked.connect(self.back_requested.emit)
        buttons_layout.addWidget(btn_back)

        buttons_layout.addStretch()

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_all)
        buttons_layout.addWidget(btn_reset)

        btn_confirm = QPushButton("Conferma Formazione")
        btn_confirm.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        btn_confirm.setStyleSheet(
            """
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: 1px solid #C7451A;
            }
            QPushButton:hover {
                background-color: #F06B3C;
            }
            QPushButton:pressed {
                background-color: #C7451A;
            }
        """
        )
        btn_confirm.clicked.connect(self.confirm_formation)
        buttons_layout.addWidget(btn_confirm)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self._refresh_game_method_summary()
        self.detect_game_method()

    def _rotate_team_formation(self, team_id: int):
        """Ruota la formazione della squadra specificata."""
        if team_id not in self.team_widgets:
            return
        self.team_widgets[team_id].rotate_formation()
        self.detect_game_method()

    def _reset_team_formation(self, team_id: int):
        """Resetta solo la formazione della squadra specificata."""
        if team_id not in self.team_widgets:
            return
        self.team_widgets[team_id].reset_formation()
        self.detect_game_method()

    def _reload_team_widget(self, team_id: int):
        """Ricrea il widget squadra per riallineare i box ai ruoli aggiornati."""
        if team_id not in self.team_container_layouts:
            return

        team_layout = self.team_container_layouts[team_id]
        old_widget = self.team_widgets.get(team_id)

        team_meta = next((t for t in self.teams if t["id"] == team_id), None)
        players = self.players_by_team.get(team_id, [])
        if team_meta is None:
            return

        new_widget = TeamFormationWidget(team_meta, players)

        insert_index = 2
        if old_widget is not None:
            current_index = team_layout.indexOf(old_widget)
            if current_index >= 0:
                insert_index = current_index
            team_layout.removeWidget(old_widget)
            old_widget.deleteLater()

        team_layout.insertWidget(insert_index, new_widget, 1)
        self.team_widgets[team_id] = new_widget

        # Ricalcola metodi dopo ricostruzione dei box
        self.detect_game_method()

    def _switch_teams_formations(self):
        """Scambia realmente i due campi (pannello sinistra/destra)."""
        if len(self.teams) != 2:
            return

        if (
            self.teams_layout is None
            or self.left_team_container is None
            or self.right_team_container is None
            or self.separator_widget is None
        ):
            return

        # Rimuovi i widget correnti dal layout
        self.teams_layout.removeWidget(self.left_team_container)
        self.teams_layout.removeWidget(self.separator_widget)
        self.teams_layout.removeWidget(self.right_team_container)

        # Re-inserisci invertendo i lati
        self.teams_layout.addWidget(self.right_team_container, 1)
        self.teams_layout.addWidget(self.separator_widget)
        self.teams_layout.addWidget(self.left_team_container, 1)

        # Aggiorna riferimenti interni
        self.left_team_container, self.right_team_container = (
            self.right_team_container,
            self.left_team_container,
        )
        self.left_team_header, self.right_team_header = (
            self.right_team_header,
            self.left_team_header,
        )

        # Mantieni allineato anche l'ordine logico delle squadre
        self.teams[0], self.teams[1] = self.teams[1], self.teams[0]

        # Refresh visivo
        self.teams_layout.activate()
        self.update()

        # Ridetecta il metodo di gioco
        self.detect_game_method()

    def _refresh_game_method_summary(self):
        """Aggiorna il riepilogo metodi gioco per entrambe le squadre."""
        summary_parts = []
        for team in self.teams:
            team_id = team["id"]
            combo = self.team_method_combos.get(team_id)
            selected = combo.currentText() if combo is not None else "P-S-C"
            summary_parts.append(f"{team['name']}: {selected}")

        if summary_parts:
            self.game_method_display.setText(
                "Metodo di gioco: " + " | ".join(summary_parts)
            )
        else:
            self.game_method_display.setText("Metodo di gioco: -")

        if self.teams:
            first_team_id = self.teams[0]["id"]
            first_combo = self.team_method_combos.get(first_team_id)
            self.game_method = first_combo.currentText() if first_combo else "P-S-C"

    def _on_team_auto_method_toggled(self, team_id: int, checked: bool):
        """Gestisce auto/manuale del metodo gioco per una squadra."""
        combo = self.team_method_combos.get(team_id)
        if combo is not None:
            combo.setEnabled(not checked)

        if checked:
            self._detect_and_apply_team_method(team_id, force=False)
        else:
            self._refresh_game_method_summary()

    def _detect_method_for_team(self, team_id: int):
        """Rileva il metodo di gioco per una singola squadra."""
        if team_id not in self.team_widgets:
            return None

        team_widget = self.team_widgets[team_id]
        players = team_widget.players

        setter_idx = None
        for idx, slot in team_widget.formation_slots.items():
            if not slot.player_id:
                continue
            for p in players:
                if p["id"] == slot.player_id and p.get("role") == "Palleggiatore":
                    setter_idx = idx
                    break
            if setter_idx is not None:
                break

        if setter_idx is None:
            return None

        detected_method = None
        oraria_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 0}
        adjacent_idx = oraria_map.get(setter_idx)

        if adjacent_idx is not None and adjacent_idx in team_widget.formation_slots:
            adjacent_slot = team_widget.formation_slots[adjacent_idx]
            if adjacent_slot.player_id:
                for p in players:
                    if p["id"] == adjacent_slot.player_id:
                        role = p.get("role", "").lower()
                        if any(
                            keyword in role
                            for keyword in [
                                "schiacciatore",
                                "opposto",
                                "banda",
                                "universale",
                            ]
                        ):
                            detected_method = "P-S-C"
                        elif "centrale" in role:
                            detected_method = "P-C-S"
                        break

        return detected_method

    def _detect_and_apply_team_method(self, team_id: int, force: bool = False):
        """Rileva e applica (se auto/manuale) il metodo gioco per squadra."""
        detected = self._detect_method_for_team(team_id)

        lbl_detect = self.team_method_detected_labels.get(team_id)
        if lbl_detect is not None:
            lbl_detect.setText(f"Rilevato: {detected or '-'}")

        combo = self.team_method_combos.get(team_id)
        auto_check = self.team_method_auto_checkboxes.get(team_id)
        auto_enabled = auto_check.isChecked() if auto_check is not None else False

        if combo is not None and detected and (force or auto_enabled):
            combo.setCurrentText(detected)

        self._refresh_game_method_summary()

    def detect_game_method(self):
        """Rileva automaticamente il metodo di gioco per entrambe le squadre."""
        if not self.teams:
            return

        for team in self.teams:
            self._detect_and_apply_team_method(team["id"], force=False)

        self._refresh_game_method_summary()

    def _autofill_liberi_if_available(self, team_widget):
        """Inserisce automaticamente i primi 2 liberi disponibili nei box L1/L2."""
        libero_candidates = sorted(
            [p for p in team_widget.players if p.get("role", "").lower() == "libero"],
            key=lambda p: p.get("number", 0),
        )

        if not libero_candidates:
            return

        for idx in sorted(team_widget.libero_slots.keys()):
            slot = team_widget.libero_slots[idx]
            if slot.player_id is not None:
                continue

            next_player = next(
                (
                    p
                    for p in libero_candidates
                    if p["id"] not in team_widget.used_players
                ),
                None,
            )

            if next_player is None:
                break

            slot.set_player(
                next_player["number"],
                next_player["id"],
                next_player.get("role"),
            )
            libero_candidates = [
                p for p in libero_candidates if p["id"] != next_player["id"]
            ]

    def confirm_formation(self):
        """Valida e conferma la formazione"""
        # Rileva automaticamente il metodo di gioco prima di confermare
        self.detect_game_method()

        titolari_by_team = {}
        libero_by_team = {}
        game_method_by_team = {}

        for team in self.teams:
            team_id = team["id"]
            team_widget = self.team_widgets[team_id]

            # Autofill liberi se disponibili
            self._autofill_liberi_if_available(team_widget)

            formation = team_widget.get_formation()

            # Validazione numero titolari (formazioni scritte)
            if len(formation["titolari"]) != 6:
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Seleziona 6 titolari per {team['name']}. "
                    f"Attualmente: {len(formation['titolari'])}",
                )
                return

            # Validazione palleggiatore obbligatorio
            has_setter_available = any(
                p["role"] == "Palleggiatore" for p in team_widget.players
            )

            if has_setter_available:
                titolari_ids = formation["titolari"]
                titolari_players = [
                    p for p in team_widget.players if p["id"] in titolari_ids
                ]
                has_setter_in_field = any(
                    p["role"] == "Palleggiatore" for p in titolari_players
                )

                if not has_setter_in_field:
                    dialog = QMessageBox(self)
                    dialog.setWindowTitle(f"Palleggiatore per {team['name']}")
                    dialog.setText(
                        "Nessun titolare ha il ruolo di Palleggiatore.\n\n"
                        "Seleziona uno dei titolari come palleggiatore temporaneo:"
                    )
                    dialog.setIcon(QMessageBox.Icon.Question)

                    combo = QComboBox()
                    options = [
                        f"#{p['number']} - {p['last_name']} ({p['role']})"
                        for p in titolari_players
                    ]
                    combo.addItems(options)

                    dialog.layout().addWidget(
                        combo, dialog.layout().rowCount(), 0, 1, 2
                    )
                    dialog.setStandardButtons(
                        QMessageBox.StandardButton.Ok
                        | QMessageBox.StandardButton.Cancel
                    )
                    dialog.setDefaultButton(QMessageBox.StandardButton.Ok)

                    result = dialog.exec()
                    if result != QMessageBox.StandardButton.Ok:
                        QMessageBox.warning(
                            self,
                            "Errore",
                            "Seleziona un palleggiatore per continuare",
                        )
                        return

            titolari_by_team[team_id] = formation["titolari"]
            libero_by_team[team_id] = (
                formation["liberi"][0] if formation["liberi"] else None
            )

            combo_method = self.team_method_combos.get(team_id)
            game_method_by_team[team_id] = (
                combo_method.currentText() if combo_method is not None else "P-S-C"
            )

        # Compatibilità con payload precedente
        if self.teams:
            self.game_method = game_method_by_team.get(self.teams[0]["id"], "P-S-C")
        else:
            self.game_method = "P-S-C"

        self.formation_confirmed.emit(
            {
                "titolari": titolari_by_team,
                "libero": libero_by_team,
                "game_method": self.game_method,
                "game_method_by_team": game_method_by_team,
            }
        )

    def _open_team_roles_dialog(self, team_id):
        """Apre il dialog di modifica ruoli per una squadra specifica"""
        if team_id not in self.team_widgets:
            return

        team_widget = self.team_widgets[team_id]
        team_name = None
        for team in self.teams:
            if team["id"] == team_id:
                team_name = team["name"]
                break

        if not team_name:
            return

        players = self.players_by_team.get(team_id, team_widget.players)
        dialog = EditMatchRolesDialog(team_name, players, self)
        if dialog.exec():
            # Applica i cambiamenti di ruolo ai dati dei giocatori
            role_changes = dialog.get_role_changes()
            for player_id, new_role in role_changes.items():
                for player in players:
                    if player["id"] == player_id:
                        player["role"] = new_role
                        break

            # Mantieni i dati sincronizzati e ricrea il widget squadra
            self.players_by_team[team_id] = players
            self._reload_team_widget(team_id)

            # Dopo i cambiamenti, rileva il metodo di gioco di nuovo
            self.detect_game_method()

    def open_edit_roles_dialog(self):
        """Apre la finestra di dialogo per modificare i ruoli dei giocatori per tutte le squadre"""
        for team in self.teams:
            self._open_team_roles_dialog(team["id"])

    def reset_all(self):
        """Resetta tutte le formazioni e le opzioni di gioco"""
        # Resetta le formazioni di tutte le squadre
        for team_id, team_widget in self.team_widgets.items():
            team_widget.reset_formation()

        # Reset metodo di gioco per entrambe le squadre
        for team_id, combo in self.team_method_combos.items():
            combo.setCurrentText("P-S-C")
            combo.setEnabled(False)

        for team_id, chk_auto in self.team_method_auto_checkboxes.items():
            chk_auto.setChecked(True)

        for team_id, lbl_detect in self.team_method_detected_labels.items():
            lbl_detect.setText("Rilevato: -")

        self.game_method = "P-S-C"
        self._refresh_game_method_summary()
