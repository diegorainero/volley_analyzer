from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crea dataset YOLO da video usando pseudo-label automatiche"
    )
    parser.add_argument("video", help="Path video")
    parser.add_argument("--output", default="data/volley_yolo")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--sample-every", type=int, default=30)
    parser.add_argument("--max-frames", type=int, default=1000)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    args = parser.parse_args()

    output = Path(args.output)
    for split in ["train", "val"]:
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)

    data_yaml = output / "data.yaml"
    if not data_yaml.exists():
        data_yaml.write_text(
            f"path: {output}\ntrain: images/train\nval: images/val\nnc: 1\nnames:\n  0: player\n",
            encoding="utf-8",
        )

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"Impossibile aprire video: {args.video}")

    model = YOLO(args.model)
    frame_idx = 0
    saved = 0
    while saved < args.max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % args.sample_every != 0:
            frame_idx += 1
            continue

        results = model.predict(frame, verbose=False, classes=[0], conf=args.conf)
        boxes = results[0].boxes if results else []
        if boxes is None or len(boxes) == 0:
            frame_idx += 1
            continue

        split = "val" if (saved % max(1, int(1 / args.val_ratio))) == 0 else "train"
        image_name = f"frame_{frame_idx:06d}.jpg"
        label_name = f"frame_{frame_idx:06d}.txt"
        cv2.imwrite(str(output / "images" / split / image_name), frame)

        h, w = frame.shape[:2]
        lines = []
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            xc = ((x1 + x2) / 2.0) / w
            yc = ((y1 + y2) / 2.0) / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h
            lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
        (output / "labels" / split / label_name).write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        saved += 1
        frame_idx += 1

    cap.release()
    print(f"Dataset creato in {output}. Frame salvati: {saved}")
    print(
        "Nota: sono pseudo-label automatiche. Correggile manualmente per un training di qualità."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
