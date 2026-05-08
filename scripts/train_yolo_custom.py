from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Avvia training Ultralytics YOLO custom"
    )
    parser.add_argument("--data", required=True, help="Path data.yaml")
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="Peso base YOLO, es. yolov8n.pt o yolov8n-seg.pt",
    )
    parser.add_argument("--task", choices=["detect", "segment"], default="detect")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None, help="Device Ultralytics, es. 0, cpu")
    parser.add_argument("--project", default="runs/volley")
    parser.add_argument("--name", default="custom_yolo")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"data.yaml non trovato: {data_path}. Usa prima 'Genera data.yaml YOLO' o 'Crea dataset YOLO da video'."
        )
    dataset_root = data_path.parent
    missing = []
    for rel in ["images/train", "images/val", "labels/train", "labels/val"]:
        path = dataset_root / rel
        if not path.exists():
            missing.append(str(path))
    if missing:
        raise RuntimeError(
            "Dataset YOLO incompleto. Cartelle mancanti:\n" + "\n".join(missing)
        )
    if not any((dataset_root / "images" / "train").glob("*")) or not any(
        (dataset_root / "images" / "val").glob("*")
    ):
        raise RuntimeError(
            "Dataset YOLO senza immagini train/val. Usa 'Addestramento > Crea dataset YOLO da video...' "
            "oppure aggiungi immagini e label annotate manualmente."
        )

    model = YOLO(args.model)
    kwargs = {
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": args.project,
        "name": args.name,
        "task": args.task,
    }
    if args.device is not None:
        kwargs["device"] = args.device

    results = model.train(**kwargs)
    print(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
