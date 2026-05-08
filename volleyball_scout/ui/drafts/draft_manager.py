"""
DraftManager - Gestisce il salvataggio automatico e il ripristino delle bozze
"""

from datetime import datetime
from typing import Optional

from volleyball_scout.core.database import DatabaseManager
from volleyball_scout.core.models import Match, MatchPlayer, ScoutEvent


class DraftManager:
    """Gestisce le sessioni di scout in bozza (draft)"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_draft(
        self, home_team_id: int, away_team_id: int, notes: str = ""
    ) -> int:
        """
        Crea una nuova sessione di scout in bozza.

        Args:
            home_team_id: ID della squadra di casa
            away_team_id: ID della squadra ospite
            notes: Note opzionali

        Returns:
            ID del match creato (in stato draft)
        """
        with self.db.session_scope() as session:
            match = Match(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                date=datetime.utcnow(),
                notes=notes,
                status="draft",
            )
            session.add(match)
            session.commit()
            return match.id

    def get_drafts(self) -> list:
        """
        Ottiene tutte le sessioni in bozza.

        Returns:
            Lista di match in stato draft ordinati per data di modifica decrescente
        """
        with self.db.session_scope() as session:
            drafts = (
                session.query(Match)
                .filter_by(status="draft")
                .order_by(Match.updated_at.desc())
                .all()
            )
            return [
                {
                    "id": m.id,
                    "home_team_id": m.home_team_id,
                    "away_team_id": m.away_team_id,
                    "home_team_name": m.home_team.name if m.home_team else "Unknown",
                    "away_team_name": m.away_team.name if m.away_team else "Unknown",
                    "date": m.date,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                    "notes": m.notes,
                }
                for m in drafts
            ]

    def get_draft(self, match_id: int) -> Optional[dict]:
        """
        Ottiene i dettagli di una bozza specifica.

        Args:
            match_id: ID del match

        Returns:
            Dizionario con i dettagli della bozza, oppure None se non trovato
        """
        with self.db.session_scope() as session:
            match = session.query(Match).filter_by(id=match_id, status="draft").first()
            if not match:
                return None

            return {
                "id": match.id,
                "home_team_id": match.home_team_id,
                "away_team_id": match.away_team_id,
                "home_team_name": match.home_team.name
                if match.home_team
                else "Unknown",
                "away_team_name": match.away_team.name
                if match.away_team
                else "Unknown",
                "date": match.date,
                "created_at": match.created_at,
                "updated_at": match.updated_at,
                "notes": match.notes,
            }

    def save_draft(self, match_id: int, notes: str = "") -> bool:
        """
        Salva/aggiorna una bozza (auto-save).

        Args:
            match_id: ID del match
            notes: Note da aggiornare (opzionale)

        Returns:
            True se salvato con successo, False altrimenti
        """
        with self.db.session_scope() as session:
            match = session.query(Match).filter_by(id=match_id).first()
            if not match:
                return False

            match.status = "draft"
            match.updated_at = datetime.utcnow()
            if notes:
                match.notes = notes

            session.commit()
            return True

    def resume_draft(self, match_id: int) -> bool:
        """
        Ripristina una bozza (cambia status a in_progress).

        Args:
            match_id: ID del match

        Returns:
            True se ripristinato con successo, False altrimenti
        """
        with self.db.session_scope() as session:
            match = session.query(Match).filter_by(id=match_id, status="draft").first()
            if not match:
                return False

            match.status = "in_progress"
            match.updated_at = datetime.utcnow()
            session.commit()
            return True

    def complete_draft(self, match_id: int) -> bool:
        """
        Completa una bozza (cambia status a completed).

        Args:
            match_id: ID del match

        Returns:
            True se completato con successo, False altrimenti
        """
        with self.db.session_scope() as session:
            match = session.query(Match).filter_by(id=match_id).first()
            if not match:
                return False

            match.status = "completed"
            match.updated_at = datetime.utcnow()
            session.commit()
            return True

    def delete_draft(self, match_id: int) -> bool:
        """
        Elimina una bozza e tutti gli eventi associati.

        Args:
            match_id: ID del match

        Returns:
            True se eliminato con successo, False altrimenti
        """
        with self.db.session_scope() as session:
            match = session.query(Match).filter_by(id=match_id, status="draft").first()
            if not match:
                return False

            # Elimina tutti gli eventi
            session.query(ScoutEvent).filter_by(match_id=match_id).delete()
            # Elimina tutti i MatchPlayer
            session.query(MatchPlayer).filter_by(match_id=match_id).delete()
            # Elimina il match
            session.delete(match)
            session.commit()
            return True

    def get_draft_event_count(self, match_id: int) -> int:
        """
        Ottiene il numero di eventi registrati in una bozza.

        Args:
            match_id: ID del match

        Returns:
            Numero di eventi
        """
        with self.db.session_scope() as session:
            count = session.query(ScoutEvent).filter_by(match_id=match_id).count()
            return count
