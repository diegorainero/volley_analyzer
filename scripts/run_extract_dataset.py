import os
import sys

from dataset_tools.extract_crops import extract_crops_and_labels
from detectors.yolov8_detector import YOLOv8Detector

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            "Usage: python scripts/run_extract_dataset.py <video_path> <model_path> <output_dir> [class_id] [conf_thresh]"
        )
        sys.exit(1)
    video_path = sys.argv[1]
    model_path = sys.argv[2]
    output_dir = sys.argv[3]
    class_id = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    conf_thresh = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5

    detector = YOLOv8Detector(model_path, task="detect")
    extract_crops_and_labels(video_path, detector, output_dir, class_id, conf_thresh)
    print(f"Estrazione completata in {output_dir}")
