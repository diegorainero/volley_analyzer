from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Training YOLO pose/keypoints per rilevare i 4 angoli del campo"
    )
    parser.add_argument("--data", required=True, help="data.yaml keypoint Ultralytics")
    parser.add_argument("--model", default="yolov8n-pose.pt")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None)
    parser.add_argument("--project", default="runs/volley")
    parser.add_argument("--name", default="court_keypoints")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset keypoints non trovato: {data_path}. "
            "Crea prima il dataset oppure usa il template in data/court_keypoints/data.yaml"
        )

    dataset_root = data_path.parent
    train_images = dataset_root / "images" / "train"
    val_images = dataset_root / "images" / "val"
    has_train_images = train_images.exists() and any(train_images.glob("*"))
    has_val_images = val_images.exists() and any(val_images.glob("*"))
    if not has_train_images or not has_val_images:
        raise RuntimeError(
            "Dataset keypoints vuoto o incompleto. Inserisci immagini annotate in:\n"
            f"- {train_images}\n"
            f"- {val_images}\n"
            "e le label YOLO pose corrispondenti in labels/train e labels/val."
        )

    model = YOLO(args.model)
    kwargs = {
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": args.project,
        "name": args.name,
        "task": "pose",
    }
    if args.device is not None:
        kwargs["device"] = args.device
    model.train(**kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
