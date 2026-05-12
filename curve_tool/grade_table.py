from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from .curve import apply_curve, letter_grade
from .data import StudentRecord


class _NumericItem(QTableWidgetItem):
    """Table item that sorts by a numeric UserRole value instead of display text."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            return float(self.data(Qt.ItemDataRole.UserRole)) < float(
                other.data(Qt.ItemDataRole.UserRole)
            )
        except (TypeError, ValueError):
            return super().__lt__(other)


class GradeTable(QTableWidget):
    _HEADERS = ["Name", "Raw %", "Curved %", "Adjustment", "Grade"]

    def __init__(self, parent=None):
        super().__init__(0, len(self._HEADERS), parent)
        self.setHorizontalHeaderLabels(self._HEADERS)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(self._HEADERS)):
            hh.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def update_data(
        self,
        records: list[StudentRecord],
        x1: float, y1: float,
        x2: float, y2: float,
        coeff: float = 0.0,
        cap: bool = False,
    ) -> None:
        self.setSortingEnabled(False)
        self.setRowCount(len(records))

        for row, rec in enumerate(records):
            raw = rec.raw_pct
            curved = apply_curve(raw, x1, y1, x2, y2, coeff)
            if cap:
                curved = min(curved, 100.0)
            adj = curved - raw
            grade = letter_grade(curved)

            self.setItem(row, 0, QTableWidgetItem(rec.name))

            for col, val in enumerate([raw, curved, adj], start=1):
                item = _NumericItem(f"{val:+.1f}%" if col == 3 else f"{val:.1f}%")
                item.setData(Qt.ItemDataRole.UserRole, val)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.setItem(row, col, item)

            grade_item = _NumericItem(grade)
            grade_item.setData(Qt.ItemDataRole.UserRole, curved)
            grade_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 4, grade_item)

        self.setSortingEnabled(True)
