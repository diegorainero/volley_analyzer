# Volley Analyzer Modular Pipeline

⚠️ **Consigliato Python 3.10 o 3.11**
Per la massima compatibilità delle dipendenze (es. psycopg2-binary, python-dotenv, pyinstaller), usa Python 3.10 o 3.11. Python 3.14 è molto recente e molte librerie scientifiche e di packaging potrebbero non essere ancora compatibili.

💡 **Se usi Python 3.14 o superiore**: installa anche il pacchetto di sistema `libpq-dev` (Ubuntu/Debian) o `postgresql-devel` (Fedora) per permettere la compilazione di psycopg2-binary:

    sudo apt install libpq-dev
# oppure
    sudo dnf install postgresql-devel

## Moduli
- detectors: detection/segmentation (YOLOv8)
- trackers: tracking (DeepSORT)
- dataset_tools: estrazione dataset
- pipeline: pipeline end-to-end

## Tracking
Il tracking dei giocatori ora è gestito esclusivamente da DeepSORT (`deep_sort_realtime`), che garantisce robustezza anche in caso di sovrapposizioni e occlusioni.
Non è più necessario installare ByteTrack o YOLOX per il tracking.

## Instance segmentation
Per separare meglio giocatori sovrapposti puoi usare YOLOv8-seg.

- Da GUI: abilita `Usa instance segmentation YOLOv8-seg`.
- Da CLI: usa `--segment` oppure passa un modello `*-seg.pt`.

Esempi:

`python main.py video.mp4 --segment`

`python main.py video.mp4 --model yolov8n-seg.pt`

Se abiliti la segmentazione senza indicare un modello `-seg`, la pipeline usa automaticamente `yolov8n-seg.pt`; Ultralytics lo scaricherà se non è presente localmente.
Le maschere instance vengono usate nella preview per separare visivamente le persone sovrapposte e vengono associate alle tracce DeepSORT.

## Miglior riconoscimento AI: maglie, numeri, squadre

### A. Fine-tune YOLO detect/segment

1. Prepara dataset in formato YOLO:
   - `images/train`, `images/val`
   - `labels/train`, `labels/val`
2. Genera `data.yaml`:

`python scripts/generate_yolo_data_yaml.py data/volley_yolo --classes player,number`

3. Avvia training detection:

`python scripts/train_yolo_custom.py --task detect --model yolov8n.pt --data data/volley_yolo/data.yaml --epochs 50 --imgsz 640`

4. Avvia training segmentation:

`python scripts/train_yolo_custom.py --task segment --model yolov8n-seg.pt --data data/volley_seg/data.yaml --epochs 50 --imgsz 640`

### B. Two-stage detection → crop → classificatore numero/team

1. Estrai crop dei giocatori:

`python scripts/extract_player_crops_for_classifier.py video.mp4 --output data/jersey_crops/unlabeled --model yolov8n-seg.pt --seg`

2. Sposta i crop in cartelle per classe, ad esempio:
   - `data/jersey_dataset/7/*.jpg`
   - `data/jersey_dataset/10/*.jpg`
   - `data/jersey_dataset/team_home/*.jpg`
   - `data/jersey_dataset/team_away/*.jpg`

3. Allena il classificatore:

`python scripts/train_jersey_classifier.py data/jersey_dataset --output models/jersey_classifier.pt --epochs 30`

4. Usa il classificatore nella pipeline:

CLI:

`python main.py video.mp4 --model yolov8n-seg.pt --jersey-classifier models/jersey_classifier.pt`

GUI:

imposta il campo `Classificatore maglia` a `models/jersey_classifier.pt`.

## Setup Sviluppo (Volleyball Scout)

Per preparare l'ambiente di sviluppo per la parte di scouting (PyQt6 + DB):

1. **Crea ambiente virtuale**:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Esegui setup automatico**:
   ```sh
   python setup.py dev_setup
   ```
   *Questo comando installa i requirements ed esegue automaticamente le migrazioni Alembic.*

## Scouting Workflow

Il modulo `volleyball_scout` ora supporta il seguente flusso:
1. **Dashboard**: Panoramica match.
2. **Match Setup**: Scelta squadre e competizione.
3. **Roster**: Selezione convocati.
4. **Formazione**: Inserimento dei 6 titolari e del libero per ogni squadra.
5. **Scout**: Inserimento eventi live.

## Esempio uso Pipeline AI
python scripts/run_pipeline.py
