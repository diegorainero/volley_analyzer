# Advanced Player Detection Configuration Examples

## Default Configuration (Balanced)
```python
from src.volley_analizer.core.detector import PlayerDetector

detector = PlayerDetector(
    model_name="yolov8n.pt",
    confidence_threshold=0.25,
    detector_type="yolo",
    # NMS Settings
    nms_threshold=0.45,
    soft_nms_enabled=True,
    soft_nms_method="linear",
    # Filtering Settings
    aspect_ratio_min=0.3,
    aspect_ratio_max=0.8,
    min_detection_area=500,
    max_detection_area=None,
    # Adaptive Settings
    adaptive_confidence=True
)
```

**Use Case:** General purpose volleyball detection in standard lighting conditions

---

## High-Precision Configuration (Conservative)
```python
detector = PlayerDetector(
    confidence_threshold=0.35,           # Higher threshold
    nms_threshold=0.35,                  # Stricter NMS
    soft_nms_enabled=True,
    soft_nms_method="linear",
    aspect_ratio_min=0.35,               # Narrower range
    aspect_ratio_max=0.75,
    min_detection_area=800,              # Larger minimum
    adaptive_confidence=False,           # Disable adaptive to be consistent
)
```

**Use Case:** Scenarios where false positives are critical to avoid (e.g., tactical analysis)

---

## High-Recall Configuration (Sensitive)
```python
detector = PlayerDetector(
    confidence_threshold=0.15,           # Lower threshold
    nms_threshold=0.5,                   # More lenient NMS
    soft_nms_enabled=True,
    soft_nms_method="gaussian",          # Gentle confidence reduction
    aspect_ratio_min=0.25,               # Wider range
    aspect_ratio_max=0.9,
    min_detection_area=300,              # Smaller minimum
    adaptive_confidence=True,            # Important for low-light
)
```

**Use Case:** Crowd scenes, low lighting, need to catch all players

---

## Performance-Optimized Configuration
```python
detector = PlayerDetector(
    confidence_threshold=0.30,
    nms_threshold=0.45,
    soft_nms_enabled=False,              # Hard NMS is faster
    soft_nms_method="hard",
    aspect_ratio_min=0.3,
    aspect_ratio_max=0.8,
    min_detection_area=500,
    adaptive_confidence=False,           # Skip brightness calculation
)
```

**Use Case:** Real-time processing on resource-constrained systems

---

## Low-Light Configuration
```python
detector = PlayerDetector(
    confidence_threshold=0.15,           # Very lenient
    nms_threshold=0.4,
    soft_nms_enabled=True,
    soft_nms_method="gaussian",
    aspect_ratio_min=0.3,
    aspect_ratio_max=0.85,
    min_detection_area=400,
    adaptive_confidence=True,            # CRITICAL - adapts to darkness
)
```

**Use Case:** Evening matches, indoor gym with poor lighting

---

## Crowd/Dense Configuration
```python
detector = PlayerDetector(
    confidence_threshold=0.28,
    nms_threshold=0.3,                   # Very aggressive NMS
    soft_nms_enabled=True,
    soft_nms_method="gaussian",          # Soft to preserve nearby players
    aspect_ratio_min=0.35,
    aspect_ratio_max=0.7,
    min_detection_area=700,
    adaptive_confidence=True,
)
```

**Use Case:** Packed sidelines, many spectators, bunched teams

---

## Dynamic/Adaptive Configuration
```python
# Start with default
detector = PlayerDetector()

# Adjust based on frame analysis
stats = detector.get_confidence_calibration()

if stats['std'] > 0.2:
    # High variance in detections - scene is complex
    detector.soft_nms_method = "gaussian"
    detector.nms_threshold = 0.35
    
if stats['mean'] < 0.4:
    # Low average confidence - difficult scene
    detector.confidence_threshold = 0.15
    detector.adaptive_confidence = True
```

**Use Case:** Live streaming with varying conditions

---

## Configuration Tuning Guide

### If you see too many false positives:
```python
detector.confidence_threshold = 0.35    # ↑ Increase
detector.min_detection_area = 800       # ↑ Increase
detector.aspect_ratio_min = 0.4         # ↑ Increase
detector.aspect_ratio_max = 0.7         # ↓ Decrease (narrow range)
detector.adaptive_confidence = False     # ✗ Disable
```

### If you're missing real players:
```python
detector.confidence_threshold = 0.15    # ↓ Decrease
detector.min_detection_area = 300       # ↓ Decrease
detector.aspect_ratio_min = 0.25        # ↓ Decrease (widen range)
detector.aspect_ratio_max = 0.9         # ↑ Increase (widen range)
detector.adaptive_confidence = True      # ✓ Enable
```

### If you see duplicate detections:
```python
detector.soft_nms_enabled = True        # ✓ Enable Soft-NMS
detector.nms_threshold = 0.3            # ↓ Lower threshold
detector.soft_nms_method = "gaussian"   # Use gentle method
```

### If detection is too slow:
```python
detector.soft_nms_enabled = False       # Use Hard NMS
detector.adaptive_confidence = False     # Skip brightness calc
detector.confidence_threshold = 0.35    # Higher = fewer to process
```

---

## Runtime Configuration

### Monitor and Adjust
```python
import time

detector = PlayerDetector()
frame_times = []

for frame in video_frames:
    start = time.time()
    detections = detector.detect(frame)
    frame_times.append(time.time() - start)
    
    # Check if too slow
    if sum(frame_times[-30:]) / 30 > 0.05:  # > 50ms average
        print("Too slow! Consider:")
        print("- Disabling adaptive_confidence")
        print("- Using hard_nms instead of soft")
        print("- Increasing confidence_threshold")
    
    # Check detection quality
    stats = detector.get_confidence_calibration()
    print(f"Avg confidence: {stats['mean']:.2f}")
```

### Per-Frame Adaptation
```python
def adaptive_detect(detector, frame):
    # Analyze frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray) / 255.0
    
    # Adapt threshold
    if brightness < 0.3:
        detector.confidence_threshold = 0.15
    elif brightness > 0.8:
        detector.confidence_threshold = 0.35
    else:
        detector.confidence_threshold = 0.25
    
    return detector.detect(frame)
```

---

## File: `config/detector_config.yaml`

```yaml
# Detector Configuration

# Model & Detection Type
model:
  name: "yolov8n.pt"
  type: "yolo"  # or "hog"
  confidence_threshold: 0.25

# Non-Maximum Suppression
nms:
  enabled: true
  threshold: 0.45
  soft_nms:
    enabled: true
    method: "linear"  # "linear", "gaussian", "hard"

# Filtering
filtering:
  aspect_ratio:
    min: 0.3
    max: 0.8
  size:
    min_area: 500
    max_area: null  # null = unlimited
  
# Adaptive Processing
adaptive:
  confidence: true
  merge_nearby: true
  merge_threshold: 0.5

# Calibration
calibration:
  history_size: 100
  log_statistics: true
```

---

## Quick Start Examples

### Example 1: Basic Usage
```python
from src.volley_analizer.core.detector import PlayerDetector
import cv2

detector = PlayerDetector()
video = cv2.VideoCapture("video.mp4")

while True:
    ret, frame = video.read()
    if not ret:
        break
    
    detections = detector.detect(frame)
    
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
    
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
```

### Example 2: With Calibration Monitoring
```python
detector = PlayerDetector(confidence_threshold=0.25)

for i, frame in enumerate(video_frames):
    detections = detector.detect(frame)
    
    if (i + 1) % 30 == 0:  # Every 30 frames
        stats = detector.get_confidence_calibration()
        print(f"Frame {i+1}: Avg confidence={stats['mean']:.2f}, "
              f"Detections count={stats['count']}")
```

### Example 3: Custom Configuration from Dict
```python
config = {
    'confidence_threshold': 0.30,
    'nms_threshold': 0.35,
    'soft_nms_enabled': True,
    'aspect_ratio_min': 0.35,
    'aspect_ratio_max': 0.75,
    'min_detection_area': 800,
}

detector = PlayerDetector(**config)
```

---

## Parameter Reference

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `confidence_threshold` | 0.25 | 0.0-1.0 | Base confidence threshold |
| `nms_threshold` | 0.45 | 0.0-1.0 | IoU threshold for NMS |
| `soft_nms_enabled` | True | - | Enable Soft-NMS |
| `soft_nms_method` | "linear" | "linear", "gaussian", "hard" | Soft-NMS method |
| `aspect_ratio_min` | 0.3 | 0.0-1.0 | Minimum height/width ratio |
| `aspect_ratio_max` | 0.8 | 0.0-2.0 | Maximum height/width ratio |
| `min_detection_area` | 500 | 0-∞ | Minimum box area (pixels²) |
| `max_detection_area` | None | 0-∞ | Maximum box area (None=unlimited) |
| `adaptive_confidence` | True | - | Enable adaptive thresholding |

