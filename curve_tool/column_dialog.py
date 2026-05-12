from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class ColumnDialog(QDialog):
    """Modal dialog for choosing the name column and one or more score columns."""

    def __init__(self, headers: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Columns")
        self.setMinimumSize(640, 420)
        self._setup_ui(headers)

    def _setup_ui(self, headers: list[str]) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Select the name column (left) and score columns to sum (right):")
        )

        cols_layout = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel("Name column:"))
        self._name_list = QListWidget()
        for i, h in enumerate(headers):
            self._name_list.addItem(f"{i}: {h}")
        if self._name_list.count() > 0:
            self._name_list.setCurrentRow(0)
        left.addWidget(self._name_list)
        cols_layout.addLayout(left)

        right = QVBoxLayout()
        right.addWidget(QLabel("Score columns (check all that apply):"))
        self._score_list = QListWidget()
        for i, h in enumerate(headers):
            item = QListWidgetItem(f"{i}: {h}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._score_list.addItem(item)
        right.addWidget(self._score_list)
        cols_layout.addLayout(right)

        layout.addLayout(cols_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def name_col(self) -> int:
        return max(0, self._name_list.currentRow())

    @property
    def score_cols(self) -> list[int]:
        return [
            i
            for i in range(self._score_list.count())
            if self._score_list.item(i).checkState() == Qt.CheckState.Checked
        ]
