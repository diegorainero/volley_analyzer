from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from volley_analizer.core.detector import PlayerDetector


def clamp_bbox(bbox, width: int, height: int):
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(0, min(width, x2))
    y2 = max(0, min(height, y2))
    return x1, y1, x2, y2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estrae crop giocatori da video per dataset classificatore numero/squadra"
    )
    parser.add_argument("video", help="Path video")
    parser.add_argument(
        "--output", default="data/player_crops/unlabeled", help="Directory output"
    )
    parser.add_argument("--model", default="yolov8n.pt", help="Modello YOLO/YOLO-seg")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument(
        "--sample-every", type=int, default=10, help="Salva 1 frame ogni N"
    )
    parser.add_argument("--min-area", type=int, default=500)
    parser.add_argument(
        "--seg",
        action="store_true",
        help="Usa yolov8n-seg.pt se il modello fornito non è -seg",
    )
    args = parser.parse_args()

    model_name = args.model
    if args.seg and "-seg" not in model_name:
        model_name = "yolov8n-seg.pt"

    detector = PlayerDetector(
        model_name=model_name,
        confidence_threshold=args.conf,
        detector_type="yolo",
        min_detection_area=args.min_area,
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"Impossibile aprire video: {args.video}")

    frame_idx = 0
    saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % args.sample_every != 0:
            frame_idx += 1
            continue

        detections = detector.detect(frame)
        h, w = frame.shape[:2]
        for det_idx, det in enumerate(detections):
            x1, y1, x2, y2 = clamp_bbox(det.bbox, w, h)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = frame[y1:y2, x1:x2]
            filename = (
                output_dir
                / f"frame_{frame_idx:06d}_det_{det_idx:02d}_conf_{det.confidence:.2f}.jpg"
            )
            cv2.imwrite(str(filename), crop)
            saved += 1

        frame_idx += 1

    cap.release()
    print(f"Crop salvati: {saved} in {output_dir}")
    print("Ora puoi spostare manualmente i crop in cartelle per classe, es:")
    print("data/jersey_dataset/train/7/*.jpg, data/jersey_dataset/train/10/*.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
