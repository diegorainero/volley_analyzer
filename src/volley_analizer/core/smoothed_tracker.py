from __future__ import annotations

from collections import defaultdict

import numpy as np


class SmoothedTracker:
    """Tracker AI con smoothing e filtraggio intelligente per tracciamento robusto."""

    def __init__(self, smoothing_window: int = 5, distance_threshold: float = 100.0):
        """
        Args:
            smoothing_window: Numero di frame per il smoothing (media mobile)
            distance_threshold: Distanza massima per associare track a detection
        """
        self.smoothing_window = smoothing_window
        self.distance_threshold = distance_threshold
        self.track_history: defaultdict[int, list] = defaultdict(list)

    def smooth_position(
        self, track_id: int, position: tuple[float, float]
    ) -> tuple[float, float]:
        """Applica smoothing alla posizione usando media mobile.

        Args:
            track_id: ID del track
            position: Posizione (x, y) non smussata

        Returns:
            Posizione smussata
        """
        self.track_history[track_id].append(position)

        # Mantieni solo gli ultimi N frame
        if len(self.track_history[track_id]) > self.smoothing_window:
            self.track_history[track_id].pop(0)

        # Media mobile
        history = self.track_history[track_id]
        x_smooth = sum(p[0] for p in history) / len(history)
        y_smooth = sum(p[1] for p in history) / len(history)

        return x_smooth, y_smooth

    def filter_outliers(
        self, tracks: list, field_width: float = 9.0, field_height: float = 9.0
    ) -> list:
        """Filtra tracciamenti anomali fuori dai confini del campo.

        Args:
            tracks: Lista di track
            field_width: Larghezza del campo in metri
            field_height: Altezza del campo in metri

        Returns:
            Lista di track filtrati
        """
        filtered = []
        for track in tracks:
            x, y = track.field_position
            # Se la posizione è dentro il campo (con margine), mantieni il track
            if -0.5 <= x <= field_width + 0.5 and -0.5 <= y <= field_height + 0.5:
                filtered.append(track)
        return filtered

    def detect_stationary_zones(self, track_id: int, threshold: float = 0.2) -> bool:
        """Rileva se un giocatore è statico o in movimento.

        Args:
            track_id: ID del track
            threshold: Distanza minima per considerare il movimento

        Returns:
            True se il giocatore è statico
        """
        history = self.track_history[track_id]
        if len(history) < 2:
            return False

        # Calcola la distanza totale percorsa
        total_distance = 0.0
        for i in range(1, len(history)):
            x1, y1 = history[i - 1]
            x2, y2 = history[i]
            dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            total_distance += dist

        avg_distance = total_distance / (len(history) - 1)
        return avg_distance < threshold

    def interpolate_missing_frames(
        self, track_id: int, max_gap_frames: int = 3
    ) -> list[tuple[float, float]]:
        """Interpola posizioni mancanti tra frame (es. occlusion temporanea).

        Args:
            track_id: ID del track
            max_gap_frames: Numero massimo di frame di gap da interpolare

        Returns:
            Lista di posizioni interpolate
        """
        history = self.track_history[track_id]
        if len(history) < 2:
            return history

        interpolated = [history[0]]
        for i in range(1, len(history)):
            # Potrebbe aggiungere logica di interpolazione qui
            interpolated.append(history[i])

        return interpolated

    def get_track_confidence(self, track_id: int, min_frames: int = 3) -> float:
        """Calcola un punteggio di confidenza per un track.

        Args:
            track_id: ID del track
            min_frames: Numero minimo di frame per alta confidenza

        Returns:
            Confidenza tra 0.0 e 1.0
        """
        history = self.track_history[track_id]

        # Più frame = più confidenza
        if len(history) < min_frames:
            return len(history) / min_frames

        # Verifica stabilità (bassa varianza = alta confidenza)
        if len(history) < 2:
            return 1.0

        positions = np.array(history)
        variance = np.var(positions, axis=0)
        stability = 1.0 / (1.0 + np.mean(variance))

        return min(1.0, stability)
