from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.volley_analizer.core.dv_codes import (
    ATTACK_COMBOS,
    DV_CODES,
    EVALUATIONS,
    SETTER_CALLS,
    SKILL_CATEGORIES,
)


class DvSkillTable(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container_layout = QVBoxLayout(container)

        self._add_title(container_layout, "Legenda Codici DataVolley", 16)
        self._add_section(container_layout, "Categorie Skill", self._build_category_grid())
        self._add_section(container_layout, "Codici Skill", self._build_codes_table())
        self._add_section(container_layout, "Valutazioni", self._build_evaluations_grid())
        self._add_section(container_layout, "Combinazioni d'Attacco", self._build_combos_table())
        self._add_section(container_layout, "Chiamate Alzatore", self._build_setter_calls_table())

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _add_title(self, layout: QVBoxLayout, text: str, size: int = 14):
        label = QLabel(text)
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        label.setFont(f)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def _add_section(self, layout: QVBoxLayout, title: str, widget: QWidget):
        box = QGroupBox(title)
        inner = QVBoxLayout(box)
        inner.addWidget(widget)
        layout.addWidget(box)

    def _build_category_grid(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(4)
        row = 0
        for code, info in SKILL_CATEGORIES.items():
            lbl = QLabel(f"{info['icon']} = {info['label']}")
            color = QColor(info["color"])
            lbl.setStyleSheet(
                f"background-color: {color.name()}; color: white; "
                f"padding: 4px 8px; border-radius: 4px; font-weight: bold;"
            )
            grid.addWidget(lbl, row // 2, row % 2)
            row += 1
        return w

    def _build_codes_table(self) -> QWidget:
        cols = 4
        rows = (len(DV_CODES) + cols - 1) // cols
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(3)
        for i, dv in enumerate(DV_CODES):
            lbl = QLabel(f"{dv.code} = {dv.label}")
            cat = SKILL_CATEGORIES.get(dv.category, {})
            bg = dv.color if dv.color != "#999999" else cat.get("color", "#999999")
            lbl.setStyleSheet(
                f"background-color: {bg}; color: white; "
                f"padding: 3px 6px; border-radius: 3px; font-size: 10px;"
            )
            lbl.setToolTip(dv.description)
            grid.addWidget(lbl, i // cols, i % cols)
        return w

    def _build_evaluations_grid(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(6)
        for i, (code, info) in enumerate(EVALUATIONS.items()):
            lbl = QLabel(f"  {code}  = {info['label']}  ")
            lbl.setStyleSheet(
                f"background-color: {info['color']}; color: white; "
                f"padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 14px;"
            )
            grid.addWidget(lbl, i // 2, i % 2)
        return w

    def _build_combos_table(self) -> QWidget:
        known = [ac for ac in ATTACK_COMBOS if ac.code]
        table = QTableWidget(len(known), 3)
        table.setHorizontalHeaderLabels(["Codice", "Nome", "Descrizione"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 120)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for i, ac in enumerate(known):
            table.setItem(i, 0, QTableWidgetItem(ac.code))
            table.setItem(i, 1, QTableWidgetItem(ac.label))
            table.setItem(i, 2, QTableWidgetItem(ac.description))
            for col in range(3):
                item = table.item(i, col)
                if item:
                    item.setBackground(QColor(ac.color).lighter(180))

        table.setMinimumHeight(300)
        return table

    def _build_setter_calls_table(self) -> QWidget:
        table = QTableWidget(len(SETTER_CALLS), 3)
        table.setHorizontalHeaderLabels(["Codice", "Nome", "Descrizione"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 120)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for i, sc in enumerate(SETTER_CALLS):
            table.setItem(i, 0, QTableWidgetItem(sc.code))
            table.setItem(i, 1, QTableWidgetItem(sc.label))
            table.setItem(i, 2, QTableWidgetItem(sc.description))
            for col in range(3):
                item = table.item(i, col)
                if item:
                    item.setBackground(QColor(sc.color))

        table.setMinimumHeight(200)
        return table
