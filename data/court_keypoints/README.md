# Dataset AI campo/keypoints

Questa cartella è il template per addestrare un modello YOLO pose che riconosce i 4 angoli del campo.

## Keypoint richiesti

Ogni immagine deve avere 4 keypoint nell'ordine:

1. alto-sinistra
2. alto-destra
3. basso-destra
4. basso-sinistra

## Workflow

1. Da GUI: `Addestramento > Estrai frame per AI campo...`
2. Annota i frame in Label Studio, CVAT o Roboflow con 4 keypoint.
3. Esporta in formato YOLO pose.
4. Inserisci le immagini annotate in:
   - `images/train`
   - `images/val`
5. Inserisci le label corrispondenti in:
   - `labels/train`
   - `labels/val`
6. Da GUI: `Addestramento > Addestra AI campo/keypoints...`

Il file `data.yaml` è già predisposto per 4 keypoint.
