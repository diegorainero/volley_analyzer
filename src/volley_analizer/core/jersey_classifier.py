from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover
    torch = None
    nn = None


class SmallJerseyCNN(nn.Module if nn is not None else object):
    def __init__(self, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = x.flatten(1)
        return self.classifier(x)


class JerseyClassifier:
    """Inferenza two-stage su crop giocatore per numero maglia o team.

    Il checkpoint deve contenere:
    - model_state_dict
    - class_names
    """

    def __init__(
        self,
        checkpoint_path: str | Path,
        image_size: int = 128,
        device: str | None = None,
    ):
        if torch is None:
            raise RuntimeError(
                "PyTorch non disponibile: installa torch per usare JerseyClassifier"
            )

        self.checkpoint_path = Path(checkpoint_path)
        self.image_size = image_size
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
        self.class_names = checkpoint["class_names"]
        self.model = SmallJerseyCNN(num_classes=len(self.class_names)).to(self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def predict(self, crop_bgr: np.ndarray) -> tuple[str, float]:
        if crop_bgr is None or crop_bgr.size == 0:
            return "unknown", 0.0
        image = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.image_size, self.image_size))
        tensor = torch.from_numpy(image).float().permute(2, 0, 1) / 255.0
        tensor = tensor.unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]
            confidence, index = torch.max(probs, dim=0)
        return self.class_names[int(index.item())], float(confidence.item())
