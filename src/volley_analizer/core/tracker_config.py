"""
Configuration profiles for AdvancedMultiObjectTracker.

This module provides pre-configured tracker profiles optimized for different scenarios.
"""

from dataclasses import dataclass


@dataclass
class TrackerConfig:
    """Configuration for AdvancedMultiObjectTracker."""

    fps: int = 25
    max_missed_frames: int = 30
    max_age: int = 100
    distance_threshold: float = 100.0
    iou_threshold: float = 0.3
    velocity_weight: float = 0.3
    use_kalman: bool = True
    use_hungarian: bool = True
    kalman_process_var: float = 0.1
    kalman_measurement_var: float = 1.0


# Profile for volleyball tracking
VOLLEYBALL_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=15,  # ~0.5 seconds at 30fps
    max_age=300,  # ~10 seconds
    distance_threshold=150.0,  # Larger threshold for field movement
    iou_threshold=0.2,  # Lower IoU for small player boxes
    velocity_weight=0.4,  # Higher weight for velocity matching
    use_kalman=True,
    use_hungarian=True,
    kalman_process_var=0.15,  # Moderate process noise
    kalman_measurement_var=2.0,  # Higher measurement noise (detection imprecision)
)

# Profile for crowded scenes (many objects)
CROWDED_SCENE_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=10,
    max_age=100,
    distance_threshold=75.0,  # Stricter distance matching
    iou_threshold=0.4,  # Stricter IoU matching
    velocity_weight=0.5,  # Higher velocity weight (more predictive)
    use_kalman=True,
    use_hungarian=True,  # Hungarian is better for many objects
    kalman_process_var=0.05,  # Low process noise (predictable movement)
    kalman_measurement_var=1.0,  # Normal measurement noise
)

# Profile for high FPS video (slow motion, 60+ fps)
HIGH_FPS_PROFILE = TrackerConfig(
    fps=60,
    max_missed_frames=20,
    max_age=200,
    distance_threshold=80.0,  # Smaller distances between frames
    iou_threshold=0.35,
    velocity_weight=0.35,
    use_kalman=True,
    use_hungarian=True,
    kalman_process_var=0.08,
    kalman_measurement_var=0.8,  # Better detection at high fps
)

# Profile for low FPS video (e.g., 15 fps, surveillance)
LOW_FPS_PROFILE = TrackerConfig(
    fps=15,
    max_missed_frames=8,  # Shorter duration for missing frames
    max_age=80,
    distance_threshold=150.0,  # Larger jumps between frames
    iou_threshold=0.25,
    velocity_weight=0.3,
    use_kalman=True,
    use_hungarian=True,
    kalman_process_var=0.2,  # Higher process noise (more movement between frames)
    kalman_measurement_var=2.5,  # Higher measurement variance
)

# Profile for fast motion (sports, high speed)
FAST_MOTION_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=20,  # More tolerance for fast motion blur
    max_age=150,
    distance_threshold=200.0,  # Larger distances for fast objects
    iou_threshold=0.2,
    velocity_weight=0.5,  # Very high velocity weight
    use_kalman=True,
    use_hungarian=True,
    kalman_process_var=0.2,  # High process noise (unpredictable acceleration)
    kalman_measurement_var=2.0,
)

# Profile for slow motion (e.g., posture analysis)
SLOW_MOTION_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=10,
    max_age=100,
    distance_threshold=80.0,  # Tighter matching
    iou_threshold=0.4,
    velocity_weight=0.2,  # Lower velocity weight
    use_kalman=True,
    use_hungarian=True,
    kalman_process_var=0.05,  # Low process noise (predictable movement)
    kalman_measurement_var=1.0,
)

# Profile for real-time tracking (low latency)
REALTIME_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=15,
    max_age=100,
    distance_threshold=120.0,
    iou_threshold=0.3,
    velocity_weight=0.3,
    use_kalman=True,
    use_hungarian=False,  # Greedy is faster
    kalman_process_var=0.1,
    kalman_measurement_var=1.0,
)

# Profile for high precision (offline processing)
HIGH_PRECISION_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=30,
    max_age=300,
    distance_threshold=90.0,  # Conservative threshold
    iou_threshold=0.35,
    velocity_weight=0.35,
    use_kalman=True,
    use_hungarian=True,  # Hungarian for optimal assignment
    kalman_process_var=0.08,
    kalman_measurement_var=1.2,
)

# Profile for debugging
DEBUG_PROFILE = TrackerConfig(
    fps=30,
    max_missed_frames=5,
    max_age=50,
    distance_threshold=100.0,
    iou_threshold=0.3,
    velocity_weight=0.3,
    use_kalman=False,  # Easier to debug without Kalman
    use_hungarian=False,  # Greedy for simplicity
    kalman_process_var=0.1,
    kalman_measurement_var=1.0,
)


# Registry of profiles
PROFILES = {
    "volleyball": VOLLEYBALL_PROFILE,
    "crowded_scene": CROWDED_SCENE_PROFILE,
    "high_fps": HIGH_FPS_PROFILE,
    "low_fps": LOW_FPS_PROFILE,
    "fast_motion": FAST_MOTION_PROFILE,
    "slow_motion": SLOW_MOTION_PROFILE,
    "realtime": REALTIME_PROFILE,
    "high_precision": HIGH_PRECISION_PROFILE,
    "debug": DEBUG_PROFILE,
}


def get_profile(name: str) -> TrackerConfig:
    """Get a tracker configuration profile by name.

    Args:
        name: Profile name (see PROFILES keys)

    Returns:
        TrackerConfig instance

    Raises:
        ValueError: If profile name not found
    """
    if name not in PROFILES:
        available = ", ".join(sorted(PROFILES.keys()))
        raise ValueError(f"Unknown profile '{name}'. Available: {available}")

    # Return a copy to avoid modifications
    config = PROFILES[name]
    return TrackerConfig(
        fps=config.fps,
        max_missed_frames=config.max_missed_frames,
        max_age=config.max_age,
        distance_threshold=config.distance_threshold,
        iou_threshold=config.iou_threshold,
        velocity_weight=config.velocity_weight,
        use_kalman=config.use_kalman,
        use_hungarian=config.use_hungarian,
        kalman_process_var=config.kalman_process_var,
        kalman_measurement_var=config.kalman_measurement_var,
    )


def list_profiles() -> list[str]:
    """List all available profile names.

    Returns:
        Sorted list of profile names
    """
    return sorted(PROFILES.keys())


def print_profiles():
    """Print all profiles with descriptions."""
    descriptions = {
        "volleyball": "Optimized for volleyball tracking (typical 30fps, field-scale)",
        "crowded_scene": "For scenes with many objects (stricter matching)",
        "high_fps": "For high FPS video (60+fps, slow motion)",
        "low_fps": "For low FPS video (15fps or less, surveillance)",
        "fast_motion": "For fast moving objects (sports, high speed)",
        "slow_motion": "For slow, predictable motion (posture analysis)",
        "realtime": "For low-latency real-time tracking (uses greedy Hungarian)",
        "high_precision": "For offline processing with high precision",
        "debug": "For debugging (no Kalman, no Hungarian)",
    }

    print("\nAvailable Tracker Configuration Profiles:")
    print("=" * 70)

    for name in list_profiles():
        config = PROFILES[name]
        desc = descriptions.get(name, "")
        print(f"\n{name.upper()}")
        print(f"  Description: {desc}")
        print(f"  FPS: {config.fps}")
        print(f"  Max missed frames: {config.max_missed_frames}")
        print(f"  Distance threshold: {config.distance_threshold}")
        print(f"  IoU threshold: {config.iou_threshold}")
        print(f"  Velocity weight: {config.velocity_weight}")
        print(f"  Kalman: {'Yes' if config.use_kalman else 'No'}")
        print(f"  Hungarian: {'Yes' if config.use_hungarian else 'No'}")
