import sys

from pipeline.main_pipeline import run_pipeline

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python scripts/run_pipeline.py <video_path> <model_path> [detect|segment]"
        )
        sys.exit(1)
    video_path = sys.argv[1]
    model_path = sys.argv[2]
    task = sys.argv[3] if len(sys.argv) > 3 else "detect"
    run_pipeline(video_path, model_path, task)
