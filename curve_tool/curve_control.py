from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QWidget


class CurveControl(QWidget):
    """Curve editor: two-point linear interpolation plus optional quadratic term.

    Emits curveChanged(x1, y1, x2, y2, coeff) whenever any value changes.
    """

    curveChanged = Signal(float, float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        def pct_spin(default: float) -> QDoubleSpinBox:
            s = QDoubleSpinBox()
            s.setRange(0.0, 150.0)
            s.setDecimals(1)
            s.setSingleStep(1.0)
            s.setSuffix(" %")
            s.setValue(default)
            s.setFixedWidth(90)
            return s

        layout.addWidget(QLabel("Point 1 — raw:"))
        self._x1 = pct_spin(0.0)
        layout.addWidget(self._x1)
        layout.addWidget(QLabel("→ curved:"))
        self._y1 = pct_spin(0.0)
        layout.addWidget(self._y1)

        layout.addSpacing(24)

        layout.addWidget(QLabel("Point 2 — raw:"))
        self._x2 = pct_spin(100.0)
        layout.addWidget(self._x2)
        layout.addWidget(QLabel("→ curved:"))
        self._y2 = pct_spin(100.0)
        layout.addWidget(self._y2)

        layout.addSpacing(24)

        layout.addWidget(QLabel("Quadratic:"))
        self._coeff = QDoubleSpinBox()
        self._coeff.setRange(-0.02, 0.02)
        self._coeff.setDecimals(4)
        self._coeff.setSingleStep(0.001)
        self._coeff.setValue(0.0)
        self._coeff.setFixedWidth(90)
        layout.addWidget(self._coeff)

        layout.addStretch()

        for s in (self._x1, self._y1, self._x2, self._y2, self._coeff):
            s.valueChanged.connect(self._emit)

    def _emit(self) -> None:
        self.curveChanged.emit(
            self._x1.value(), self._y1.value(),
            self._x2.value(), self._y2.value(),
            self._coeff.value(),
        )

    def params(self) -> tuple[float, float, float, float, float]:
        return (
            self._x1.value(), self._y1.value(),
            self._x2.value(), self._y2.value(),
            self._coeff.value(),
        )

    def set_points(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        coeff: float = 0.0,
    ) -> None:
        """Set all curve values without triggering intermediate redraws."""
        for spin, val in zip(
            (self._x1, self._y1, self._x2, self._y2, self._coeff),
            (x1, y1, x2, y2, coeff),
        ):
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)
