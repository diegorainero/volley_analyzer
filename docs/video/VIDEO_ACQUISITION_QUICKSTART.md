# Video Acquisition System - Quick Start

## Installation

Il sistema è già integrato nel progetto volley_analizer. Non sono necessari pacchetti aggiuntivi oltre a quelli già presenti.

**Requisiti opzionali per GPU acceleration:**
```bash
# NVIDIA CUDA Toolkit (per NVDEC)
# FFmpeg con supporto NVDEC compilato
sudo apt-get install ffmpeg

# Verificare NVDEC support
ffmpeg -decoders | grep nvdec
```

## 5-Minute Examples

### 1. Leggere da File Locale

```python
from volley_analizer.core import create_video_source

# Crea sorgente
source = create_video_source("video.mp4", use_gpu=True)

# Leggi frame
frame_count = 0
while True:
    ret, frame = source.read_frame()
    if not ret:
        break
    
    # Processa frame
    print(f"Frame {frame_count}: {frame.shape}")
    frame_count += 1

source.close()
print(f"Totale frame: {frame_count}")
```

### 2. Leggere da Streaming RTSP

```python
from volley_analizer.core import create_video_source

# Camera IP (es. Hikvision, Dahua, Reolink)
source = create_video_source(
    "rtsp://admin:password@192.168.1.100:554/stream",
    buffer_size=20
)

# Leggi 100 frame
for i in range(100):
    ret, frame = source.read_frame()
    if not ret:
        break
    print(f"Frame {i}: {frame.shape}")

source.close()
```

### 3. Leggere da Webcam

```python
from volley_analizer.core import create_video_source

# Webcam device 0
source = create_video_source("0")

# Leggi 30 frame
for i in range(30):
    ret, frame = source.read_frame()
    if not ret:
        break
    print(f"Webcam frame {i}: {frame.shape}")

source.close()
```

### 4. Con VideoProcessor (Integrazione Completa)

```python
from volley_analizer.core import VideoProcessor

# File locale con GPU
processor = VideoProcessor(
    "video.mp4",
    sample_every_n_frames=3,
    use_gpu=True,
    buffer_size=30,
    target_resolution=(640, 480)  # Opzionale: scala risoluzione
)

# Leggi frame
for frame_idx, timestamp, frame in processor.frames():
    print(f"Frame {frame_idx} @{timestamp:.2f}s: {frame.shape}")

# Informazioni sorgente
info = processor.get_source_info()
print(f"\nSource Info:")
print(f"  Type: {info['type']}")
print(f"  Resolution: {info['width']}x{info['height']}")
print(f"  FPS: {info['fps']}")
print(f"  Codec: {info.get('codec', 'N/A')}")
print(f"  Frames read: {info['frames_read']}")
print(f"  Errors: {info['errors']}")

processor.release()
```

### 5. Controllo Hardware Decoder

```python
from volley_analizer.core import get_hardware_decoder, Codec

decoder = get_hardware_decoder()

# Best decoder disponibile
best = decoder.get_best_decoder()
print(f"Best decoder: {best.value}")

# Capabilities
caps = decoder.get_capabilities()
for decoder_type, capability in caps.items():
    print(f"\n{decoder_type.value}:")
    print(f"  Available: {capability.is_available}")
    if capability.is_available:
        print(f"  Codecs: {[c.value for c in capability.supported_codecs]}")
        print(f"  Max res: {capability.max_resolution}")
        print(f"  GPU Memory: {capability.memory_mb}MB")

# Per codec specifico
h264_decoder = decoder.get_decoder_for_codec(Codec.H264)
print(f"\nH.264 decoder: {h264_decoder.value if h264_decoder else 'N/A'}")
```

### 6. Frame Buffer (Thread-Safe)

```python
from volley_analizer.core import FrameBuffer, create_video_source
import threading
import time
import numpy as np

# Crea buffer
buffer = FrameBuffer(max_size=30)

# Producer thread
def producer():
    source = create_video_source("video.mp4")
    while True:
        ret, frame = source.read_frame()
        if not ret:
            break
        buffer.put(frame, frame_index=buffer.size(), block=False)
    source.close()

# Consumer thread
def consumer():
    for _ in range(100):
        result = buffer.get(block=False, timeout=1.0)
        if result:
            frame, idx, ts = result
            print(f"Consumed frame {idx}")
        time.sleep(0.05)

# Run threads
prod = threading.Thread(target=producer)
cons = threading.Thread(target=consumer)

prod.start()
cons.start()

prod.join(timeout=10)
cons.join(timeout=10)

# Metriche
metrics = buffer.get_metrics()
print(f"\nBuffer Metrics:")
print(f"  Frames: {metrics.frames_added} added, {metrics.frames_removed} removed")
print(f"  Dropped: {metrics.frames_dropped}")
print(f"  FPS: {metrics.fps:.1f}")
print(f"  Usage: {metrics.buffer_usage_percent:.1f}%")
```

### 7. Adaptive Buffer

```python
from volley_analizer.core import AdaptiveBuffer
import numpy as np

# Buffer che auto-adjusts based on performance
buffer = AdaptiveBuffer(
    initial_size=30,
    min_size=5,
    max_size=100,
    adjust_interval_seconds=5.0
)

# Simula frames
for i in range(300):
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    buffer.put(frame, frame_index=i)
    
    # Simula consumer con delay variabile
    if i % 10 == 0:
        result = buffer.get(block=False)

metrics = buffer.get_buffer().get_metrics()
print(f"Final buffer size: {buffer.get_buffer().max_size}")
print(f"Metrics: {metrics}")
```

## Auto-Detection Examples

Il sistema rileva automaticamente il tipo di sorgente:

```python
from volley_analizer.core import create_video_source, VideoSourceFactory, SourceType

# File locale - LocalFileSource
source = create_video_source("/path/to/video.mp4")

# RTSP - StreamingSource
source = create_video_source("rtsp://camera.local/stream")

# RTMP - StreamingSource
source = create_video_source("rtmp://server/live")

# HLS - StreamingSource
source = create_video_source("https://example.com/stream.m3u8")

# Webcam - WebcamSource
source = create_video_source("0")

# IP Camera - StreamingSource
source = create_video_source("192.168.1.100:554/stream")

# Verifica tipo rilevato
factory = VideoSourceFactory()
source = factory.create("video.mp4")
print(f"Detected: {source.metadata.source_type.value}")
```

## Configuration Examples

### Per Live Streaming con Bassa Latency

```python
from volley_analizer.core import VideoSourceConfig, create_video_source

config = VideoSourceConfig(
    buffer_size=5,              # Piccolo buffer
    timeout_seconds=5,          # Timeout basso
    read_timeout_ms=1000,       # Read timeout basso
    max_connection_retries=5,
    retry_delay_seconds=1,
)

source = create_video_source("rtsp://camera/stream", use_gpu=True)
```

### Per Streaming Affidabile (Alta Reliability)

```python
from volley_analizer.core import VideoSourceConfig, create_video_source

config = VideoSourceConfig(
    buffer_size=60,             # Buffer grande
    timeout_seconds=20,         # Timeout alto
    read_timeout_ms=5000,       # Read timeout alto
    max_connection_retries=10,
    retry_delay_seconds=3,
)

source = create_video_source("rtsp://camera/stream", use_gpu=True)
```

### Per Analisi Video su File (Performance)

```python
from volley_analizer.core import VideoProcessor

processor = VideoProcessor(
    "video.mp4",
    sample_every_n_frames=3,     # Salta frames
    use_gpu=True,                 # GPU acceleration
    target_resolution=(640, 480), # Scala
    buffer_size=50
)
```

## Troubleshooting

### "Failed to open video source"

```python
# Verifica file esiste
from pathlib import Path
if not Path("video.mp4").exists():
    print("File not found!")

# Verifica formato supportato
# Supportati: MP4, MKV, AVI, FLV, MOV, WebM, etc.

# Usa VideoProcessor per fallback a cv2
from volley_analizer.core import VideoProcessor
processor = VideoProcessor("video.mp4")  # Fallback automatico
```

### "Connection timeout" per streaming

```python
from volley_analizer.core import VideoSourceConfig, create_video_source

# Aumenta timeout
config = VideoSourceConfig(
    timeout_seconds=30,
    read_timeout_ms=10000,
    max_connection_retries=5,
)

# Verifica URL è corretto
# Formato: rtsp://user:pass@host:port/path
```

### "NVIDIA NVDEC not available"

```python
# Verifica GPU
import subprocess
result = subprocess.run(["nvidia-smi"], capture_output=True)
print(result.stdout.decode())

# Verifica FFmpeg NVDEC support
result = subprocess.run(["ffmpeg", "-decoders"], capture_output=True, text=True)
if "h264_nvdec" in result.stdout:
    print("FFmpeg NVDEC is available")
else:
    print("FFmpeg NVDEC not found - compile FFmpeg with NVDEC support")

# Fallback a CPU è automatico
source = create_video_source("video.mp4", use_gpu=False)
```

### "Buffer drops" (Frames persi)

```python
from volley_analizer.core import create_video_source, VideoSourceConfig

# Aumenta buffer
config = VideoSourceConfig(buffer_size=100)

# Leggi source info
source = create_video_source("video.mp4")
info = source.get_source_info()
print(f"Frames read: {info['frames_read']}")
print(f"Errors: {info['errors']}")

# Usa adaptive buffer
from volley_analizer.core import AdaptiveBuffer
buffer = AdaptiveBuffer(initial_size=30, max_size=200)
```

## Performance Benchmarks

Tipici throughput:

| Source | Resolution | Decoder | FPS |
|--------|-----------|---------|-----|
| Local File (H.264) | 1080p | NVDEC | ~300 |
| Local File (H.264) | 1080p | Software | ~60 |
| RTSP Stream | 1080p | NVDEC | ~200 |
| Webcam USB | 720p | Software | ~30 |

## Next Steps

- Leggi [VIDEO_ACQUISITION_SYSTEM.md](VIDEO_ACQUISITION_SYSTEM.md) per documentazione completa
- Vedi [test_video_acquisition.py](../tests/test_video_acquisition.py) per più esempi
- Consulta [hardware_decoder.py](../src/volley_analizer/core/hardware_decoder.py) per API completa
