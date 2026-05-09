"""
Configurazioni di esempio per il TeamClassifier.

Questo file contiene profili pre-configurati per diversi tornei e scenari.
"""

from src.volley_analizer.core.team_classifier import TeamColorProfile


class TeamProfilesConfiguration:
    """Configurazioni predefinite per diversi scenari di torneo."""

    # Profilo di default: Rosso, Giallo, Nero (arbitro)
    DEFAULT = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(0, 0, 255)],
            hue_ranges=[(170, 180), (0, 10)],
            confidence_threshold=0.5,
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(0, 255, 255)],
            hue_ranges=[(20, 40)],
            confidence_threshold=0.5,
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(0, 0, 0)],
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
    }

    # Profilo A: Blu e Bianco
    BLUE_WHITE = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(200, 100, 0)],  # Blu scuro
            hue_ranges=[(100, 140)],
            confidence_threshold=0.5,
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(255, 255, 255)],  # Bianco
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(0, 0, 0)],
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
    }

    # Profilo B: Verde e Blu
    GREEN_BLUE = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(0, 128, 0)],  # Verde scuro
            hue_ranges=[(40, 80)],
            confidence_threshold=0.5,
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(255, 0, 0)],  # Blu (BGR)
            hue_ranges=[(100, 140)],
            confidence_threshold=0.5,
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(200, 200, 200)],  # Grigio
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
    }

    # Profilo C: Nero e Arancione
    BLACK_ORANGE = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(0, 0, 0)],  # Nero
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(0, 165, 255)],  # Arancione (BGR)
            hue_ranges=[(10, 25)],
            confidence_threshold=0.5,
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(200, 200, 200)],  # Grigio
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
    }

    # Profilo D: Rosso Scuro e Bianco
    DARK_RED_WHITE = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(0, 0, 139)],  # Rosso scuro
            hue_ranges=[(170, 180), (0, 5)],
            confidence_threshold=0.5,
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(255, 255, 255)],  # Bianco
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(0, 0, 0)],  # Nero
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
    }

    # Profilo E: Giallo e Rosso (per tornei specifici)
    YELLOW_RED = {
        "home": TeamColorProfile(
            team_id="home",
            expected_colors=[(0, 255, 255)],  # Giallo
            hue_ranges=[(20, 40)],
            confidence_threshold=0.5,
        ),
        "away": TeamColorProfile(
            team_id="away",
            expected_colors=[(0, 0, 255)],  # Rosso
            hue_ranges=[(170, 180), (0, 10)],
            confidence_threshold=0.5,
        ),
        "referee": TeamColorProfile(
            team_id="referee",
            expected_colors=[(200, 200, 200)],  # Grigio
            hue_ranges=None,
            confidence_threshold=0.5,
        ),
    }

    @classmethod
    def get_profile(cls, name: str) -> dict | None:
        """
        Ottiene un profilo per nome.

        Args:
            name: Nome del profilo ('DEFAULT', 'BLUE_WHITE', etc.)

        Returns:
            Dictionary con profili o None se non trovato.
        """
        profiles = {
            "DEFAULT": cls.DEFAULT,
            "BLUE_WHITE": cls.BLUE_WHITE,
            "GREEN_BLUE": cls.GREEN_BLUE,
            "BLACK_ORANGE": cls.BLACK_ORANGE,
            "DARK_RED_WHITE": cls.DARK_RED_WHITE,
            "YELLOW_RED": cls.YELLOW_RED,
        }
        return profiles.get(name.upper())

    @classmethod
    def list_profiles(cls) -> list[str]:
        """
        Lista tutti i profili disponibili.

        Returns:
            Lista dei nomi dei profili disponibili.
        """
        return [
            "DEFAULT",
            "BLUE_WHITE",
            "GREEN_BLUE",
            "BLACK_ORANGE",
            "DARK_RED_WHITE",
            "YELLOW_RED",
        ]


# Parametri di configurazione avanzata
class ClassifierConfiguration:
    """Parametri di configurazione per il classificatore."""

    # Configurazione conservativa (alta precisione, bassa recall)
    CONSERVATIVE = {
        "history_size": 10,
        "n_clusters": 5,
        "confidence_threshold": 0.7,
    }

    # Configurazione bilanciata (default)
    BALANCED = {
        "history_size": 5,
        "n_clusters": 3,
        "confidence_threshold": 0.5,
    }

    # Configurazione aggressiva (alta recall, bassa precisione)
    AGGRESSIVE = {
        "history_size": 3,
        "n_clusters": 2,
        "confidence_threshold": 0.3,
    }

    # Configurazione veloce per tempo reale
    REALTIME = {
        "history_size": 2,
        "n_clusters": 2,
        "confidence_threshold": 0.4,
    }

    @classmethod
    def get_config(cls, name: str) -> dict | None:
        """Ottiene una configurazione per nome."""
        configs = {
            "CONSERVATIVE": cls.CONSERVATIVE,
            "BALANCED": cls.BALANCED,
            "AGGRESSIVE": cls.AGGRESSIVE,
            "REALTIME": cls.REALTIME,
        }
        return configs.get(name.upper())


# Pesi per la combinazione di score (personalizzabili)
class ScoreWeights:
    """Pesi per la combinazione dei diversi metodi di analisi."""

    # Default: bilanciato
    DEFAULT = (0.4, 0.3, 0.3)  # (hsv_weight, moments_weight, kmeans_weight)

    # HSV-focused: per colori molto saturi
    HSV_FOCUSED = (0.6, 0.2, 0.2)

    # Balanced moment-based: per illuminazione variabile
    MOMENTS_FOCUSED = (0.2, 0.6, 0.2)

    # Clustering-focused: per pattern complessi
    CLUSTERING_FOCUSED = (0.2, 0.2, 0.6)

    # Equally weighted
    EQUAL = (0.333, 0.333, 0.334)

    @classmethod
    def get_weights(cls, name: str) -> tuple | None:
        """Ottiene i pesi per nome."""
        weights_dict = {
            "DEFAULT": cls.DEFAULT,
            "HSV_FOCUSED": cls.HSV_FOCUSED,
            "MOMENTS_FOCUSED": cls.MOMENTS_FOCUSED,
            "CLUSTERING_FOCUSED": cls.CLUSTERING_FOCUSED,
            "EQUAL": cls.EQUAL,
        }
        return weights_dict.get(name.upper())


if __name__ == "__main__":
    # Esempio di utilizzo
    print("Profili disponibili:")
    for profile_name in TeamProfilesConfiguration.list_profiles():
        print(f"  - {profile_name}")

    print("\nConfigurazione di esempio (DEFAULT):")
    from src.volley_analizer.core.team_classifier import TeamClassifier

    classifier = TeamClassifier(
        team_profiles=TeamProfilesConfiguration.DEFAULT,
        **ClassifierConfiguration.BALANCED,
    )

    print(f"  - team_profiles: {list(classifier.team_profiles.keys())}")
    print(f"  - history_size: {classifier.history_size}")
    print(f"  - n_clusters: {classifier.n_clusters}")
    print(f"  - confidence_threshold: {classifier.confidence_threshold}")
