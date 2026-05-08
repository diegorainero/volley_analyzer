"""
Volleyball Scout - Core Data Models
SQLAlchemy ORM compatibile SQLite (locale) e PostgreSQL (cloud)
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ─────────────────────────────────────────
#  ENUM per i codici DataVolley
# ─────────────────────────────────────────


class SkillCode(str, enum.Enum):
    SERVE = "S"
    RECEPTION = "R"
    SET = "E"
    ATTACK = "A"
    BLOCK = "B"
    DIG = "D"
    FREEBALL = "F"


class EvaluationCode(str, enum.Enum):
    PERFECT = "#"  # perfetto / ace / punto
    POSITIVE = "+"  # positivo
    OVERPASS = "!"  # sovramano
    NEGATIVE = "-"  # negativo
    ERROR = "="  # errore
    HALF = "/"  # metà


class ZoneCode(str, enum.Enum):
    Z1 = "1"
    Z2 = "2"
    Z3 = "3"
    Z4 = "4"
    Z5 = "5"
    Z6 = "6"
    Z7 = "7"
    Z8 = "8"
    Z9 = "9"


# ─────────────────────────────────────────
#  MODELLI
# ─────────────────────────────────────────


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(10))
    category = Column(String(50))  # es. "Serie A1", "Under 18"
    venue = Column(String(150))  # Impianto di gioco
    logo = Column(String(250))  # Path o URL logo
    created_at = Column(DateTime, default=datetime.utcnow)

    players = relationship(
        "Player", back_populates="team", cascade="all, delete-orphan"
    )
    matches_home = relationship(
        "Match", foreign_keys="Match.home_team_id", back_populates="home_team"
    )
    matches_away = relationship(
        "Match", foreign_keys="Match.away_team_id", back_populates="away_team"
    )

    def __repr__(self):
        return f"<Team {self.name}>"


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    number = Column(Integer, nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50), nullable=False)
    role = Column(String(30))  # Libero, Opposto, Palleggiatore, ecc.
    is_libero = Column(Boolean, default=False)
    captain = Column(Boolean, default=False)
    birth_date = Column(DateTime)  # Data di nascita
    photo = Column(String(250))  # Path o URL foto

    team = relationship("Team", back_populates="players")
    events = relationship("ScoutEvent", back_populates="player")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __repr__(self):
        return f"<Player #{self.number} {self.last_name}>"


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    number = Column(Integer, nullable=False)
    role = Column(String(30))
    is_libero = Column(Boolean, default=False)
    is_starter = Column(Boolean, default=False)

    match = relationship("Match", back_populates="roster")
    player = relationship("Player")
    team = relationship("Team")

    def __repr__(self):
        return f"<MatchPlayer Match:{self.match_id} Player:{self.player_id} #{self.number}>"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    venue = Column(String(150))
    competition = Column(String(100))
    video_path = Column(String(500))  # path al file video
    video_offset = Column(Float, default=0.0)  # offset secondi tra orologio e video
    notes = Column(Text)
    status = Column(String(20), default="draft")  # draft, in_progress, completed
    game_method = Column(String(10), default="P-S-C")  # P-S-C o P-C-S
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    home_team = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="matches_home"
    )
    away_team = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="matches_away"
    )
    sets = relationship(
        "MatchSet",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchSet.set_number",
    )
    events = relationship(
        "ScoutEvent", back_populates="match", cascade="all, delete-orphan"
    )
    roster = relationship(
        "MatchPlayer", back_populates="match", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Match {self.home_team.name} vs {self.away_team.name} {self.date:%Y-%m-%d}>"


class MatchSet(Base):
    __tablename__ = "match_sets"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    set_number = Column(Integer, nullable=False)  # 1-5
    score_home = Column(Integer, default=0)
    score_away = Column(Integer, default=0)
    duration = Column(Integer)  # durata in secondi
    winner = Column(String(10))  # "home" | "away"

    match = relationship("Match", back_populates="sets")
    events = relationship("ScoutEvent", back_populates="match_set")

    def __repr__(self):
        return f"<Set {self.set_number}: {self.score_home}-{self.score_away}>"


class ScoutEvent(Base):
    """
    Evento di scouting - corrisponde a una riga del formato DataVolley .dvw
    """

    __tablename__ = "scout_events"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    set_id = Column(Integer, ForeignKey("match_sets.id"))
    player_id = Column(Integer, ForeignKey("players.id"))

    # DataVolley fields
    team_side = Column(String(1))  # "a" home | "b" away
    skill = Column(String(1))  # S R E A B D F
    evaluation = Column(String(1))  # # + ! - = /
    zone_start = Column(String(1))  # zona di partenza 1-9
    zone_end = Column(String(1))  # zona di arrivo 1-9
    attack_combo = Column(String(2))  # codice combinazione attacco
    set_code = Column(String(2))  # codice alzata
    special_code = Column(String(2))  # codice speciale

    # Score at moment of event
    score_home = Column(Integer, default=0)
    score_away = Column(Integer, default=0)

    # Video sync
    video_timestamp = Column(Float)  # secondi dall'inizio del video
    rally_number = Column(Integer)

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="events")
    match_set = relationship("MatchSet", back_populates="events")
    player = relationship("Player", back_populates="events")

    @property
    def datavolley_code(self):
        """Genera il codice DataVolley per questo evento"""
        p = self.player
        number = f"{p.number:02d}" if p else "00"
        skill = self.skill or "-"
        ev = self.evaluation or "-"
        zs = self.zone_start or "0"
        ze = self.zone_end or "0"
        return f"{number}{skill}{ev}{zs}{ze}"

    def __repr__(self):
        return f"<Event {self.datavolley_code} @{self.video_timestamp:.1f}s>"
