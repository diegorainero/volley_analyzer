from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estrae frame da annotare per AI campo/keypoints"
    )
    parser.add_argument("video", help="Path video")
    parser.add_argument("--output", default="data/court_keypoints/raw_frames")
    parser.add_argument(
        "--sample-every", type=int, default=90, help="Salva 1 frame ogni N frame"
    )
    parser.add_argument("--max-frames", type=int, default=300)
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f"Impossibile aprire video: {args.video}")

    frame_idx = 0
    saved = 0
    while saved < args.max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % args.sample_every == 0:
            path = output / f"court_frame_{frame_idx:06d}.jpg"
            cv2.imwrite(str(path), frame)
            saved += 1
        frame_idx += 1

    cap.release()
    print(f"Frame salvati: {saved} in {output}")
    print(
        "Annota questi frame con 4 keypoint in Label Studio/Roboflow/CVAT e poi esporta in formato YOLO pose."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
