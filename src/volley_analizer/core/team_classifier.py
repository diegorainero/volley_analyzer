from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np
from scipy import stats
from sklearn.cluster import KMeans


@dataclass
class TeamColorProfile:
    """Profilo di colori per una squadra."""

    team_id: str
    expected_colors: list[tuple[int, int, int]]  # BGR
    hue_ranges: list[tuple[int, int]] | None = None  # (min_hue, max_hue)
    confidence_threshold: float = 0.5

    def __post_init__(self):
        """Calcola i range di hue dai colori attesi."""
        if self.hue_ranges is None and self.expected_colors:
            self.hue_ranges = []
            for bgr in self.expected_colors:
                # Converti BGR a HSV per ottenere il range di hue
                hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0][0]
                hue = int(hsv[0])
                # Aggiungi un margine di ±15 gradi (OpenCV: 0-180)
                min_hue = max(0, hue - 15)
                max_hue = min(180, hue + 15)
                self.hue_ranges.append((min_hue, max_hue))


class TeamClassifier:
    """Classificatore avanzato di squadre basato su analisi di colore.

    Combina più metodi di analisi del colore:
    - HSV histogram (hue + saturation + value)
    - BGR color moments (media, varianza)
    - K-means clustering per colori dominanti
    - Tracciamento storico di frame precedenti
    """

    DEFAULT_TEAM_PROFILES = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(0, 0, 255)],  # Rosso in BGR
            hue_ranges=[(170, 180), (0, 10)],  # Rosso ha range diviso
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(0, 255, 255)],  # Giallo in BGR
            hue_ranges=[(20, 40)],
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(0, 0, 0)],  # Nero in BGR
            hue_ranges=None,  # Verrà calcolato
        ),
    }

    def __init__(
        self,
        team_profiles: dict[str, TeamColorProfile] | None = None,
        history_size: int = 5,
        n_clusters: int = 3,
        confidence_threshold: float = 0.5,
    ):
        """Inizializza il classificatore.

        Args:
            team_profiles: Dictionary con profili di colore per squadra.
                          Se None, usa i profili di default.
            history_size: Numero di frame precedenti da tracciare.
            n_clusters: Numero di cluster K-means per colori dominanti.
            confidence_threshold: Soglia minima di confidenza per classificazione.
        """
        self.team_profiles = team_profiles or self.DEFAULT_TEAM_PROFILES
        self.history_size = history_size
        self.n_clusters = n_clusters
        self.confidence_threshold = confidence_threshold

        # Deque per tracciare le classificazioni precedenti per track_id
        self.team_history: dict[int, deque[tuple[str, float]]] = {}

    def classify(
        self,
        crop: np.ndarray,
        track_id: int | None = None,
    ) -> tuple[str, float]:
        """Classifica il team dal crop di un giocatore.

        Args:
            crop: Immagine ritagliata del giocatore (BGR).
            track_id: ID del track per usare lo storico. Opzionale.

        Returns:
            Tuple (team_id, confidence) dove team_id è il team predetto
            e confidence è un score tra 0 e 1.
        """
        if crop.size == 0:
            return "unknown", 0.0

        # Estrai feature dal crop
        hsv_score = self._analyze_hsv_histogram(crop)
        moments_score = self._analyze_color_moments(crop)
        kmeans_score = self._analyze_dominant_colors(crop)

        # Combina i score
        combined_scores = self._combine_scores(hsv_score, moments_score, kmeans_score)

        # Seleziona il team migliore
        best_team = max(combined_scores, key=combined_scores.get)
        best_confidence = combined_scores[best_team]

        # Applica temporal smoothing se disponibile un track_id
        if track_id is not None:
            best_team, best_confidence = self._apply_temporal_smoothing(
                track_id, best_team, best_confidence
            )

        return best_team, best_confidence

    def _analyze_hsv_histogram(
        self,
        crop: np.ndarray,
        bins: int = 16,
    ) -> dict[str, float]:
        """Analizza l'istogramma HSV del crop.

        Returns:
            Dictionary con score per ogni team.
        """
        if crop.size == 0:
            return {team_id: 0.0 for team_id in self.team_profiles}

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h_channel = hsv[:, :, 0]
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]

        # Calcola istogrammi normalizzati
        h_hist = cv2.calcHist([h_channel], [0], None, [bins], [0, 180])
        s_hist = cv2.calcHist([s_channel], [0], None, [bins], [0, 256])
        v_hist = cv2.calcHist([v_channel], [0], None, [bins], [0, 256])

        h_hist = h_hist.flatten() / h_hist.sum()
        s_hist = s_hist.flatten() / s_hist.sum()
        v_hist = v_hist.flatten() / v_hist.sum()

        scores = {}
        for team_id, profile in self.team_profiles.items():
            if profile.hue_ranges is None:
                scores[team_id] = 0.0
                continue

            # Calcola la frazione di pixel nei range di hue attesi
            hue_match = 0.0
            for min_hue, max_hue in profile.hue_ranges:
                min_bin = int(min_hue * bins / 180)
                max_bin = int(max_hue * bins / 180)
                if max_bin > bins:
                    max_bin = bins
                hue_match += h_hist[min_bin:max_bin].sum()

            # Normalizza per il numero di range (nel caso di rosso che ha 2 range)
            hue_match /= len(profile.hue_ranges)

            # Combina con saturazione (color strength)
            saturation_score = (s_hist[s_hist > 0.01]).sum()

            # Score combinato
            scores[team_id] = hue_match * 0.7 + saturation_score * 0.3

        return scores

    def _analyze_color_moments(self, crop: np.ndarray) -> dict[str, float]:
        """Analizza i momenti dei colori (media e varianza) nel crop.

        Returns:
            Dictionary con score per ogni team.
        """
        if crop.size == 0:
            return {team_id: 0.0 for team_id in self.team_profiles}

        # Converti a LAB per una migliore rappresentazione perceptual
        lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)

        # Calcola media e varianza per ogni canale
        crop_flat = lab.reshape(-1, 3).astype(float)
        mean_color = crop_flat.mean(axis=0)
        std_color = crop_flat.std(axis=0)

        scores = {}
        for team_id, profile in self.team_profiles.items():
            # Calcola la distanza euclidea dal colore atteso
            min_distance = float("inf")
            for bgr in profile.expected_colors:
                expected_lab = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0][
                    0
                ].astype(float)
                distance = np.linalg.norm(mean_color - expected_lab)
                min_distance = min(min_distance, distance)

            # Converti distanza a score (più vicino = più alto)
            # Normalizza assumendo max distance di ~150
            scores[team_id] = max(0.0, 1.0 - (min_distance / 150.0))

        return scores

    def _analyze_dominant_colors(
        self,
        crop: np.ndarray,
        n_samples: int = 500,
    ) -> dict[str, float]:
        """Analizza i colori dominanti usando K-means clustering.

        Returns:
            Dictionary con score per ogni team.
        """
        if crop.size == 0:
            return {team_id: 0.0 for team_id in self.team_profiles}

        # Campiona pixel casuali per efficienza
        crop_flat = crop.reshape(-1, 3).astype(float)
        if len(crop_flat) > n_samples:
            indices = np.random.choice(len(crop_flat), n_samples, replace=False)
            crop_flat = crop_flat[indices]

        try:
            # K-means clustering
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            kmeans.fit(crop_flat)
            centers = kmeans.cluster_centers_
            labels = kmeans.labels_
        except Exception:
            # Fallback se K-means fallisce
            return {team_id: 0.0 for team_id in self.team_profiles}

        # Conta i pixel per cluster
        cluster_counts = np.bincount(labels)
        sorted_indices = np.argsort(-cluster_counts)

        scores = {}
        for team_id, profile in self.team_profiles.items():
            team_score = 0.0

            for bgr in profile.expected_colors:
                expected_lab = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0][
                    0
                ].astype(float)

                # Calcola la distanza dai colori dominanti
                distances = [
                    np.linalg.norm(centers[idx] - expected_lab)
                    for idx in sorted_indices[:2]  # Prendi i 2 colori più dominanti
                ]

                # Score basato sulla distanza minima
                min_distance = min(distances)
                color_score = max(0.0, 1.0 - (min_distance / 150.0))
                team_score = max(team_score, color_score)

            scores[team_id] = team_score

        return scores

    def _combine_scores(
        self,
        hsv_scores: dict[str, float],
        moments_scores: dict[str, float],
        kmeans_scores: dict[str, float],
        weights: tuple[float, float, float] | None = None,
    ) -> dict[str, float]:
        """Combina i score di diversi metodi.

        Args:
            hsv_scores: Score dall'analisi HSV.
            moments_scores: Score dall'analisi dei momenti.
            kmeans_scores: Score dall'analisi K-means.
            weights: Tuple (hsv_weight, moments_weight, kmeans_weight).
                    Default: (0.4, 0.3, 0.3)

        Returns:
            Dictionary con score combinato per ogni team.
        """
        if weights is None:
            weights = (0.4, 0.3, 0.3)

        combined = {}
        for team_id in self.team_profiles:
            combined[team_id] = (
                hsv_scores.get(team_id, 0.0) * weights[0]
                + moments_scores.get(team_id, 0.0) * weights[1]
                + kmeans_scores.get(team_id, 0.0) * weights[2]
            )

        # Normalizza i score
        max_score = max(combined.values()) if combined.values() else 1.0
        if max_score > 0:
            combined = {k: v / max_score for k, v in combined.items()}

        return combined

    def _apply_temporal_smoothing(
        self,
        track_id: int,
        team_id: str,
        confidence: float,
    ) -> tuple[str, float]:
        """Applica smoothing temporale usando lo storico dei frame.

        Args:
            track_id: ID del track.
            team_id: Team predetto nel frame corrente.
            confidence: Confidenza della predizione corrente.

        Returns:
            Tuple (smoothed_team_id, smoothed_confidence).
        """
        # Inizializza la deque per questo track se non esiste
        if track_id not in self.team_history:
            self.team_history[track_id] = deque(maxlen=self.history_size)

        # Aggiungi la predizione corrente
        self.team_history[track_id].append((team_id, confidence))

        # Applica median filtering sulle confidenze
        history = list(self.team_history[track_id])

        if len(history) == 0:
            return team_id, confidence

        # Estrai i team dalla storia e conta le occorrenze
        team_counts = {}
        confidence_sum = {}
        for hist_team, hist_conf in history:
            team_counts[hist_team] = team_counts.get(hist_team, 0) + 1
            confidence_sum[hist_team] = confidence_sum.get(hist_team, 0.0) + hist_conf

        # Seleziona il team più frequente
        smoothed_team = max(team_counts, key=team_counts.get)
        smoothed_confidence = confidence_sum[smoothed_team] / team_counts[smoothed_team]

        # Penalizza se c'è instabilità (molti team diversi)
        if len(team_counts) > 1:
            smoothed_confidence *= 0.8

        return smoothed_team, smoothed_confidence

    def clear_history(self, track_id: int | None = None) -> None:
        """Pulisce lo storico.

        Args:
            track_id: Se fornito, pulisce solo lo storico di questo track.
                     Se None, pulisce tutto lo storico.
        """
        if track_id is not None:
            self.team_history.pop(track_id, None)
        else:
            self.team_history.clear()

    def set_team_profiles(self, team_profiles: dict[str, TeamColorProfile]) -> None:
        """Imposta nuovi profili di colore per le squadre.

        Args:
            team_profiles: Dictionary con nuovi profili.
        """
        self.team_profiles = team_profiles

    def add_team_profile(self, profile: TeamColorProfile) -> None:
        """Aggiunge un nuovo profilo di team.

        Args:
            profile: Profilo da aggiungere.
        """
        self.team_profiles[profile.team_id] = profile
