"""
Volleyball Scout - Team Management Widget
Gestisce l'interfaccia per squadre e giocatori
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

# Ensure imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Player, Team


class TeamManagementWidget(QWidget):
    """Widget per gestire squadre e giocatori"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
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
        header_layout.addWidget(QLabel("<h2>👥 Team & Players</h2>"))
        header_layout.addStretch()
        btn_add_team = QPushButton("➕ Aggiungi Squadra")
        btn_add_team.clicked.connect(self.enable_team_form)
        header_layout.addWidget(btn_add_team)
        main_layout.addLayout(header_layout)

        # Team management section
        team_section = QGroupBox("Squadre Disponibili")
        team_layout = QHBoxLayout()

        # Left side: Teams list
        self.teams_list = QListWidget()
        self.teams_list.itemClicked.connect(self.on_team_selected)
        team_layout.addWidget(self.teams_list, 1)

        # Right side: Team form
        self.team_form = QWidget()
        team_form_layout = QVBoxLayout(self.team_form)

        team_form_layout.addWidget(QLabel("<b>Informazioni Squadra</b>"))

        form_layout = QFormLayout()
        self.team_name_input = QLineEdit()
        self.team_short_name_input = QLineEdit()
        self.team_category_input = QLineEdit()
        self.team_venue_input = QLineEdit()
        self.team_logo_label = QLabel("(Nessun logo selezionato)")
        btn_choose_logo = QPushButton("Scegli Logo")
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
        team_form_layout.addWidget(QLabel("<b>Giocatrici</b>"))

        players_buttons = QHBoxLayout()
        btn_add_player = QPushButton("➕ Aggiungi Giocatrice")
        btn_add_player.clicked.connect(self.enable_player_form)
        btn_remove_player = QPushButton("❌ Rimuovi Giocatrice")
        btn_remove_player.clicked.connect(self.delete_player)
        players_buttons.addWidget(btn_add_player)
        players_buttons.addWidget(btn_remove_player)
        team_form_layout.addLayout(players_buttons)

        self.players_list = QListWidget()
        self.players_list.itemClicked.connect(self.on_player_selected)
        team_form_layout.addWidget(self.players_list)

        # Player form
        self.player_form = QWidget()
        player_form_layout = QVBoxLayout(self.player_form)

        player_form_layout.addWidget(QLabel("<b>Nuova Giocatrice</b>"))

        player_form_content = QFormLayout()
        self.player_first_name_input = QLineEdit()
        self.player_last_name_input = QLineEdit()
        self.player_number_input = QSpinBox()
        self.player_number_input.setMinimum(1)
        self.player_number_input.setMaximum(99)
        self.player_role_input = QLineEdit()
        self.player_photo_label = QLabel("(Nessuna foto selezionata)")
        btn_choose_photo = QPushButton("Scegli Foto")
        btn_choose_photo.clicked.connect(self.choose_player_photo)

        photo_layout = QHBoxLayout()
        photo_layout.addWidget(self.player_photo_label)
        photo_layout.addWidget(btn_choose_photo)

        player_form_content.addRow("Nome:", self.player_first_name_input)
        player_form_content.addRow("Cognome:", self.player_last_name_input)
        player_form_content.addRow("Numero:", self.player_number_input)
        player_form_content.addRow("Ruolo:", self.player_role_input)
        player_form_content.addRow("Foto:", photo_layout)
        player_form_layout.addLayout(player_form_content)

        player_form_layout.addStretch()

        # Save/Cancel buttons for player form
        player_buttons = QHBoxLayout()
        btn_save_player = QPushButton("✅ Salva Giocatrice")
        btn_save_player.clicked.connect(self.save_player)
        btn_cancel_player = QPushButton("❌ Annulla")
        btn_cancel_player.clicked.connect(lambda: self.player_form.hide())
        player_buttons.addWidget(btn_save_player)
        player_buttons.addWidget(btn_cancel_player)
        player_form_layout.addLayout(player_buttons)

        team_form_layout.addWidget(self.player_form)
        self.player_form.hide()

        team_form_layout.addStretch()

        # Save/Delete/Cancel buttons for team form
        save_delete_layout = QHBoxLayout()
        btn_save_team = QPushButton("✅ Salva Squadra")
        btn_save_team.clicked.connect(self.save_team)
        btn_delete_team = QPushButton("❌ Elimina Squadra")
        btn_delete_team.clicked.connect(self.delete_team)
        btn_cancel = QPushButton("↩️ Annulla")
        btn_cancel.clicked.connect(lambda: self.team_form.hide())
        save_delete_layout.addWidget(btn_save_team)
        save_delete_layout.addWidget(btn_delete_team)
        save_delete_layout.addWidget(btn_cancel)
        team_form_layout.addLayout(save_delete_layout)

        self.team_form.hide()
        team_layout.addWidget(self.team_form, 1)

        team_section.setLayout(team_layout)
        main_layout.addWidget(team_section)

        self.setLayout(main_layout)

    def load_teams(self):
        """Carica le squadre dal database"""
        self.teams_list.clear()

        try:
            session = self.db.get_session()
            teams = session.query(Team).all()

            if not teams:
                # Mostra messaggio se no teams
                item = QListWidgetItem(
                    "(Nessuna squadra - Clicca '➕ Aggiungi Squadra')"
                )
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.teams_list.addItem(item)
            else:
                for team in teams:
                    display_text = f"🏐 {team.name}"
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
                    display_text = f"#{player.number} - {full_name}"
                    if player.role:
                        display_text += f" ({player.role})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, player.id)
                    self.players_list.addItem(item)

                self.team_form.show()
                self.player_form.hide()

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
        self.player_form.hide()

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

        self.player_first_name_input.clear()
        self.player_last_name_input.clear()
        self.player_number_input.setValue(1)
        self.player_role_input.clear()
        self.player_photo_label.setText("(Nessuna foto selezionata)")
        self.current_player_photo = None
        self.current_player_id = None
        self.player_form.show()

    def on_player_selected(self, item: QListWidgetItem):
        """Quando viene selezionato un giocatore"""
        player_id = item.data(Qt.ItemDataRole.UserRole)

        if player_id is None:
            return

        try:
            session = self.db.get_session()
            player = session.query(Player).filter_by(id=player_id).first()

            if player:
                self.current_player_id = player.id
                self.player_first_name_input.setText(player.first_name or "")
                self.player_last_name_input.setText(player.last_name or "")
                self.player_number_input.setValue(player.number or 1)
                self.player_role_input.setText(player.role or "")

                if player.photo:
                    self.player_photo_label.setText(f"Foto: {Path(player.photo).name}")
                    self.current_player_photo = player.photo
                else:
                    self.player_photo_label.setText("(Nessuna foto selezionata)")
                    self.current_player_photo = None

            session.close()
        except Exception as e:
            print(f"❌ Errore selezione giocatore: {e}")

    def save_player(self):
        """Salva il giocatore nel database"""
        first_name = self.player_first_name_input.text().strip()
        last_name = self.player_last_name_input.text().strip()

        if not last_name:
            QMessageBox.warning(
                self, "Errore", "Inserisci almeno il cognome della giocatrice."
            )
            return

        if not self.current_team_id:
            QMessageBox.warning(self, "Errore", "Nessuna squadra selezionata.")
            return

        try:
            session = self.db.get_session()

            if self.current_player_id:
                player = (
                    session.query(Player).filter_by(id=self.current_player_id).first()
                )
            else:
                player = Player(team_id=self.current_team_id)

            player.first_name = first_name or None
            player.last_name = last_name
            player.number = self.player_number_input.value()
            player.role = self.player_role_input.text().strip() or None
            if self.current_player_photo:
                player.photo = self.current_player_photo

            session.add(player)
            session.commit()

            QMessageBox.information(
                self, "Successo", "Giocatrice salvata con successo!"
            )

            # Ricarica i giocatori della squadra
            if self.current_team_id:
                session_refresh = self.db.get_session()
                team_item = None
                for i in range(self.teams_list.count()):
                    item = self.teams_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == self.current_team_id:
                        team_item = item
                        break

                if team_item:
                    self.on_team_selected(team_item)

                session_refresh.close()

            self.player_form.hide()
            session.close()
        except Exception as e:
            print(f"❌ Errore salvataggio giocatore: {e}")
            QMessageBox.critical(self, "Errore", f"Errore salvataggio: {e}")

    def delete_player(self):
        """Elimina il giocatore dal database"""
        current_item = self.players_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Errore", "Seleziona una giocatrice da eliminare."
            )
            return

        player_id = current_item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            "Sei sicuro di voler eliminare questa giocatrice?",
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
                    self, "Successo", "Giocatrice eliminata con successo!"
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

    def choose_player_photo(self):
        """Sceglie la foto del giocatore"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Scegli Foto", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.current_player_photo = file_path
            self.player_photo_label.setText(f"Foto: {Path(file_path).name}")
