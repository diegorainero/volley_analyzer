"""
Volleyball Scout - Team Management Widget
Gestisce l'interfaccia per squadre e giocatori
"""

import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStyle,
    QVBoxLayout,
    QWidget,
)

# Ensure imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Player, Team

try:
    from volleyball_scout.ui.assets import get_role_icon
except ImportError:
    try:
        from .assets import get_role_icon
    except ImportError:
        get_role_icon = None


class ModifyPlayerDialog(QDialog):
    """Dialog per modificare i dettagli di un giocatore"""

    ROLES = ["Palleggiatore", "Opposto", "Schiacciatore", "Centrale", "Libero"]

    def __init__(self, player=None, parent=None):
        """Inizializza dialog modifica giocatore."""
        super().__init__(parent)
        self.player = player
        self.photo_path = player.photo if player else None

        self.setWindowTitle("Modifica Giocatore" if player else "Nuovo Giocatore")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui()
        self._load_player_data()

    def _setup_ui(self):
        """Crea l'interfaccia del dialog"""
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Nome
        self.first_name_input = QLineEdit()
        form_layout.addRow("Nome:", self.first_name_input)

        # Cognome
        self.last_name_input = QLineEdit()
        form_layout.addRow("Cognome:", self.last_name_input)

        # Numero maglia
        self.number_input = QSpinBox()
        self.number_input.setMinimum(0)
        self.number_input.setMaximum(99)
        form_layout.addRow("Numero Maglia:", self.number_input)

        # Ruolo
        self.role_combo = QComboBox()
        self.role_combo.addItems(self.ROLES)
        form_layout.addRow("Ruolo:", self.role_combo)

        # Foto
        self.photo_label = QLabel("(Nessuna foto selezionata)")
        btn_choose_photo = QPushButton("Seleziona Foto")
        btn_choose_photo.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        )
        btn_choose_photo.clicked.connect(self._choose_photo)

        photo_layout = QHBoxLayout()
        photo_layout.addWidget(self.photo_label)
        photo_layout.addWidget(btn_choose_photo)
        form_layout.addRow("Foto:", photo_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Pulsanti Salva/Annulla
        buttons_layout = QHBoxLayout()

        btn_save = QPushButton("Salva")
        btn_save.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        btn_save.clicked.connect(self.accept)

        btn_cancel = QPushButton("Annulla")
        btn_cancel.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        )
        btn_cancel.clicked.connect(self.reject)

        buttons_layout.addWidget(btn_save)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _load_player_data(self):
        """Carica i dati del giocatore nel form"""
        if self.player:
            self.first_name_input.setText(self.player.first_name or "")
            self.last_name_input.setText(self.player.last_name or "")
            self.number_input.setValue(self.player.number or 0)

            if self.player.role and self.player.role in self.ROLES:
                self.role_combo.setCurrentText(self.player.role)

            if self.player.photo:
                self.photo_label.setText(f"Foto: {Path(self.player.photo).name}")

    def _choose_photo(self):
        """Apre il dialog per scegliere la foto"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Scegli Foto", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.photo_path = file_path
            self.photo_label.setText(f"Foto: {Path(file_path).name}")

    def get_player_data(self):
        """Ritorna i dati modificati del giocatore"""
        return {
            "first_name": self.first_name_input.text().strip() or None,
            "last_name": self.last_name_input.text().strip(),
            "number": self.number_input.value(),
            "role": self.role_combo.currentText(),
            "photo": self.photo_path,
        }

    def validate(self):
        """Valida i dati inseriti"""
        last_name = self.last_name_input.text().strip()
        number = self.number_input.value()

        if not last_name:
            QMessageBox.warning(self, "Errore", "Il cognome è obbligatorio.")
            return False

        if number < 0 or number > 99:
            QMessageBox.warning(
                self, "Errore", "Il numero maglia deve essere tra 0 e 99."
            )
            return False

        if not self.role_combo.currentText():
            QMessageBox.warning(self, "Errore", "Seleziona un ruolo.")
            return False

        return True


class TeamManagementWidget(QWidget):
    """Widget per gestire squadre e giocatori"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        """Inizializza widget gestione squadre."""
        super().__init__(parent)
        self.db = db_manager
        self.current_team_id = None
        self.current_team_logo = None
        self.current_player_id = None
        self.current_player_photo = None

        self._setup_ui()
        self.load_teams()

    def _setup_ui(self):
        """Crea l'interfaccia utente"""
        main_layout = QVBoxLayout()

        # Header con titolo e pulsante aggiungi squadra
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2>Squadre e Giocatori</h2>"))
        header_layout.addStretch()
        btn_add_team = QPushButton("Nuova Squadra")
        btn_add_team.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        btn_add_team.clicked.connect(self.enable_team_form)
        header_layout.addWidget(btn_add_team)
        main_layout.addLayout(header_layout)

        # Team management section con QSplitter
        team_section = QGroupBox("Gestione Squadre")
        team_layout = QVBoxLayout()

        # QSplitter orizzontale
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT SIDE: Teams list (25%) ===
        teams_container = QWidget()
        teams_container_layout = QVBoxLayout(teams_container)
        teams_container_layout.setContentsMargins(0, 0, 0, 0)

        self.teams_list = QListWidget()
        self.teams_list.itemClicked.connect(self.on_team_selected)
        teams_container_layout.addWidget(self.teams_list)

        splitter.addWidget(teams_container)

        # === RIGHT SIDE: Team form + Players (75%) ===
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.team_form = QWidget()
        team_form_layout = QVBoxLayout(self.team_form)

        team_form_layout.addWidget(QLabel("<b>Informazioni Squadra</b>"))

        form_layout = QFormLayout()
        self.team_name_input = QLineEdit()
        self.team_short_name_input = QLineEdit()
        self.team_category_input = QLineEdit()
        self.team_venue_input = QLineEdit()
        self.team_logo_label = QLabel("(Nessun logo selezionato)")
        btn_choose_logo = QPushButton("Seleziona Logo")
        btn_choose_logo.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        )
        btn_choose_logo.clicked.connect(self.choose_team_logo)

        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.team_logo_label)
        logo_layout.addWidget(btn_choose_logo)

        form_layout.addRow("Nome:", self.team_name_input)
        form_layout.addRow("Abbreviazione:", self.team_short_name_input)
        form_layout.addRow("Categoria:", self.team_category_input)
        form_layout.addRow("Impianto:", self.team_venue_input)
        form_layout.addRow("Logo:", logo_layout)
        team_form_layout.addLayout(form_layout)

        # Players section
        team_form_layout.addWidget(QLabel("<b>Giocatori</b>"))

        players_buttons = QHBoxLayout()
        btn_add_player = QPushButton("Nuovo Giocatore")
        btn_add_player.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        btn_add_player.clicked.connect(self.enable_player_form)
        btn_remove_player = QPushButton("Rimuovi Giocatore")
        btn_remove_player.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        )
        btn_remove_player.clicked.connect(self.delete_player)
        players_buttons.addWidget(btn_add_player)
        players_buttons.addWidget(btn_remove_player)
        team_form_layout.addLayout(players_buttons)

        self.players_list = QListWidget()
        self.players_list.setIconSize(QSize(34, 34))
        self.players_list.setSpacing(4)
        self.players_list.itemClicked.connect(self.on_player_selected)
        self.players_list.itemDoubleClicked.connect(self.edit_player)
        team_form_layout.addWidget(self.players_list)

        team_form_layout.addStretch()

        # Save/Delete/Cancel buttons for team form
        save_delete_layout = QHBoxLayout()
        btn_save_team = QPushButton("Salva Squadra")
        btn_save_team.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        btn_save_team.clicked.connect(self.save_team)
        btn_delete_team = QPushButton("Elimina Squadra")
        btn_delete_team.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        )
        btn_delete_team.clicked.connect(self.delete_team)
        btn_cancel = QPushButton("Annulla")
        btn_cancel.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        )
        btn_cancel.clicked.connect(lambda: self.team_form.hide())
        save_delete_layout.addWidget(btn_save_team)
        save_delete_layout.addWidget(btn_delete_team)
        save_delete_layout.addWidget(btn_cancel)
        team_form_layout.addLayout(save_delete_layout)

        self.team_form.hide()

        right_layout.addWidget(self.team_form)
        splitter.addWidget(right_container)

        # Imposta i rapporti di larghezza (25% e 75%)
        splitter.setSizes([25, 75])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        team_layout.addWidget(splitter)
        team_section.setLayout(team_layout)
        main_layout.addWidget(team_section)

        self.setLayout(main_layout)

    def _resolve_image_path(self, image_path):
        # Risolve il path immagine se esiste.
        if not image_path:
            return None
        p = Path(str(image_path))
        return p if p.exists() else None

    def _build_player_icon(self, player):
        photo_path = self._resolve_image_path(getattr(player, "photo", None))
        if photo_path:
            source = QPixmap(str(photo_path))
            if not source.isNull():
                size = 34
                avatar = QPixmap(size, size)
                avatar.fill(Qt.GlobalColor.transparent)

                painter = QPainter(avatar)
                painter.setRenderHints(
                    QPainter.RenderHint.Antialiasing
                    | QPainter.RenderHint.SmoothPixmapTransform
                )
                clip = QPainterPath()
                clip.addEllipse(1, 1, size - 2, size - 2)
                painter.setClipPath(clip)

                scaled = source.scaled(
                    size - 2,
                    size - 2,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(1, 1, scaled)
                painter.setClipping(False)
                painter.setPen(QPen(QColor("#E95420"), 2))
                painter.drawEllipse(1, 1, size - 2, size - 2)
                painter.end()

                return QIcon(avatar)

        if callable(get_role_icon):
            role_icon = get_role_icon(getattr(player, "role", ""), size=18)
            if isinstance(role_icon, QIcon) and not role_icon.isNull():
                return role_icon

        return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def load_teams(self):
        """Carica le squadre dal database"""
        self.teams_list.clear()

        try:
            session = self.db.get_session()
            teams = session.query(Team).all()

            if not teams:
                # Mostra messaggio se no teams
                item = QListWidgetItem("(Nessuna squadra - Clicca 'Nuova Squadra')")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.teams_list.addItem(item)
            else:
                for team in teams:
                    display_text = f"{team.name}"
                    if team.short_name:
                        display_text += f" ({team.short_name})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, team.id)
                    self.teams_list.addItem(item)

            session.close()
        except Exception as e:
            print(f"❌ Errore caricamento squadre: {e}")
            QMessageBox.critical(self, "Errore", f"Errore caricamento squadre: {e}")

    def on_team_selected(self, item: QListWidgetItem):
        """Quando viene selezionata una squadra"""
        team_id = item.data(Qt.ItemDataRole.UserRole)

        if team_id is None:
            return

        try:
            session = self.db.get_session()
            team = session.query(Team).filter_by(id=team_id).first()

            if team:
                self.current_team_id = team.id
                self.team_name_input.setText(team.name or "")
                self.team_short_name_input.setText(team.short_name or "")
                self.team_category_input.setText(team.category or "")
                self.team_venue_input.setText(team.venue or "")

                if team.logo:
                    self.team_logo_label.setText(f"Logo: {Path(team.logo).name}")
                    self.current_team_logo = team.logo
                else:
                    self.team_logo_label.setText("(Nessun logo selezionato)")
                    self.current_team_logo = None

                # Carica giocatori della squadra
                self.players_list.clear()
                for player in team.players:
                    full_name = f"{player.first_name or ''} {player.last_name}".strip()
                    display_text = f"#{player.number:02d} - {full_name}"
                    if player.role:
                        display_text += f" ({player.role})"
                    item = QListWidgetItem(display_text)
                    item.setIcon(self._build_player_icon(player))
                    item.setData(Qt.ItemDataRole.UserRole, player.id)
                    self.players_list.addItem(item)

                self.team_form.show()

            session.close()
        except Exception as e:
            print(f"❌ Errore selezione squadra: {e}")
            QMessageBox.critical(self, "Errore", f"Errore selezione squadra: {e}")

    def enable_team_form(self):
        """Abilita il form per aggiungere una nuova squadra"""
        self.team_name_input.clear()
        self.team_short_name_input.clear()
        self.team_category_input.clear()
        self.team_venue_input.clear()
        self.team_logo_label.setText("(Nessun logo selezionato)")
        self.current_team_logo = None
        self.current_team_id = None
        self.players_list.clear()
        self.team_form.show()

    def save_team(self):
        """Salva la squadra nel database"""
        team_name = self.team_name_input.text().strip()
        if not team_name:
            QMessageBox.warning(self, "Errore", "Inserisci il nome della squadra.")
            return

        try:
            session = self.db.get_session()

            if self.current_team_id:
                team = session.query(Team).filter_by(id=self.current_team_id).first()
            else:
                team = Team()

            team.name = team_name
            team.short_name = self.team_short_name_input.text().strip() or None
            team.category = self.team_category_input.text().strip() or None
            team.venue = self.team_venue_input.text().strip() or None
            if self.current_team_logo:
                team.logo = self.current_team_logo

            session.add(team)
            session.commit()

            QMessageBox.information(self, "Successo", "Squadra salvata con successo!")
            self.load_teams()
            self.team_form.hide()
            session.close()
        except Exception as e:
            print(f"❌ Errore salvataggio squadra: {e}")
            QMessageBox.critical(self, "Errore", f"Errore salvataggio: {e}")

    def delete_team(self):
        """Elimina la squadra dal database"""
        if not self.current_team_id:
            QMessageBox.warning(self, "Errore", "Seleziona una squadra da eliminare.")
            return

        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            "Sei sicuro di voler eliminare questa squadra e tutti i suoi giocatori?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = self.db.get_session()
                team = session.query(Team).filter_by(id=self.current_team_id).first()
                if team:
                    session.delete(team)
                    session.commit()

                QMessageBox.information(
                    self, "Successo", "Squadra eliminata con successo!"
                )
                self.load_teams()
                self.team_form.hide()
                session.close()
            except Exception as e:
                print(f"❌ Errore eliminazione squadra: {e}")
                QMessageBox.critical(self, "Errore", f"Errore eliminazione: {e}")

    def choose_team_logo(self):
        """Sceglie il logo della squadra"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Scegli Logo", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.current_team_logo = file_path
            self.team_logo_label.setText(f"Logo: {Path(file_path).name}")

    def enable_player_form(self):
        """Abilita il form per aggiungere un nuovo giocatore"""
        if not self.current_team_id:
            QMessageBox.warning(
                self, "Errore", "Seleziona una squadra prima di aggiungere giocatori."
            )
            return

        dialog = ModifyPlayerDialog(None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_player_data()

            if not dialog.validate():
                return

            try:
                session = self.db.get_session()
                player = Player(team_id=self.current_team_id)

                player.first_name = data["first_name"]
                player.last_name = data["last_name"]
                player.number = data["number"]
                player.role = data["role"]
                if data["photo"]:
                    player.photo = data["photo"]

                session.add(player)
                session.commit()

                QMessageBox.information(
                    self, "Successo", "Giocatore aggiunto con successo!"
                )

                # Ricarica i giocatori della squadra
                if self.current_team_id:
                    for i in range(self.teams_list.count()):
                        item = self.teams_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) == self.current_team_id:
                            self.on_team_selected(item)
                            break

                session.close()
            except Exception as e:
                print(f"❌ Errore aggiunta giocatore: {e}")
                QMessageBox.critical(self, "Errore", f"Errore aggiunta: {e}")

    def on_player_selected(self, item: QListWidgetItem):
        """Quando viene selezionato un giocatore"""
        player_id = item.data(Qt.ItemDataRole.UserRole)

        if player_id is None:
            return

        try:
            session = self.db.get_session()
            self.current_player_id = player_id
            session.close()
        except Exception as e:
            print(f"❌ Errore selezione giocatore: {e}")

    def edit_player(self, item: QListWidgetItem):
        """Apre il dialog di modifica quando doppio-click su un giocatore"""
        player_id = item.data(Qt.ItemDataRole.UserRole)

        if player_id is None:
            return

        try:
            session = self.db.get_session()
            player = session.query(Player).filter_by(id=player_id).first()

            if player:
                dialog = ModifyPlayerDialog(player, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    if not dialog.validate():
                        return

                    data = dialog.get_player_data()

                    player.first_name = data["first_name"]
                    player.last_name = data["last_name"]
                    player.number = data["number"]
                    player.role = data["role"]
                    if data["photo"]:
                        player.photo = data["photo"]

                    session.add(player)
                    session.commit()

                    QMessageBox.information(
                        self, "Successo", "Giocatore modificato con successo!"
                    )

                    # Ricarica i giocatori della squadra
                    if self.current_team_id:
                        for i in range(self.teams_list.count()):
                            team_item = self.teams_list.item(i)
                            if (
                                team_item.data(Qt.ItemDataRole.UserRole)
                                == self.current_team_id
                            ):
                                self.on_team_selected(team_item)
                                break

            session.close()
        except Exception as e:
            print(f"❌ Errore modifica giocatore: {e}")
            QMessageBox.critical(self, "Errore", f"Errore modifica: {e}")

    def delete_player(self):
        """Elimina il giocatore dal database"""
        current_item = self.players_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Errore", "Seleziona un giocatore da eliminare.")
            return

        player_id = current_item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            "Sei sicuro di voler eliminare questo giocatore?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = self.db.get_session()
                player = session.query(Player).filter_by(id=player_id).first()
                if player:
                    session.delete(player)
                    session.commit()

                QMessageBox.information(
                    self, "Successo", "Giocatore eliminato con successo!"
                )

                # Ricarica i giocatori della squadra
                if self.current_team_id:
                    team_item = None
                    for i in range(self.teams_list.count()):
                        item = self.teams_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) == self.current_team_id:
                            team_item = item
                            break

                    if team_item:
                        self.on_team_selected(team_item)

                session.close()
            except Exception as e:
                print(f"❌ Errore eliminazione giocatore: {e}")
                QMessageBox.critical(self, "Errore", f"Errore eliminazione: {e}")
