from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .curve import GRADE_THRESHOLDS, letter_grade

_GRADES = [grade for _, grade in GRADE_THRESHOLDS]  # A+ … F, in order


def _count_grades(scores: list[float]) -> dict[str, int]:
    counts: dict[str, int] = {g: 0 for g in _GRADES}
    for s in scores:
        counts[letter_grade(s)] += 1
    return counts


class GradeBreakdownWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(QLabel("Grade Distribution"))

        self._table = QTableWidget(len(_GRADES), 3)
        self._table.setHorizontalHeaderLabels(["Grade", "Before", "After"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        for row, grade in enumerate(_GRADES):
            g_item = QTableWidgetItem(grade)
            g_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, g_item)
            for col in (1, 2):
                item = QTableWidgetItem("—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._table)

    def update_counts(self, before: list[float], after: list[float]) -> None:
        before_counts = _count_grades(before)
        after_counts  = _count_grades(after)
        for row, grade in enumerate(_GRADES):
            self._table.item(row, 1).setText(str(before_counts[grade]))
            self._table.item(row, 2).setText(str(after_counts[grade]))
