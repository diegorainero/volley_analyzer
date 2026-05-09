# 📹 Video Sources - Sistema di Acquisizione Video

Volley Analyzer supporta nativamente molteplici sorgenti video, garantendo flessibilità sia per l'analisi offline che per lo streaming in tempo reale.

## 📋 Sorgenti Supportate

Il sistema riconosce automaticamente il tipo di sorgente dall'input:

| Tipo Sorgente | Formato Input | Esempio | Latenza | Caso d'Uso |
|---------------|--------------|---------|---------|------------|
| **File Locale** | Path al file | `video.mp4`, `/path/to/file.avi` | ~0ms | Analisi post-partita, Scouting |
| **RTSP Stream** | `rtsp://...` | `rtsp://admin:pass@192.168.1.100:554/stream` | ~500ms | Telecamere IP fisse in palestra |
| **RTMP Stream** | `rtmp://...` | `rtmp://localhost/live/volley` | ~1s | Streaming broadcast, OBS |
| **HLS Stream** | `http://...m3u8` | `http://server/stream.m3u8` | ~3-5s | Web streaming |
| **Webcam USB** | ID numerico | `0`, `1`, `2` | ~30ms | Test rapidi, setup portatile |

---

## 🚀 Quick Start

### Uso da CLI
Il `main.py` accetta qualsiasi tipo di sorgente:

```bash
# File locale
python main.py my_match.mp4

# Webcam (device 0)
python main.py 0

# Telecamera IP (RTSP)
python main.py rtsp://user:pass@192.168.1.100/stream
```

### Uso da Codice Python
Il `VideoProcessor` gestisce tutto automaticamente:

```python
from src.volley_analizer.core.video_processor import VideoProcessor

# Sostituisci la stringa con il tuo input
source_input = "rtsp://camera_ip/stream"  # o "video.mp4", o 0

# Inizializza (auto-detect type, auto-hardware accel)
processor = VideoProcessor(source_input, sample_every_n_frames=2)

# Processa i frame
for frame_idx, timestamp, frame in processor.frames():
    print(f"Lettura frame {frame_idx} al tempo {timestamp:.2f}s")
    
processor.release()
```

---

## ⚡ Accelerazione Hardware (NVDEC)

Per ottenere le massime prestazioni, il sistema supporta il decode video accelerato via GPU NVIDIA (NVDEC).

### Benefici dell'Hardware Decode:
- **Riduzione uso CPU**: La CPU rimane libera per il tracking e la UI
- **Velocità**: 5-10x più veloce per file 4K e H.265 (HEVC)
- **Minore latenza**: Cruciale per analisi RTSP in tempo reale

### Come abilitarlo
È abilitato di default. Il sistema proverà ad usare `cv2.CAP_FFMPEG` con backend hardware. Se non è disponibile o fallisce, farà un fallback trasparente al decoding software.

```python
# Opzionale: forzare l'uso (o disabilitarlo)
processor = VideoProcessor("video.mp4", use_hw_accel=True)
```

Per maggiori dettagli, leggi la [Guida all'Accelerazione Hardware](./HARDWARE_ACCELERATION.md).

---

## 🛠️ Ottimizzazioni per Tipo di Sorgente

### 1. File Locali (Analisi Offline)
- **Formati Consigliati**: H.264 o H.265 (HEVC) in container `.mp4`
- **Performance**: Sfrutta al massimo l'accelerazione hardware
- **Frame Skipping**: Per velocizzare l'analisi di lunghi video, usa `sample_every_n_frames=3` (analizza 1 frame su 3)

### 2. Streaming RTSP (Telecamere IP)
- Il sistema ottimizza automaticamente le variabili d'ambiente FFmpeg per ridurre la latenza:
  `rtsp_transport=tcp`, buffer minimizzati.
- Assicurati che la telecamera sia connessa via cavo (Ethernet), il Wi-Fi introduce latenza variabile.

### 3. Webcam
- Ideale per setup portatili con un laptop a bordo campo.
- La risoluzione massima e gli FPS dipendono dall'hardware della webcam.

---

## 🐛 Troubleshooting

### "Impossibile aprire la sorgente video"
1. **File locale**: Verifica che il percorso sia corretto e il file non sia corrotto.
2. **Webcam**: Assicurati che nessun altro programma (es. Zoom, Skype) stia usando la telecamera.
3. **RTSP**: Verifica le credenziali e l'IP. Testa lo stream con VLC Media Player prima.

### Latenza alta nello streaming
- Se usi RTSP su Wi-Fi, passa a connessione cablata.
- Riduci la risoluzione in output dalla configurazione della telecamera IP (1080p è ottimale, 4K richiede molta banda).

### Errori FFmpeg nel log
Se vedi errori relativi a codec o hardware acceleration, OpenCV farà il fallback al software decode. Per risolvere, potresti dover reinstallare OpenCV con supporto CUDA abilitato o aggiornare i driver NVIDIA.
