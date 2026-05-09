from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
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
        self.setGeometry(100, 100, 600, 500)

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

    def __init__(self, number, player_id, role="", parent=None, is_titolare=False):
        super().__init__(str(number), parent)
        self.player_id = player_id
        self.number = number
        self.role = role
        self.is_selected = False
        self.is_disabled = False
        self.is_titolare = is_titolare  # True se giocatore titolare
        self.setFixedSize(70, 70)
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

    def _update_style(self):
        # Determina il testo del bottone
        button_text = str(self.number)
        # Aggiunge "P" se il giocatore è palleggiatore
        if self.role and "palleggiatore" in self.role.lower():
            button_text += "P"

        if self.is_titolare:
            # Stile titolari: cerchi blu brillanti
            if self.is_selected:
                self.setStyleSheet(
                    """
                    QPushButton {
                        border-radius: 35px;
                        font-weight: bold;
                        font-size: 16px;
                        background-color: #FFD700;
                        color: #333;
                        border: 3px solid #FFA500;
                        cursor: move;
                    }
                    QPushButton:hover {
                        background-color: #FFED4E;
                    }
                """
                )
            else:
                self.setStyleSheet(
                    """
                    QPushButton {
                        border-radius: 35px;
                        font-weight: bold;
                        font-size: 16px;
                        background-color: #5B8DEF;
                        color: white;
                        border: 2px solid #3A5DB5;
                        cursor: move;
                    }
                    QPushButton:hover {
                        background-color: #7BA3FF;
                    }
                """
                )
        else:
            # Stile liberi: cerchi blu standard
            if self.is_selected:
                self.setStyleSheet(
                    """
                    QPushButton {
                        border-radius: 35px;
                        font-weight: bold;
                        font-size: 16px;
                        background-color: #f4c430;
                        color: #333;
                        border: 3px solid #e6b800;
                        cursor: move;
                    }
                    QPushButton:hover {
                        background-color: #ffdd47;
                    }
                """
                )
            else:
                self.setStyleSheet(
                    """
                    QPushButton {
                        border-radius: 35px;
                        font-weight: bold;
                        font-size: 16px;
                        background-color: #4a90e2;
                        color: white;
                        border: 2px solid #2e5cb8;
                        cursor: move;
                    }
                    QPushButton:hover {
                        background-color: #6ba3f5;
                    }
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
                    border-radius: 30px;
                    font-weight: bold;
                    font-size: 14px;
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
        self.formation_widget = None  # Riferimento al TeamFormationWidget padre
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(80, 80)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.label = QLabel("-")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #333;")

        layout.addWidget(self.label)
        self.setLayout(layout)
        self._update_style()

    def _update_style(self):
        if self.player_id is None:
            self.setStyleSheet(
                """
                QFrame {
                    border: 3px dashed #cccccc;
                    border-radius: 8px;
                    background-color: #ffffcc;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QFrame {
                    border: 3px solid #27ae60;
                    border-radius: 8px;
                    background-color: #d5f4e6;
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
                    border: 3px solid #27ae60;
                    border-radius: 8px;
                    background-color: #a9dfbf;
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
        self.formation_widget = None  # Riferimento al TeamFormationWidget padre
        self.setAcceptDrops(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)

        self.label = QLabel("-")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #333;")

        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setFixedSize(70, 70)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self._update_style()

    def _update_style(self):
        if self.player_id is None:
            self.setStyleSheet(
                """
                QFrame {
                    background-color: #e8d4a2;
                    border: 2px dashed #d4c5a0;
                    border-radius: 5px;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QFrame {
                    background-color: #e8d4a2;
                    border: 2px solid #d4c5a0;
                    border-radius: 5px;
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
                    background-color: #f5e6c8;
                    border: 3px solid #d4c5a0;
                    border-radius: 5px;
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
        self.label.setText("-")
        self._update_style()


class TeamFormationWidget(QWidget):
    """Widget per la formazione di una singola squadra"""

    def __init__(self, team, players, parent=None):
        super().__init__(parent)
        self.team = team
        self.players = players  # [{id, number, last_name, role}]
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
                border: 3px solid #2d5016;
                border-radius: 10px;
                background-color: #90EE90;
            }
        """)
        formation_layout = QVBoxLayout()
        formation_layout.setContentsMargins(15, 15, 15, 15)
        formation_layout.setSpacing(8)

        # Grid dei giocatori titolari disponibili (cerchi blu brillanti in alto)
        titolari_grid = QGridLayout()
        titolari_grid.setSpacing(10)
        titolari_grid.setContentsMargins(0, 0, 0, 0)

        row, col = 0, 0
        for player in titolari_players:
            btn = PlayerButton(
                player["number"],
                player["id"],
                role=player.get("role", ""),
                is_titolare=True,
            )
            btn.player_selected.connect(self._on_player_button_clicked)
            btn.setFixedSize(50, 50)
            self.player_buttons[player["id"]] = btn
            titolari_grid.addWidget(btn, row, col)

            col += 1
            if col >= 6:
                col = 0
                row += 1

        formation_layout.addLayout(titolari_grid)

        # Separatore visivo (linea nera 2px)
        separator = QFrame()
        separator.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: none;
            }
        """)
        separator.setFixedHeight(2)
        formation_layout.addWidget(separator)

        # Grid della formazione in gioco (6 posizioni: P1-P6)
        formation_grid = QGridLayout()
        formation_grid.setSpacing(15)
        formation_grid.setContentsMargins(0, 10, 0, 0)

        positions = ["P1", "P2", "P3", "P4", "P5", "P6"]
        idx = 0
        for row in range(2):
            for col in range(3):
                # Crea un container per ogni posizione con bordo verde e background giallo
                position_container = QFrame()
                position_container.setStyleSheet("""
                    QFrame {
                        border: 2px solid #2d5016;
                        border-radius: 6px;
                        background-color: #FFFACD;
                    }
                """)
                position_layout = QVBoxLayout()
                position_layout.setContentsMargins(8, 8, 8, 8)
                position_layout.setSpacing(0)

                slot = FormationSlot(positions[idx])
                slot.formation_widget = self
                self.formation_slots[idx] = slot

                position_layout.addWidget(slot, alignment=Qt.AlignmentFlag.AlignCenter)
                position_container.setLayout(position_layout)

                # Imposta una dimensione fissa per i box
                position_container.setMinimumSize(100, 85)

                formation_grid.addWidget(position_container, row, col)
                idx += 1

        formation_layout.addLayout(formation_grid)
        formation_frame.setLayout(formation_layout)
        layout.addWidget(formation_frame)

        # --- SEZIONE LIBERI COMPATTA (ORIZZONTALE) ---
        libero_group = QGroupBox("Liberi")
        libero_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #FF6B6B;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #FFE5E5;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 2px 0 2px;
                font-weight: bold;
                font-size: 9px;
                color: #CC0000;
            }
        """)
        libero_layout = QHBoxLayout()
        libero_layout.setSpacing(10)
        libero_layout.setContentsMargins(5, 3, 5, 3)

        # Sezione slot liberi (a sinistra)
        libero_slots_container = QVBoxLayout()
        libero_slots_container.setSpacing(2)
        libero_slots_container.setContentsMargins(0, 0, 0, 0)

        libero_slots_label = QLabel("Posizioni:")
        libero_slots_label.setFont(QFont("Arial", 7, QFont.Weight.Bold))
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
                background-color: #FF6B6B;
                border: none;
            }
        """)
        separator_v.setFixedWidth(1)
        libero_layout.addWidget(separator_v)

        # Sezione giocatori liberi disponibili (a destra, in orizzontale)
        liberi_disponibili_container = QVBoxLayout()
        liberi_disponibili_container.setSpacing(2)
        liberi_disponibili_container.setContentsMargins(0, 0, 0, 0)

        liberi_disp_label = QLabel("Disponibili:")
        liberi_disp_label.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        liberi_disponibili_container.addWidget(liberi_disp_label)

        # Grid dei giocatori liberi disponibili (in orizzontale)
        liberi_grid = QHBoxLayout()
        liberi_grid.setSpacing(3)
        liberi_grid.setContentsMargins(0, 0, 0, 0)

        for player in liberi_players:
            btn = PlayerButton(
                player["number"], player["id"], role=player.get("role", "")
            )
            btn.player_selected.connect(self._on_player_button_clicked)
            self.player_buttons[player["id"]] = btn
            liberi_grid.addWidget(btn)

        liberi_grid.addStretch()
        liberi_disponibili_container.addLayout(liberi_grid)
        libero_layout.addLayout(liberi_disponibili_container)

        libero_group.setLayout(libero_layout)
        libero_group.setMaximumHeight(85)
        layout.addWidget(libero_group)

        self.setLayout(layout)

    def _on_player_button_clicked(self, player_id):
        """Gestisce il click su un bottone giocatore"""
        sender = self.sender()
        if sender.is_selected:
            self.selected_players.add(player_id)
        else:
            self.selected_players.discard(player_id)

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

        # Sezione selezione metodo di gioco (nascoste inizialmente - determinate automaticamente)
        self.game_method_layout = QHBoxLayout()
        self.game_method_label = QLabel("Metodo di gioco:")
        self.game_method_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.game_method_layout.addWidget(self.game_method_label)
        self.game_method_layout.addSpacing(10)

        self.radio_psc = QRadioButton("P-S-C (Palleggio - Schiacciatore - Centrale)")
        self.radio_pcs = QRadioButton("P-C-S (Palleggio - Centrale - Schiacciatore)")
        # Default: nessuno selezionato
        self.radio_psc.setVisible(False)  # Nascosto - determinato automaticamente
        self.radio_pcs.setVisible(False)  # Nascosto - determinato automaticamente
        self.game_method_layout.addWidget(self.radio_psc)
        self.game_method_layout.addWidget(self.radio_pcs)
        self.game_method_layout.addStretch()

        self.game_method_display = QLabel("Metodo di gioco: -")
        self.game_method_display.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.game_method_layout.addWidget(self.game_method_display)
        layout.addLayout(self.game_method_layout)

        # NUOVO LAYOUT ORIZZONTALE: due squadre affiancate con separatore
        teams_layout = QHBoxLayout()
        teams_layout.setContentsMargins(0, 0, 0, 0)
        teams_layout.setSpacing(0)

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
            team_a_layout.addWidget(header_a)

            # Widget formazione team A
            team_a_layout.addWidget(widget_a, 1)

            # Bottoni team A
            buttons_team_a = QHBoxLayout()
            buttons_team_a.setSpacing(5)
            btn_rotate_a = QPushButton(f"🔄 Ruota")
            btn_rotate_a.setMaximumWidth(150)
            btn_rotate_a.setStyleSheet(
                """
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    font-weight: bold;
                    padding: 8px 12px;
                    border-radius: 5px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
                QPushButton:pressed {
                    background-color: #d35400;
                }
            """
            )
            btn_rotate_a.clicked.connect(
                lambda checked: self._rotate_team_formation(team_a["id"])
            )
            buttons_team_a.addWidget(btn_rotate_a)

            btn_elenco_a = QPushButton(f"📋 Elenco")
            btn_elenco_a.setMaximumWidth(150)
            btn_elenco_a.setStyleSheet(
                """
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    font-weight: bold;
                    padding: 8px 12px;
                    border-radius: 5px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
                QPushButton:pressed {
                    background-color: #76448a;
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
            teams_layout.addWidget(team_a_container, 1)

        # SEPARATORE RETE CON SWITCH AL CENTRO
        separator_widget = QWidget()
        separator_widget.setFixedWidth(70)
        separator_layout = QVBoxLayout()
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        separator_layout.addStretch()

        # Pulsante Switch al centro
        btn_switch = QPushButton("⟷")
        btn_switch.setFixedSize(50, 50)
        btn_switch.setStyleSheet(
            """
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                border-radius: 25px;
                border: 2px solid #e67e22;
                font-size: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """
        )
        btn_switch.clicked.connect(self._switch_teams_formations)
        separator_layout.addWidget(btn_switch, alignment=Qt.AlignmentFlag.AlignCenter)

        separator_layout.addStretch()
        separator_widget.setLayout(separator_layout)
        teams_layout.addWidget(separator_widget)

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
            team_b_layout.addWidget(header_b)

            # Widget formazione team B
            team_b_layout.addWidget(widget_b, 1)

            # Bottoni team B
            buttons_team_b = QHBoxLayout()
            buttons_team_b.setSpacing(5)
            btn_rotate_b = QPushButton(f"🔄 Ruota")
            btn_rotate_b.setMaximumWidth(150)
            btn_rotate_b.setStyleSheet(
                """
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    font-weight: bold;
                    padding: 8px 12px;
                    border-radius: 5px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
                QPushButton:pressed {
                    background-color: #d35400;
                }
            """
            )
            btn_rotate_b.clicked.connect(
                lambda checked: self._rotate_team_formation(team_b["id"])
            )
            buttons_team_b.addWidget(btn_rotate_b)

            btn_elenco_b = QPushButton(f"📋 Elenco")
            btn_elenco_b.setMaximumWidth(150)
            btn_elenco_b.setStyleSheet(
                """
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    font-weight: bold;
                    padding: 8px 12px;
                    border-radius: 5px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
                QPushButton:pressed {
                    background-color: #76448a;
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
            teams_layout.addWidget(team_b_container, 1)

        layout.addLayout(teams_layout, 1)

        # Bottoni di controllo principali (sotto)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        btn_back = QPushButton("← Torna Indietro")
        btn_back.setStyleSheet(
            """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #687475;
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
        btn_confirm.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """
        )
        btn_confirm.clicked.connect(self.confirm_formation)
        buttons_layout.addWidget(btn_confirm)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _switch_teams_formations(self):
        """Scambia le formazioni fra le due squadre"""
        if len(self.teams) != 2:
            return

        team_a_id = self.teams[0]["id"]
        team_b_id = self.teams[1]["id"]

        team_a_widget = self.team_widgets[team_a_id]
        team_b_widget = self.team_widgets[team_b_id]

        # Salva lo stato di team A
        team_a_state = {}
        for idx in range(6):
            slot = team_a_widget.formation_slots[idx]
            if slot.player_id:
                team_a_state[idx] = {
                    "player_id": slot.player_id,
                    "player_number": slot.player_number,
                    "player_role": slot.player_role,
                }

        # Salva lo stato di team B
        team_b_state = {}
        for idx in range(6):
            slot = team_b_widget.formation_slots[idx]
            if slot.player_id:
                team_b_state[idx] = {
                    "player_id": slot.player_id,
                    "player_number": slot.player_number,
                    "player_role": slot.player_role,
                }

        # Applica team A a team B
        for idx in range(6):
            slot = team_b_widget.formation_slots[idx]
            if idx in team_a_state:
                player = team_a_state[idx]
                slot.set_player(
                    player["player_number"],
                    player["player_id"],
                    player["player_role"],
                )
            else:
                slot.clear()

        # Applica team B a team A
        for idx in range(6):
            slot = team_a_widget.formation_slots[idx]
            if idx in team_b_state:
                player = team_b_state[idx]
                slot.set_player(
                    player["player_number"],
                    player["player_id"],
                    player["player_role"],
                )
            else:
                slot.clear()

        # Ridetecta il metodo di gioco
        self.detect_game_method()

    def detect_game_method(self):
        """Rileva automaticamente il metodo di gioco dalla formazione"""
        # Esamina solo la prima squadra per il metodo di gioco
        if not self.teams:
            return

        team_id = self.teams[0]["id"]
        team_widget = self.team_widgets[team_id]
        players = team_widget.players

        # Trova il palleggiatore OVUNQUE sia nella formazione
        # Mapping posizioni: idx 0=P1, 1=P2, 2=P3, 3=P4, 4=P5, 5=P6
        # Sequenza rotazione in campo: 1→6→5→4→3→2→1 (antioraria in indici: 0→5→4→3→2→1→0)
        setter_idx = None
        setter_player = None

        for idx, slot in team_widget.formation_slots.items():
            if slot.player_id:
                # Trova il giocatore nel roster
                for p in players:
                    if p["id"] == slot.player_id:
                        if p.get("role") == "Palleggiatore":
                            setter_idx = idx
                            setter_player = p
                        break
                if setter_idx is not None:
                    break

        # Se trovato il palleggiatore, controlla il giocatore in senso ORARIO (il prossimo)
        # Sequenza oraria in indici: 0→1→2→3→4→5→0
        detected_method = None
        if setter_idx is not None:
            # Calcola l'indice successivo in senso orario
            oraria_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 0}
            adjacent_idx = oraria_map.get(setter_idx)

            if adjacent_idx is not None and adjacent_idx in team_widget.formation_slots:
                adjacent_slot = team_widget.formation_slots[adjacent_idx]
                if adjacent_slot.player_id:
                    # Trova il giocatore adiacente
                    for p in players:
                        if p["id"] == adjacent_slot.player_id:
                            role = p.get("role", "").lower()
                            if any(
                                keyword in role
                                for keyword in ["schiacciatore", "opposto"]
                            ):
                                detected_method = "P-S-C"
                            elif "centrale" in role:
                                detected_method = "P-C-S"
                            break

        # Aggiorna la visualizzazione
        if detected_method:
            self.game_method_display.setText(f"Metodo di gioco: {detected_method}")
            self.game_method = detected_method
        else:
            self.game_method_display.setText("Metodo di gioco: Non rilevato")
            self.game_method = None

    def confirm_formation(self):
        """Valida e conferma la formazione"""
        # Rileva automaticamente il metodo di gioco prima di confermare
        self.detect_game_method()

        # Validazione metodo di gioco
        if not self.game_method:
            QMessageBox.warning(
                self,
                "Errore",
                "Impossibile rilevare il metodo di gioco automaticamente.\n"
                "Assicurati che il palleggiatore sia in posizione 1 (P1) e un schiacciatore/opposto "
                "o centrale sia in posizione 2 (P2).",
            )
            return

        titolari_by_team = {}
        libero_by_team = {}

        for team in self.teams:
            team_id = team["id"]
            team_widget = self.team_widgets[team_id]
            formation = team_widget.get_formation()

            # Validazione numero titolari
            if len(formation["titolari"]) != 6:
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Seleziona 6 titolari per {team['name']}. "
                    f"Attualmente: {len(formation['titolari'])}",
                )
                return

            # Libero è opzionale - non bloccare se non presente

            # Validazione palleggiatore obbligatorio
            # Controlla se il team ha almeno un giocatore con role "Palleggiatore"
            has_setter_available = any(
                p["role"] == "Palleggiatore" for p in team_widget.players
            )

            if has_setter_available:
                # Se il team ha un palleggiatore disponibile, deve essercene uno tra i titolari
                titolari_ids = formation["titolari"]
                titolari_players = [
                    p for p in team_widget.players if p["id"] in titolari_ids
                ]
                has_setter_in_field = any(
                    p["role"] == "Palleggiatore" for p in titolari_players
                )

                if not has_setter_in_field:
                    # Nessun titolare è palleggiatore, offri opzione di sceglierne uno dai titolari
                    dialog = QMessageBox(self)
                    dialog.setWindowTitle(f"Palleggiatore per {team['name']}")
                    dialog.setText(
                        "Nessun titolare ha il ruolo di Palleggiatore.\n\n"
                        "Seleziona uno dei titolari come palleggiatore temporaneo:"
                    )
                    dialog.setIcon(QMessageBox.Icon.Question)

                    # Crea combobox con opzioni
                    combo = QComboBox()
                    options = [
                        f"#{p['number']} - {p['last_name']} ({p['role']})"
                        for p in titolari_players
                    ]
                    combo.addItems(options)

                    # Aggiungi combobox al dialog
                    dialog.layout().addWidget(
                        combo, dialog.layout().rowCount(), 0, 1, 2
                    )

                    # Bottoni OK e Annulla
                    dialog.setStandardButtons(
                        QMessageBox.StandardButton.Ok
                        | QMessageBox.StandardButton.Cancel
                    )
                    dialog.setDefaultButton(QMessageBox.StandardButton.Ok)

                    # Mostra dialog
                    result = dialog.exec()

                    # Se utente clicca Annulla, blocca
                    if result != QMessageBox.StandardButton.Ok:
                        QMessageBox.warning(
                            self,
                            "Errore",
                            "Seleziona un palleggiatore per continuare",
                        )
                        return

                    # Se OK, continua (la scelta è stata registrata nella combobox)
                    # Non bloccare qui, continua pure con l'emit del segnale

            titolari_by_team[team_id] = formation["titolari"]
            # Libero è opzionale - prendi il primo se presente, altrimenti None
            libero_by_team[team_id] = (
                formation["liberi"][0] if formation["liberi"] else None
            )

        # Emetti il segnale con il formato atteso, includendo il metodo di gioco
        self.formation_confirmed.emit(
            {
                "titolari": titolari_by_team,
                "libero": libero_by_team,
                "game_method": self.game_method,
            }
        )

    def _open_team_roles_dialog(self, team_id):
        """Apre il dialog di modifica ruoli per una squadra specifica"""
        team_widget = self.team_widgets[team_id]
        team_name = None
        for team in self.teams:
            if team["id"] == team_id:
                team_name = team["name"]
                break

        if not team_name:
            return

        players = team_widget.players
        dialog = EditMatchRolesDialog(team_name, players, self)
        if dialog.exec():
            # Applica i cambiamenti di ruolo ai dati dei giocatori
            role_changes = dialog.get_role_changes()
            for player_id, new_role in role_changes.items():
                # Trova il giocatore e aggiorna il suo ruolo
                for player in players:
                    if player["id"] == player_id:
                        player["role"] = new_role
                        # Aggiorna anche il bottone se esiste
                        if player_id in team_widget.player_buttons:
                            btn = team_widget.player_buttons[player_id]
                            btn.role = new_role
                            btn._update_style()  # Ricostituisci lo stile con il nuovo ruolo
                        break
            # Dopo i cambiamenti, rileva il metodo di gioco di nuovo
            self.detect_game_method()

    def open_edit_roles_dialog(self):
        """Apre la finestra di dialogo per modificare i ruoli dei giocatori per tutte le squadre"""
        for team in self.teams:
            self._open_team_roles_dialog(team["id"])

    def reset_all(self):
        """Resetta tutte le formazioni e le opzioni di gioco"""
        # Resetta il metodo di gioco
        self.game_method = None
        self.game_method_display.setText("Metodo di gioco: -")

        # Resetta le formazioni di tutte le squadre
        for team_id, team_widget in self.team_widgets.items():
            team_widget.reset_formation()
