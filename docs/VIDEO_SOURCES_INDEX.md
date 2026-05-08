# 📑 Indice Sorgenti Video

Benvenuto nella documentazione del sistema di acquisizione video di Volley Analyzer.
Questo indice ti aiuterà a trovare rapidamente le informazioni che cerchi.

## 🚀 Per Cominciare

Se sei nuovo e vuoi solo far funzionare un video o la tua telecamera IP, inizia da qui:

1. **[Overview Sorgenti Video](./VIDEO_SOURCES.md)** ⭐
   - Quali sorgenti sono supportate (File, RTSP, HLS, Webcam)
   - Latenza prevista per ogni tipo
   - Quick start guide
   - Troubleshooting base

2. **[Esempi Pratici](../examples/video_sources_examples.py)**
   - 7 script Python pronti all'uso
   - Copia-incolla per file locali, webcam e RTSP

---

## ⚡ Performance e Ottimizzazione

Se il video va a scatti o la CPU è al 100%, leggi questa sezione:

1. **[Guida all'Accelerazione Hardware](./HARDWARE_ACCELERATION.md)** ⭐
   - Cos'è NVIDIA NVDEC
   - Benchmark: CPU vs GPU (fino a 10x più veloce)
   - Come verificare se il tuo PC è compatibile
   - Risoluzione problemi OpenCV/FFmpeg

2. **[Ottimizzazioni per Tipo di Sorgente](./VIDEO_SOURCES.md#%EF%B8%8F-ottimizzazioni-per-tipo-di-sorgente)**
   - Frame skipping (`sample_every_n_frames`)
   - Riduzione latenza per streaming RTSP
   - Ottimizzazioni per file locali H.265

---

## 🛠️ Per Sviluppatori

Se vuoi estendere il sistema o capire come funziona "sotto il cofano":

1. **[Guida Tecnica di Integrazione](./VIDEO_SOURCE_INTEGRATION.md)** ⭐
   - Architettura della classe `VideoProcessor`
   - Come l'interfaccia `VideoSource` astrae OpenCV
   - Tutorial: Come creare una sorgente video custom
   - Gestione avanzata degli stream live (RTSP/RTMP)

---

## 📝 Snippet Rapidi

### Leggere un file video
```python
from src.volley_analizer.core.video_processor import VideoProcessor
processor = VideoProcessor("match.mp4")
for frame_idx, timestamp, frame in processor.frames():
    pass
```

### Leggere da Telecamera IP (RTSP)
```python
# L'ottimizzazione latenza è automatica
processor = VideoProcessor("rtsp://admin:pass@192.168.1.100/stream")
```

### Leggere da Webcam
```python
# 0 è solitamente la webcam integrata
processor = VideoProcessor(0)
```

### Disabilitare Hardware Acceleration
```python
processor = VideoProcessor("video.mp4", use_hw_accel=False)
```

---

## 🐛 Risoluzione Problemi Rapida

- **Il video non si apre**: Verifica il percorso. Se è un file di rete (es. Google Drive montato), copialo in locale.
- **RTSP non si connette**: Apri VLC Media Player -> Media -> Apri Flusso di Rete, e inserisci lo stesso URL. Se non va in VLC, il problema è nella rete/telecamera, non in Volley Analyzer.
- **La CPU è al 100%**: Leggi la [Guida all'Accelerazione Hardware](./HARDWARE_ACCELERATION.md) per abilitare NVDEC. In alternativa, usa `sample_every_n_frames=2` o `3` per saltare i frame.
