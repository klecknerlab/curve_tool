import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget


class HistogramWidget(QWidget):
    def __init__(self, title: str, color: QColor, parent=None):
        super().__init__(parent)
        self._title = title
        self._color = color.name()  # matplotlib accepts "#rrggbb"
        self._scores: list[float] = []
        self._bin_width: float = 5.0

        self._fig = Figure(constrained_layout=True)
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._setup_axes(self._ax)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

    def _setup_axes(self, ax: Axes) -> None:
        ax.set_title(self._title)
        ax.set_xlabel("Score (%)")
        ax.set_ylabel("Students")
        ax.set_xlim(0, 100)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    def update_scores(self, scores: list[float]) -> None:
        self._scores = scores
        self._redraw()

    def set_bin_width(self, width: float) -> None:
        self._bin_width = width
        self._redraw()

    def draw_to_axes(self, ax: Axes) -> None:
        """Render the current histogram onto an external Axes (used for PNG export)."""
        self._setup_axes(ax)
        self._plot(ax)

    def _redraw(self) -> None:
        self._ax.clear()
        self._setup_axes(self._ax)
        self._plot(self._ax)
        self._canvas.draw()

    def _plot(self, ax: Axes) -> None:
        if self._scores:
            arr = np.clip(np.array(self._scores, dtype=float), 0.0, 100.0)
            bins = np.arange(0, 100 + self._bin_width, self._bin_width)
            ax.hist(arr, bins=bins, color=self._color, edgecolor="white", linewidth=0.5)
