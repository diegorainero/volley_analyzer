from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(slots=True)
class FieldDimensions:
    width_m: float = 9.0
    height_m: float = 9.0  # Metà campo


class FieldMapper:
    """Mappa le coordinate video alle coordinate di campo.

    Layout reale a 6 zone per lato, come riferimento pallavolo:

    Lato alto:
    1  6  5
    2  3  4
    -------- rete --------
    4  3  2
    5  6  1
    Lato basso
    """

    def __init__(
        self,
        src_points: list[list[float]] | None = None,
        field: FieldDimensions | None = None,
        num_fields: int = 1,
    ) -> None:
        """
        Args:
            src_points: Punti di calibrazione dell'immagine video (4 angoli)
            field: Dimensioni del campo
            num_fields: 1 o 2 (se 2, il campo video contiene entrambi i campi)
        """
        self.field = field or FieldDimensions()
        self.num_fields = num_fields
        default_src = src_points or [[100, 100], [1820, 100], [1820, 900], [100, 900]]

        if num_fields == 1:
            # Un solo campo
            dst = [
                [0, 0],
                [self.field.width_m, 0],
                [self.field.width_m, self.field.height_m],
                [0, self.field.height_m],
            ]
        else:
            # Due campi (uno sopra, uno sotto)
            dst = [
                [0, 0],
                [self.field.width_m, 0],
                [self.field.width_m, self.field.height_m * 2],
                [0, self.field.height_m * 2],
            ]

        self.homography, _ = cv2.findHomography(
            np.float32(default_src), np.float32(dst)
        )
        self.inverse_homography = np.linalg.inv(self.homography)

    def map_field_to_image(self, point: tuple[float, float]) -> tuple[int, int]:
        field_point = np.array([[[float(point[0]), float(point[1])]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(field_point, self.inverse_homography)
        x, y = mapped[0][0]
        return int(round(float(x))), int(round(float(y)))

    def map_bbox_to_field(
        self, bbox: tuple[float, float, float, float]
    ) -> tuple[float, float]:
        x1, y1, x2, y2 = bbox
        foot_point = np.array([[[float((x1 + x2) / 2.0), float(y2)]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(foot_point, self.homography)
        x_m, y_m = mapped[0][0]
        return float(x_m), float(y_m)

    def get_zone(self, position: tuple[float, float]) -> int:
        """Ritorna la zona pallavolo (1-6) secondo il layout reale.

        Con `num_fields=2` il campo completo è 9x18m e la rete è a y=9m.
        Con `num_fields=1` si assume una singola metà campo orientata come il lato basso.
        """
        x_m, y_m = position

        x_m = min(max(x_m, 0.0), self.field.width_m - 1e-6)
        y_m = min(max(y_m, 0.0), self.field.height_m * self.num_fields - 1e-6)

        col = int(x_m / (self.field.width_m / 3.0))
        col = min(2, max(0, col))

        if self.num_fields == 2 and y_m < self.field.height_m:
            # Lato alto: riga 0 fondo campo, riga 1 vicino rete
            y_local = y_m
            row = int(y_local / (self.field.height_m / 2.0))
            row = min(1, max(0, row))
            zone_map = [
                [1, 6, 5],
                [2, 3, 4],
            ]
            return zone_map[row][col]

        # Lato basso o singola metà campo: riga 0 vicino rete, riga 1 fondo campo
        y_local = y_m - self.field.height_m if self.num_fields == 2 else y_m
        row = int(y_local / (self.field.height_m / 2.0))
        row = min(1, max(0, row))
        zone_map = [
            [4, 3, 2],
            [5, 6, 1],
        ]
        return zone_map[row][col]
