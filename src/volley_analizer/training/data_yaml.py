from __future__ import annotations

from pathlib import Path


def generate_yolo_data_yaml(
    dataset_dir: str | Path,
    class_names: list[str],
    output_path: str | Path | None = None,
) -> Path:
    """Generate an Ultralytics-compatible data.yaml file.

    Expected dataset layout:
    - dataset_dir/images/train
    - dataset_dir/images/val
    - dataset_dir/labels/train
    - dataset_dir/labels/val
    """
    dataset_path = Path(dataset_dir).resolve()
    output = Path(output_path).resolve() if output_path else dataset_path / "data.yaml"
    names = "\n".join(f"  {idx}: {name}" for idx, name in enumerate(class_names))
    content = (
        f"path: {dataset_path}\n"
        "train: images/train\n"
        "val: images/val\n"
        f"nc: {len(class_names)}\n"
        "names:\n"
        f"{names}\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output
