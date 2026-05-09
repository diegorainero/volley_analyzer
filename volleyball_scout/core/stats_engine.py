"""
Volleyball Scout - Statistics Engine
Calcola statistiche compatibili con DataVolley
"""

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Match, Player, ScoutEvent


@dataclass
class PlayerStats:
    player_id: int
    player_name: str
    number: int

    # Attacco
    attack_total: int = 0
    attack_perfect: int = 0  # punto diretto (#)
    attack_positive: int = 0  # +
    attack_negative: int = 0  # -
    attack_error: int = 0  # =

    # Battuta
    serve_total: int = 0
    serve_ace: int = 0  # #
    serve_positive: int = 0
    serve_error: int = 0

    # Ricezione
    reception_total: int = 0
    reception_perfect: int = 0
    reception_positive: int = 0
    reception_negative: int = 0
    reception_error: int = 0

    # Difesa
    dig_total: int = 0
    dig_positive: int = 0
    dig_error: int = 0

    # Muro
    block_total: int = 0
    block_point: int = 0
    block_error: int = 0

    @property
    def attack_efficiency(self) -> float:
        if self.attack_total == 0:
            return 0.0
        return (self.attack_perfect - self.attack_error) / self.attack_total

    @property
    def reception_efficiency(self) -> float:
        if self.reception_total == 0:
            return 0.0
        return (self.reception_perfect * 3 + self.reception_positive * 2) / (
            self.reception_total * 3
        )

    @property
    def serve_efficiency(self) -> float:
        if self.serve_total == 0:
            return 0.0
        return (self.serve_ace - self.serve_error) / self.serve_total

    def to_dict(self) -> dict:
        return {
            "name": self.player_name,
            "number": self.number,
            "attack": {
                "total": self.attack_total,
                "point": self.attack_perfect,
                "error": self.attack_error,
                "efficiency": round(self.attack_efficiency, 3),
            },
            "serve": {
                "total": self.serve_total,
                "ace": self.serve_ace,
                "error": self.serve_error,
                "efficiency": round(self.serve_efficiency, 3),
            },
            "reception": {
                "total": self.reception_total,
                "perfect": self.reception_perfect,
                "positive": self.reception_positive,
                "error": self.reception_error,
                "efficiency": round(self.reception_efficiency, 3),
            },
            "dig": {
                "total": self.dig_total,
                "positive": self.dig_positive,
                "error": self.dig_error,
            },
            "block": {
                "total": self.block_total,
                "point": self.block_point,
                "error": self.block_error,
            },
        }


@dataclass
class MatchStats:
    match_id: int
    home_team_name: str
    away_team_name: str
    players: dict[int, PlayerStats] = field(default_factory=dict)
    set_scores: list[tuple[int, int]] = field(default_factory=list)

    def get_team_stats(self, side: str) -> dict:
        """side = 'a' (home) o 'b' (away)"""
        team_players = [p for p in self.players.values()]
        # Filtra per side tramite gli eventi (semplificato: raggruppa per team)
        return {p.player_name: p.to_dict() for p in team_players}


class StatsEngine:
    def __init__(self, session: Session):
        self.session = session

    # ──────────────────────────────────
    #  Calcolo statistiche partita
    # ──────────────────────────────────

    def compute_match_stats(self, match_id: int) -> MatchStats:
        match = self.session.get(Match, match_id)
        if not match:
            raise ValueError(f"Match {match_id} non trovato")

        events = (
            self.session.query(ScoutEvent).filter(ScoutEvent.match_id == match_id).all()
        )

        stats = MatchStats(
            match_id=match_id,
            home_team_name=match.home_team.name,
            away_team_name=match.away_team.name,
        )

        for ev in events:
            if not ev.player_id:
                continue
            if ev.player_id not in stats.players:
                p = ev.player
                stats.players[ev.player_id] = PlayerStats(
                    player_id=p.id, player_name=p.full_name, number=p.number
                )
            ps = stats.players[ev.player_id]
            self._apply_event(ps, ev)

        return stats

    def _apply_event(self, ps: PlayerStats, ev: ScoutEvent):
        skill = ev.skill or ""
        evcode = ev.evaluation or ""

        if skill == "A":  # Attacco
            ps.attack_total += 1
            if evcode == "#":
                ps.attack_perfect += 1
            elif evcode == "+":
                ps.attack_positive += 1
            elif evcode == "-":
                ps.attack_negative += 1
            elif evcode == "=":
                ps.attack_error += 1

        elif skill == "S":  # Battuta
            ps.serve_total += 1
            if evcode == "#":
                ps.serve_ace += 1
            elif evcode == "+":
                ps.serve_positive += 1
            elif evcode == "=":
                ps.serve_error += 1

        elif skill == "R":  # Ricezione
            ps.reception_total += 1
            if evcode == "#":
                ps.reception_perfect += 1
            elif evcode == "+":
                ps.reception_positive += 1
            elif evcode == "-":
                ps.reception_negative += 1
            elif evcode == "=":
                ps.reception_error += 1

        elif skill == "D":  # Difesa / Dig
            ps.dig_total += 1
            if evcode in ("+", "#"):
                ps.dig_positive += 1
            elif evcode == "=":
                ps.dig_error += 1

        elif skill == "B":  # Muro
            ps.block_total += 1
            if evcode == "#":
                ps.block_point += 1
            elif evcode == "=":
                ps.block_error += 1

    # ──────────────────────────────────
    #  Top performers
    # ──────────────────────────────────

    def top_attackers(self, match_id: int, top_n: int = 5) -> list[PlayerStats]:
        ms = self.compute_match_stats(match_id)
        ranked = sorted(
            ms.players.values(), key=lambda p: (-p.attack_perfect, -p.attack_efficiency)
        )
        return ranked[:top_n]

    def top_servers(self, match_id: int, top_n: int = 5) -> list[PlayerStats]:
        ms = self.compute_match_stats(match_id)
        ranked = sorted(
            ms.players.values(), key=lambda p: (-p.serve_ace, -p.serve_efficiency)
        )
        return ranked[:top_n]

    # ──────────────────────────────────
    #  Riepilogo testuale (quick report)
    # ──────────────────────────────────

    def quick_report(self, match_id: int) -> str:
        ms = self.compute_match_stats(match_id)
        lines = [f"=== STATISTICHE: {ms.home_team_name} vs {ms.away_team_name} ===", ""]
        for pid, ps in sorted(ms.players.items(), key=lambda x: x[1].number):
            lines.append(f"#{ps.number} {ps.player_name}")
            lines.append(
                f"  Att: {ps.attack_total} tot | {ps.attack_perfect} pt | {ps.attack_error} err | eff {ps.attack_efficiency:.1%}"
            )
            lines.append(
                f"  Bat: {ps.serve_total} tot | {ps.serve_ace} ace | {ps.serve_error} err"
            )
            lines.append(
                f"  Ric: {ps.reception_total} tot | {ps.reception_perfect} perf | eff {ps.reception_efficiency:.1%}"
            )
            lines.append("")
        return "\n".join(lines)
