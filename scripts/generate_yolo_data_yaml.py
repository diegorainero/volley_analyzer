from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from volley_analizer.training.data_yaml import generate_yolo_data_yaml


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera data.yaml per training YOLO/YOLO-seg"
    )
    parser.add_argument("dataset_dir", help="Directory dataset YOLO")
    parser.add_argument(
        "--classes",
        required=True,
        help="Classi separate da virgola, es: player,number,home,away",
    )
    parser.add_argument("--output", default=None, help="Path output data.yaml")
    args = parser.parse_args()

    classes = [name.strip() for name in args.classes.split(",") if name.strip()]
    if not classes:
        parser.error("Specifica almeno una classe con --classes")

    path = generate_yolo_data_yaml(args.dataset_dir, classes, args.output)
    print(f"data.yaml creato: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
