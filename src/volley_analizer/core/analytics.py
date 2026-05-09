from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from .types import Track


@dataclass(slots=True)
class TrackSample:
    frame_idx: int
    timestamp: float
    track_id: int
    team_id: str | None
    jersey_number: str | None
    x_m: float
    y_m: float
    zone: int


class AnalyticsEngine:
    def __init__(self) -> None:
        self.samples: list[TrackSample] = []

    def update(self, frame_idx: int, timestamp: float, track: Track) -> None:
        if track.field_position is None or track.zone is None:
            return

        self.samples.append(
            TrackSample(
                frame_idx=frame_idx,
                timestamp=timestamp,
                track_id=track.track_id,
                team_id=track.team_id,
                jersey_number=track.jersey_number,
                x_m=track.field_position[0],
                y_m=track.field_position[1],
                zone=track.zone,
            )
        )

    def export(self, output_dir: str | Path) -> dict[str, Path]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        tracks_csv = output_path / "tracks.csv"
        summary_csv = output_path / "summary.csv"
        summary_json = output_path / "summary.json"

        records = [asdict(sample) for sample in self.samples]
        self._write_tracks_csv(tracks_csv, records)
        summary_rows, payload = self._build_summary(records)
        self._write_summary_csv(summary_csv, summary_rows)
        summary_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        return {
            "tracks_csv": tracks_csv,
            "summary_csv": summary_csv,
            "summary_json": summary_json,
        }

    def _write_tracks_csv(self, path: Path, records: list[dict]) -> None:
        fieldnames = [
            "frame_idx",
            "timestamp",
            "track_id",
            "team_id",
            "jersey_number",
            "x_m",
            "y_m",
            "zone",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def _write_summary_csv(self, path: Path, rows: list[dict]) -> None:
        fieldnames = [
            "track_id",
            "team_id",
            "jersey_number",
            "samples",
            "dominant_zone",
            "zone_distribution",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _build_summary(self, records: list[dict]) -> tuple[list[dict], dict]:
        if pd is not None:
            return self._build_summary_with_pandas(records)
        return self._build_summary_without_pandas(records)

    def _build_summary_with_pandas(
        self, records: list[dict]
    ) -> tuple[list[dict], dict]:
        df = pd.DataFrame(records)
        if df.empty:
            return [], {"players": [], "rotations_hint": []}

        rows = []
        players = []
        for track_id, group in df.groupby("track_id"):
            zone_counts = Counter(group["zone"].tolist())
            total = len(group)
            team_id = (
                group["team_id"].mode().iloc[0]
                if not group["team_id"].dropna().empty
                else "unknown"
            )
            jersey_number = (
                group["jersey_number"].mode().iloc[0]
                if "jersey_number" in group
                and not group["jersey_number"].dropna().empty
                else "unknown"
            )
            distribution = {
                str(zone): round(count / total * 100.0, 2)
                for zone, count in sorted(zone_counts.items())
            }
            rows.append(
                {
                    "track_id": int(track_id),
                    "team_id": team_id,
                    "jersey_number": jersey_number,
                    "samples": total,
                    "dominant_zone": zone_counts.most_common(1)[0][0],
                    "zone_distribution": json.dumps(distribution, ensure_ascii=False),
                }
            )
            players.append(
                {
                    "track_id": int(track_id),
                    "team_id": team_id,
                    "jersey_number": jersey_number,
                    "samples": total,
                    "zone_percentages": distribution,
                    "dominant_zone": zone_counts.most_common(1)[0][0],
                }
            )

        payload = {"players": players, "rotations_hint": self._infer_rotations(records)}
        rows.sort(key=lambda item: item["track_id"])
        return rows, payload

    def _build_summary_without_pandas(
        self, records: list[dict]
    ) -> tuple[list[dict], dict]:
        grouped: defaultdict[int, list[dict]] = defaultdict(list)
        for record in records:
            grouped[int(record["track_id"])].append(record)

        rows = []
        players = []
        for track_id, group in sorted(grouped.items()):
            zone_counts = Counter(int(item["zone"]) for item in group)
            team_counts = Counter((item["team_id"] or "unknown") for item in group)
            total = len(group)
            distribution = {
                str(zone): round(count / total * 100.0, 2)
                for zone, count in sorted(zone_counts.items())
            }
            team_id = team_counts.most_common(1)[0][0]
            jersey_counts = Counter(
                (item.get("jersey_number") or "unknown") for item in group
            )
            jersey_number = jersey_counts.most_common(1)[0][0]
            dominant_zone = zone_counts.most_common(1)[0][0]
            rows.append(
                {
                    "track_id": track_id,
                    "team_id": team_id,
                    "jersey_number": jersey_number,
                    "samples": total,
                    "dominant_zone": dominant_zone,
                    "zone_distribution": json.dumps(distribution, ensure_ascii=False),
                }
            )
            players.append(
                {
                    "track_id": track_id,
                    "team_id": team_id,
                    "jersey_number": jersey_number,
                    "samples": total,
                    "zone_percentages": distribution,
                    "dominant_zone": dominant_zone,
                }
            )

        return rows, {
            "players": players,
            "rotations_hint": self._infer_rotations(records),
        }

    def _infer_rotations(self, records: list[dict]) -> list[dict[str, object]]:
        if not records:
            return []

        rotation_events: list[dict[str, object]] = []
        per_track_previous_zone: dict[int, int] = {}
        transitions: defaultdict[int, int] = defaultdict(int)

        for row in sorted(records, key=lambda item: item["timestamp"]):
            track_id = int(row["track_id"])
            zone = int(row["zone"])
            previous = per_track_previous_zone.get(track_id)
            if previous is not None and previous != zone:
                transitions[track_id] += 1
                if transitions[track_id] <= 5:
                    rotation_events.append(
                        {
                            "track_id": track_id,
                            "timestamp": round(float(row["timestamp"]), 2),
                            "from_zone": previous,
                            "to_zone": zone,
                        }
                    )
            per_track_previous_zone[track_id] = zone

        return rotation_events

    def get_zone_time_density(self) -> dict[int, float]:
        """Calcola il tempo totale speso in ogni zona (in secondi)."""
        from collections import defaultdict

        zone_times: defaultdict[int, float] = defaultdict(float)
        sorted_samples = sorted(self.samples, key=lambda s: s.timestamp)
        per_track_last: dict[int, TrackSample] = {}
        for sample in sorted_samples:
            last = per_track_last.get(sample.track_id)
            if last is not None:
                time_diff = sample.timestamp - last.timestamp
                zone_times[last.zone] += time_diff
            per_track_last[sample.track_id] = sample
        return dict(zone_times)
