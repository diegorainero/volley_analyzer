# Guida all'Integrazione di Nuove Sorgenti Video

Questa guida descrive come utilizzare e estendere il modulo `video_source.py` in Volley Analyzer.

## Architettura del Modulo

Il modulo si basa su 3 componenti principali:

1. `VideoSourceInfo`: Una dataclass che contiene i metadati della sorgente (risoluzione, fps, se è uno stream live).
2. `VideoSource`: Classe base astratta (ABC) che definisce l'interfaccia standard per qualsiasi sorgente video.
3. `VideoProcessor`: La classe ad alto livello che l'applicazione utilizza, la quale istanzia la corretta `VideoSource`.

## Come Usare il VideoProcessor

La classe `VideoProcessor` è il punto d'ingresso principale. Sostituisce il vecchio uso diretto di `cv2.VideoCapture` offrendo:
- Rilevamento automatico del tipo di sorgente
- Configurazione automatica dell'accelerazione hardware
- Gestione trasparente del frame skipping

### Esempio Base
```python
from src.volley_analizer.core.video_processor import VideoProcessor

# Inizializza il processore. Il path può essere:
# - Un percorso file: "match.mp4"
# - Un URL stream: "rtsp://camera/stream"
# - Un ID webcam: 0
processor = VideoProcessor("match.mp4", sample_every_n_frames=2, use_hw_accel=True)

# Accedi ai metadati unificati
print(f"Risoluzione: {processor.metadata.width}x{processor.metadata.height}")
print(f"FPS nativi: {processor.metadata.fps}")
print(f"È una diretta live? {processor.is_live}")

# Itera sui frame
for frame_idx, timestamp_sec, frame in processor.frames():
    # 'frame_idx' è l'indice originale del frame nel video
    # 'timestamp_sec' è il tempo in secondi dall'inizio (approssimato per gli stream)
    # 'frame' è l'array numpy BGR dell'immagine
    process_frame(frame)

processor.release()
```

## Creare una Nuova Sorgente Custom

Attualmente il sistema usa `OpenCVSource` per tutto, ma l'architettura è pensata per essere espandibile. Ad esempio, potresti voler implementare una sorgente basata nativamente su FFmpeg-python, su PyAV, o su un SDK specifico di una telecamera.

### 1. Implementare l'Interfaccia

Devi creare una classe che erediti da `VideoSource`:

```python
from src.volley_analizer.core.video_source import VideoSource, VideoSourceInfo
import numpy as np

class CustomCameraSDKSource(VideoSource):
    def __init__(self, ip_address: str):
        self.ip = ip_address
        self.camera = NessunSDK.Camera()
        self._info = None
        self._is_opened = False

    def open(self) -> bool:
        if self.camera.connect(self.ip):
            self._is_opened = True
            self._info = VideoSourceInfo(
                width=self.camera.width,
                height=self.camera.height,
                fps=self.camera.fps,
                is_live=True,
                source_type="custom_sdk"
            )
            return True
        return False

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self.is_opened:
            return False, None
        
        success, frame = self.camera.get_next_frame()
        return success, frame

    def release(self) -> None:
        self.camera.disconnect()
        self._is_opened = False

    def get_info(self) -> VideoSourceInfo | None:
        return self._info

    @property
    def is_opened(self) -> bool:
        return self._is_opened
```

### 2. Aggiornare la Factory

Dopo aver creato la tua classe, devi aggiornare il metodo `create` di `VideoSourceFactory` in `src/volley_analizer/core/video_source.py` per restituire la tua nuova classe quando opportuno:

```python
class VideoSourceFactory:
    @staticmethod
    def create(source_path: str | int, use_hw_accel: bool = True) -> VideoSource:
        source_str = str(source_path)
        
        # Se l'URL inizia con un prefisso custom, usa la nostra nuova classe
        if source_str.startswith("custom://"):
            ip = source_str.replace("custom://", "")
            return CustomCameraSDKSource(ip)
            
        # Altrimenti fallback alla classe standard
        return OpenCVSource(source_path, use_hw_accel)
```

Ora puoi usare il `VideoProcessor` normalmente:
```python
processor = VideoProcessor("custom://192.168.1.100")
```

## Gestione degli Stream Live (RTSP/RTMP)

Gli stream live sono speciali perché:
1. Non hanno un `frame_count` totale definito.
2. Possono avere ritardi di rete o disconnessioni.
3. Il tempo (`timestamp`) è calcolato artificialmente in base ai frame ricevuti e agli FPS dichiarati.

La classe `OpenCVSource` ottimizza già FFmpeg per minimizzare la latenza impostando:
```python
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|analyzeduration;500000|probesize;5000000"
```
Questo forza l'uso del protocollo TCP (più stabile su reti congestionate) e riduce il tempo che FFmpeg passa ad analizzare lo stream prima di iniziare la riproduzione.
