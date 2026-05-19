"""
Volleyball Scout - Database Manager
Gestisce SQLite locale e PostgreSQL cloud tramite SQLAlchemy
"""

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestisce la connessione al database.
    - Locale: SQLite (default, file .db nella cartella dati)
    - Cloud:  PostgreSQL via DATABASE_URL env var
    """

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or self._resolve_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self._init_db()

    # ──────────────────────────────────
    #  Setup
    # ──────────────────────────────────

    def _resolve_url(self) -> str:
        """Legge DATABASE_URL da env, oppure usa SQLite locale"""
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            # Heroku/Railway usano postgres://, SQLAlchemy vuole postgresql://
            if env_url.startswith("postgres://"):
                env_url = env_url.replace("postgres://", "postgresql://", 1)
            logger.info("☁️  Usando database cloud: %s", env_url.split("@")[-1])
            return env_url

        data_dir = Path.home() / ".volleyball_scout" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        sqlite_path = data_dir / "scout.db"
        logger.info("💾 Usando database locale: %s", sqlite_path)
        return f"sqlite:///{sqlite_path}"

    def _create_engine(self):
        # Crea il motore SQLAlchemy per SQLite o PostgreSQL.
        if self.db_url.startswith("sqlite"):
            engine = create_engine(
                self.db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False,
            )

            # Abilita foreign keys su SQLite
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_conn, _):
                # Abilita i vincoli foreign key su SQLite.
                dbapi_conn.execute("PRAGMA foreign_keys=ON")
        else:
            engine = create_engine(
                self.db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
            )
        return engine

    def _init_db(self):
        """Crea tutte le tabelle se non esistono"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ Schema database inizializzato")

    # ──────────────────────────────────
    #  Session context manager
    # ──────────────────────────────────

    def get_session(self) -> Session:
        """Restituisce una nuova sessione del database."""
        return self.SessionLocal()

    def session_scope(self):
        """Context manager con commit/rollback automatico"""
        from contextlib import contextmanager

        @contextmanager
        def _scope():
            # Context manager interno con commit/rollback automatico.
            session = self.SessionLocal()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        return _scope()

    # ──────────────────────────────────
    #  Utility
    # ──────────────────────────────────

    def ping(self) -> bool:
        """Verifica che la connessione funzioni"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("DB ping failed: %s", e)
            return False

    def is_cloud(self) -> bool:
        """Indica se il database è PostgreSQL cloud."""
        return not self.db_url.startswith("sqlite")

    def get_db_info(self) -> dict:
        """Restituisce info sulla connessione al database."""
        return {
            "type": "PostgreSQL" if self.is_cloud() else "SQLite",
            "url_safe": self.db_url.split("@")[-1]
            if "@" in self.db_url
            else self.db_url,
            "connected": self.ping(),
        }


# Istanza globale singleton
_db_manager: DatabaseManager | None = None


def get_db() -> DatabaseManager:
    """Restituisce l'istanza singleton del database."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
