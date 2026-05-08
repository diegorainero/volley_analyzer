from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Volleyball video analyzer MVP")
    parser.add_argument("video", help="Percorso del video da analizzare")
    parser.add_argument("--output-dir", default="output", help="Directory di export")
    parser.add_argument(
        "--sample-every", type=int, default=3, help="Processa 1 frame ogni N"
    )
    parser.add_argument(
        "--model", default="yolov8n.pt", help="Modello YOLO Ultralytics"
    )
    parser.add_argument(
        "--conf", type=float, default=0.25, help="Soglia confidenza detector"
    )
    parser.add_argument(
        "--chunk-seconds",
        type=int,
        default=60,
        help="Durata chunk di analisi (secondi)",
    )
    parser.add_argument(
        "--detector",
        choices=["yolo", "hog"],
        default="yolo",
        help="Tipo di detector da usare (yolo o hog)",
    )
    parser.add_argument(
        "--segment",
        action="store_true",
        help="Abilita segmentazione instance (YOLOv8-seg)",
    )
    parser.add_argument(
        "--jersey-classifier",
        default=None,
        help="Checkpoint classificatore numero/team, es. models/jersey_classifier.pt",
    )
    parser.add_argument(
        "--jersey-conf",
        type=float,
        default=0.45,
        help="Soglia confidenza classificatore maglia/numero",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        parser.error(f"Video non trovato: {video_path}")

    from ..pipeline.analysis_pipeline import PipelineConfig, VolleyballAnalysisPipeline

    # Se --segment, forza modello YOLOv8-seg e detector_type yolo
    detector_model = args.model
    detector_type = args.detector
    if getattr(args, "segment", False):
        if not detector_model.endswith("-seg.pt"):
            print("[INFO] --segment attivo: uso yolov8n-seg.pt di default")
            detector_model = "yolov8n-seg.pt"
        detector_type = "yolo"
    pipeline = VolleyballAnalysisPipeline(
        PipelineConfig(
            video_path=str(video_path),
            output_dir=args.output_dir,
            sample_every_n_frames=args.sample_every,
            detector_model=detector_model,
            detector_confidence=args.conf,
            detector_type=detector_type,
            use_instance_segmentation=getattr(args, "segment", False)
            or "-seg" in detector_model,
            jersey_classifier_model=args.jersey_classifier,
            jersey_confidence_threshold=args.jersey_conf,
        )
    )
    exported = None
    import traceback

    try:
        exported = pipeline.run_chunked(chunk_seconds=args.chunk_seconds)
    except KeyboardInterrupt:
        print("\nAnalisi interrotta dall'utente (CTRL+C)")
        return 1
    except Exception as e:
        print("Errore durante l'analisi:")
        traceback.print_exc()
        return 1

    print("Analisi completata")
    for name, path in exported.items():
        print(f"- {name}: {path.resolve()}")

    return 0
