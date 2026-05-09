from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from volley_analizer.core.jersey_classifier import SmallJerseyCNN

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyTorch richiesto: installa torch") from exc


class CropFolderDataset(Dataset):
    def __init__(self, root: str | Path, image_size: int = 128):
        self.root = Path(root)
        self.image_size = image_size
        self.class_names = sorted([p.name for p in self.root.iterdir() if p.is_dir()])
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
        self.samples: list[tuple[Path, int]] = []
        for class_name in self.class_names:
            for path in sorted((self.root / class_name).glob("**/*")):
                if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                    self.samples.append((path, self.class_to_idx[class_name]))
        if not self.samples:
            raise RuntimeError(f"Nessuna immagine trovata in {self.root}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        path, label = self.samples[index]
        image = cv2.imread(str(path))
        if image is None:
            raise RuntimeError(f"Immagine non leggibile: {path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.image_size, self.image_size))
        tensor = torch.from_numpy(image).float().permute(2, 0, 1) / 255.0
        return tensor, label


def split_dataset(dataset: CropFolderDataset, val_ratio: float):
    indices = list(range(len(dataset)))
    random.shuffle(indices)
    val_size = max(1, int(len(indices) * val_ratio))
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    return torch.utils.data.Subset(dataset, train_indices), torch.utils.data.Subset(
        dataset, val_indices
    )


def evaluate(model, loader, device):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            preds = model(images).argmax(dim=1)
            correct += int((preds == labels).sum().item())
            total += int(labels.numel())
    return correct / max(1, total)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train small CNN per numeri maglia o team"
    )
    parser.add_argument(
        "dataset_dir", help="Dataset con cartelle per classe, es. train/7/*.jpg"
    )
    parser.add_argument("--output", default="models/jersey_classifier.pt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--image-size", type=int, default=128)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    device = torch.device(
        args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    )
    dataset = CropFolderDataset(args.dataset_dir, image_size=args.image_size)
    train_ds, val_ds = split_dataset(dataset, args.val_ratio)
    train_loader = DataLoader(
        train_ds, batch_size=args.batch, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=0)

    model = SmallJerseyCNN(num_classes=len(dataset.class_names)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    best_acc = 0.0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item())

        val_acc = evaluate(model, val_loader, device)
        avg_loss = running_loss / max(1, len(train_loader))
        print(f"epoch={epoch}/{args.epochs} loss={avg_loss:.4f} val_acc={val_acc:.3f}")
        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_names": dataset.class_names,
                    "image_size": args.image_size,
                    "val_acc": best_acc,
                },
                output,
            )

    print(f"Checkpoint salvato: {output} best_val_acc={best_acc:.3f}")
    print(f"Classi: {dataset.class_names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
