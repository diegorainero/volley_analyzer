# Video Acquisition System Documentation

## Overview

Il sistema di acquisizione video flessibile supporta molteplici fonti di input con accelerazione hardware NVIDIA NVDEC, buffering intelligente e gestione robusta degli errori.

### Features Principali

- **Supporto fonti multiple**: File locali, streaming (RTSP/RTMP/HLS), webcam
- **Accelerazione hardware**: NVIDIA NVDEC per decodifica GPU
- **Buffering intelligente**: Buffer circolare thread-safe con metriche in tempo reale
- **Auto-detection**: Rilevamento automatico del tipo di sorgente
- **Gestione errori**: Fallback automatico e riconnessione per streaming
- **Performance monitoring**: Metriche dettagliate di decodifica e buffering

## Architettura

```
┌─────────────────────────────────────────────────────────┐
│                    VideoSourceFactory                     │
│          (Auto-detect sorgente + instanzia)             │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    LocalFileSource StreamingSource WebcamSource
         │             │             │
         └─────────────┼─────────────┘
                       │
                       ▼
            VideoSourceMetadata
         (FPS, risoluzione, codec)
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    FrameBuffer  HardwareDecoder  VideoProcessor
    (Buffering) (GPU/CPU decode) (Integrazione)
```

## Moduli Principali

### 1. `video_source.py` (683 linee)

Sistema di astrazione per le fonti video.

#### Classi Principali

```python
# Configurazione
VideoSourceConfig
  - timeout_seconds: Timeout connessione
  - use_gpu: Abilita GPU acceleration
  - target_resolution: Risoluzione target
  - buffer_size: Dimensione buffer
  - skip_frames: Frame skipping

# Interfaccia astratta
VideoSource (ABC)
  - open(): Apri sorgente
  - read_frame(): Leggi frame
  - close(): Chiudi
  - seek(): Vai a frame (se supportato)

# Implementazioni concrete
LocalFileSource   # File MP4, MKV, AVI, etc.
StreamingSource   # RTSP, RTMP, HLS
WebcamSource      # Webcam USB/IP

# Factory
VideoSourceFactory.create(source, config) -> VideoSource
```

#### Uso Basico

```python
from volley_analizer.core import create_video_source

# File locale
source = create_video_source("video.mp4", use_gpu=True)

# Streaming RTSP
source = create_video_source("rtsp://camera.local:554/stream")

# Webcam
source = create_video_source("0")  # Device ID

# Con configurazione custom
from volley_analizer.core import VideoSourceConfig
config = VideoSourceConfig(
    buffer_size=50,
    target_resolution=(640, 480),
    timeout_seconds=15
)
source = create_video_source("rtsp://...", use_gpu=True)

# Lettura frame
while True:
    ret, frame = source.read_frame()
    if not ret:
        break
    # Processa frame...

source.close()
```

#### Tipo Sorgente Auto-Detection

| Input | Rilevato come |
|-------|--------------|
| `/path/to/video.mp4` | `LocalFileSource` |
| `rtsp://camera/stream` | `StreamingSource` (RTSP) |
| `rtmp://server/live` | `StreamingSource` (RTMP) |
| `https://example.com/video.m3u8` | `StreamingSource` (HLS) |
| `0`, `1`, `2` | `WebcamSource` |
| `192.168.1.100` | `StreamingSource` (IP camera) |

### 2. `hardware_decoder.py` (501 linee)

Gestione accelerazione hardware NVIDIA NVDEC.

#### Classi Principali

```python
# Enum codec
Codec
  - H264, H265, VP9, AV1, MPEG2

# Tipo decoder
DecoderType
  - NVIDIA_NVDEC
  - INTEL_QUICKSYNC (placeholder)
  - AMD_VCE (placeholder)
  - SOFTWARE (fallback)

# Capabilities
HardwareDecoderCapabilities
  - supported_codecs: [Codec]
  - max_resolution: (width, height)
  - max_fps: int
  - cuda_compute_capability: str
  - memory_mb: int
  - driver_version: str

# Metriche performance
DecoderPerformanceMetrics
  - frames_decoded: int
  - frames_failed: int
  - avg_frame_time_ms: float
  - success_rate: float
  - avg_throughput_fps: float
  - gpu_memory_used_mb: float

# Decoder principale
HardwareDecoder
  - get_best_decoder() -> DecoderType
  - get_decoder_for_codec(codec) -> DecoderType
  - get_capabilities() -> dict[DecoderType, Capabilities]
  - get_metrics() -> DecoderPerformanceMetrics
```

#### Uso

```python
from volley_analizer.core import get_hardware_decoder, Codec

# Ottieni decoder globale
decoder = get_hardware_decoder()

# Verifica best decoder
best = decoder.get_best_decoder()
print(f"Best decoder: {best.value}")

# Verifica capabilities
caps = decoder.get_capabilities()
for decoder_type, capability in caps.items():
    print(f"{decoder_type.value}: {capability}")

# Per codec specifico
h264_decoder = decoder.get_decoder_for_codec(Codec.H264)

# Metriche
metrics = decoder.get_metrics()
print(f"Success rate: {metrics.success_rate:.1f}%")
print(f"Avg FPS: {metrics.avg_throughput_fps:.1f}")
```

#### NVIDIA NVDEC Support

**Rilevamento automatico di:**
- GPU disponibile (nvidia-smi)
- Driver version
- CUDA Compute Capability
- Memoria GPU
- FFmpeg NVDEC support
- Codec supportati per CC

**Supporto codec per Compute Capability:**
- CC 3.0+: H.264, VP9 (limitato)
- CC 5.0+: H.264, H.265, VP9
- CC 6.1+: H.264, H.265, VP9, AV1
- CC 7.0+: Full support

### 3. `frame_buffer.py` (486 linee)

Buffer circolare thread-safe per frame video.

#### Classi Principali

```python
# Metriche buffer
BufferMetrics
  - frames_added: int
  - frames_removed: int
  - frames_dropped: int
  - current_buffer_size: int
  - fps: float (property)
  - buffer_usage_percent: float (property)
  - drop_rate_percent: float (property)

# Buffer principale
FrameBuffer
  - put(frame, frame_index, timestamp, block, timeout) -> bool
  - get(block, timeout) -> (frame, index, timestamp)
  - peek(index) -> frame
  - is_empty() -> bool
  - is_full() -> bool
  - clear()
  - get_metrics() -> BufferMetrics

# Pool buffer
FrameBufferPool
  - get_buffer(name) -> FrameBuffer
  - add_buffer(name, size) -> FrameBuffer
  - get_metrics() -> dict[str, BufferMetrics]

# Buffer adattivo
AdaptiveBuffer
  - Auto-adjust size basato su metriche
  - Aumenta se drop rate > 5%
  - Diminuisce se no drops e usage < 30%
```

#### Uso

```python
from volley_analizer.core import FrameBuffer
import numpy as np

# Crea buffer
buffer = FrameBuffer(max_size=30)

# Aggiungi frame
frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
success = buffer.put(frame, frame_index=0, timestamp=0.0)

# Ottieni frame (FIFO)
result = buffer.get(block=False)
if result:
    frame, index, timestamp = result
    # Processa frame

# Metriche
metrics = buffer.get_metrics()
print(f"Buffer usage: {metrics.buffer_usage_percent:.1f}%")
print(f"FPS: {metrics.fps:.1f}")
print(f"Frames: {metrics.frames_added}/{metrics.frames_removed}")
```

#### Thread Safety

Il buffer è completamente thread-safe:
- `put()` e `get()` possono essere chiamati da thread differenti
- Sincronizzazione con `RLock` e `Condition`
- Supporto per blocking operations con timeout
- Callback per frame added/buffer full events

### 4. `video_processor.py` (Aggiornato)

Integrazione con il nuovo sistema di acquisizione.

#### Uso

```python
from volley_analizer.core import VideoProcessor

# File locale
processor = VideoProcessor(
    "video.mp4",
    sample_every_n_frames=3,
    use_gpu=True,
    buffer_size=30,
    target_resolution=(640, 480)
)

# Streaming
processor = VideoProcessor(
    "rtsp://camera/stream",
    sample_every_n_frames=1,
    use_gpu=True
)

# Leggi frame
for frame_idx, timestamp, frame in processor.frames():
    # Processa frame
    pass

# Info sorgente
info = processor.get_source_info()
print(f"Source type: {info['type']}")
print(f"Resolution: {info['width']}x{info['height']}")
print(f"FPS: {info['fps']}")

# Buffer metrics
metrics = processor.get_buffer_metrics()
if metrics:
    print(f"Buffer usage: {metrics.buffer_usage_percent:.1f}%")

processor.release()
```

#### Fallback Automatico

Se il nuovo sistema fallisce, il VideoProcessor automaticamente:
1. Prova il nuovo sistema (video_source)
2. Se fallisce, torna a cv2.VideoCapture (legacy)
3. Mantiene API uniforme per entrambi

## Configurazione

### VideoSourceConfig

```python
@dataclass
class VideoSourceConfig:
    # Connection
    timeout_seconds: float = 10.0              # Timeout connessione
    max_connection_retries: int = 3             # Retry per streaming
    retry_delay_seconds: float = 2.0            # Delay tra retry
    
    # Decoding
    use_gpu: bool = True                        # GPU acceleration
    gpu_device_id: int = 0                      # GPU device index
    target_fps: Optional[float] = None          # Target FPS (adaptive)
    target_resolution: Optional[tuple] = None   # Resolution scaling
    
    # Buffering
    buffer_size: int = 30                       # Buffer frame count
    skip_frames: int = 0                        # Frame skipping
    
    # Performance
    read_timeout_ms: int = 5000                 # Read timeout
    enable_threading: bool = True               # Use threading
    
    # Fallback
    enable_fallback_decode: bool = True         # Fallback to CPU
    enable_fallback_source: bool = True         # Fallback to cv2
```

## Gestione Errori

### Strategie di Gestione

```python
# Errori di connessione per streaming
try:
    source = create_video_source("rtsp://camera/stream")
except RuntimeError:
    # Source non disponibile
    # -> Fallback a source alternativa

# Errori di decodifica
ret, frame = source.read_frame()
if not ret:
    # Frame non letto (timeout/errore)
    # -> Riconnessione automatica per streaming
    # -> EndOfStream per file locali

# Metriche errori
info = processor.get_source_info()
error_count = info.get('errors', 0)
frame_count = info.get('frames_read', 0)
```

### Reconnection Strategy per Streaming

Per streaming RTSP/RTMP/HLS:
- Retry automatico fino a `max_connection_retries`
- Delay tra retry: `retry_delay_seconds`
- Timeout connessione: `timeout_seconds`
- Timeout lettura: `read_timeout_ms`
- Auto-reconnect se nessun frame per 2x read_timeout

## Performance Tips

### Per File Locali

```python
config = VideoSourceConfig(
    use_gpu=True,           # GPU acceleration
    target_resolution=(640, 480),  # Scala se necessario
    skip_frames=2,          # Salta frame se processing slow
)
source = create_video_source("video.mp4")
```

### Per Streaming

```python
config = VideoSourceConfig(
    buffer_size=20,         # Smaller buffer per bassa latency
    timeout_seconds=15,     # Higher timeout
    max_connection_retries=5,
    retry_delay_seconds=3,
)
source = create_video_source("rtsp://camera")
```

### Per Webcam

```python
config = VideoSourceConfig(
    buffer_size=5,          # Minimal buffer
    skip_frames=0,          # Niente skip
    target_resolution=(320, 240),  # Lower resolution
)
source = create_video_source("0")
```

## Testing

Run test suite:

```bash
pytest tests/test_video_acquisition.py -v
```

Test specifici:
```bash
# Buffer tests
pytest tests/test_video_acquisition.py::TestFrameBuffer -v

# Decoder tests
pytest tests/test_video_acquisition.py::TestHardwareDecoder -v

# Performance tests
pytest tests/test_video_acquisition.py::TestPerformance -v
```

## Logging

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("volley_analizer.core")
```

## Limitazioni e Considerazioni

1. **NVIDIA NVDEC**: Richiede FFmpeg con NVDEC support compilato
2. **Streaming**: Soggetto a latency e quality based on connection
3. **Webcam**: Limitato dal driver/hardware camera
4. **Resolution scaling**: Aumenta overhead CPU
5. **Frame skipping**: Può perdere frames importanti

## Roadmap Futuro

- [ ] Intel QuickSync support
- [ ] AMD VCE support
- [ ] Frame interpolation per lower framerate sources
- [ ] Formato output alternativi (RGBA, YUV)
- [ ] Recording with encoding
- [ ] Multi-source orchestration
- [ ] Load balancing per streaming sources
