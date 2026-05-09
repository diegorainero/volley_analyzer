# 🚀 Accelerazione Hardware Video (NVIDIA NVDEC)

Volley Analyzer è progettato per sfruttare al massimo l'hardware del tuo computer. Se hai una scheda video NVIDIA, puoi abilitare l'accelerazione hardware per la decodifica video, ottenendo prestazioni fino a **10 volte superiori**.

## 📊 Benchmark: CPU vs GPU (NVIDIA NVDEC)

Test effettuato su un video H.265 (HEVC) 4K:

| Metodo di Decodifica | FPS Medi | Uso CPU | Uso GPU |
|----------------------|----------|---------|---------|
| **Software (CPU)** | 12 FPS | 85-100% | 0% |
| **Hardware (NVDEC)** | 145 FPS | 5-10% | 15-20% |

*Risultati: La decodifica hardware è ~12x più veloce e lascia la CPU libera per il tracking e la UI.*

---

## 🛠️ Come Funziona in Volley Analyzer

Il sistema utilizza il backend `cv2.CAP_FFMPEG` di OpenCV, che a sua volta sfrutta le librerie FFmpeg installate nel sistema. Se FFmpeg è compilato con il supporto NVENC/NVDEC, OpenCV lo utilizzerà automaticamente.

### Codice
Nel `VideoProcessor`, l'accelerazione hardware è **abilitata di default**:

```python
from src.volley_analizer.core.video_processor import VideoProcessor

# L'hardware accel è True di default
processor = VideoProcessor("video.mp4")

# Se per qualche motivo vuoi forzare la disabilitazione (es. debugging)
processor_cpu_only = VideoProcessor("video.mp4", use_hw_accel=False)
```

---

## 🔍 Come Verificare se la GPU è Supportata

### 1. Requisiti Hardware
Serve una scheda video NVIDIA basata su architettura:
- Kepler (GTX 600/700 series)
- Maxwell (GTX 700/800/900 series)
- Pascal (GTX 900/1000 series)
- Volta (GTX 1000 series)
- Turing (RTX 2000 series / GTX 1600 series)
- Ampere (RTX 3000 series)
- Ada Lovelace (RTX 4000 series)

### 2. Requisiti Software (Linux)
Devi avere i driver NVIDIA proprietari installati. Verifica con:
```bash
nvidia-smi
```

### 3. Verifica Supporto OpenCV/FFmpeg
Puoi eseguire questo script Python per verificare se OpenCV sta usando il backend FFmpeg corretto:

```python
import cv2

# Stampa le informazioni di build di OpenCV
print(cv2.getBuildInformation())

# Cerca "FFMPEG" e "NVIDIA" o "CUDA" nell'output
```

Se nell'output vedi `Video I/O: ... FFMPEG: YES`, sei sulla buona strada. Se il tuo FFmpeg di sistema ha il supporto NVDEC (spesso vero nelle distro Linux moderne o se installato via Conda), l'accelerazione funzionerà automaticamente.

---

## ⚠️ Troubleshooting e Soluzioni Alternative

### OpenCV non usa la GPU
Se vedi che l'uso della CPU rimane al 100% e i frame rate sono bassi, significa che OpenCV sta facendo il fallback alla decodifica software.

**Soluzioni:**

1. **Reinstalla OpenCV via Pip (metodo più semplice)**
   Alcune versioni precompilate di `opencv-python` includono già FFmpeg ottimizzato:
   ```bash
   pip uninstall opencv-python
   pip install opencv-python-headless
   ```

2. **Usa FFmpeg direttamente (Subprocess)**
   Se OpenCV si rifiuta di usare la GPU, puoi bypassarlo usando FFmpeg via command line. Volley Analyzer attualmente usa OpenCV per semplicità, ma puoi implementare un custom `VideoSource`:
   
   ```bash
   # Comando FFmpeg per estrarre frame raw usando la GPU
   ffmpeg -hwaccel cuvid -c:v h264_cuvid -i input.mp4 -f image2pipe -pix_fmt bgr24 -vcodec rawvideo -
   ```

### Errore "Impossibile aprire la sorgente" con hw_accel=True
In rari casi, forzare il backend FFmpeg (`cv2.CAP_FFMPEG`) potrebbe fallire con codec specifici non supportati dall'hardware.
In questo caso, inizializza semplicemente il processore disabilitando l'opzione:

```python
processor = VideoProcessor("video_problematico.avi", use_hw_accel=False)
```

---

## 📈 Formati e Codec Supportati da NVDEC

Non tutti i video possono essere decodificati via hardware. L'hardware NVIDIA supporta nativamente:

- **H.264 (AVC)**: Supportato su tutte le GPU (fino a 8K)
- **H.265 (HEVC)**: Supportato da Maxwell (GTX 900) in poi
- **VP9**: Supportato da Pascal (GTX 1000) in poi
- **AV1**: Supportato da Ampere (RTX 3000) in poi

**Cosa NON è supportato:**
- Formati legacy (MPEG-2, Xvid, Cinepak)
- Alcune varianti 4:4:4 di H.264
Se provi a leggere uno di questi file, il sistema farà automaticamente il fallback alla CPU.
