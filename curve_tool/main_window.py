import csv
import os
import statistics

from matplotlib.figure import Figure as MplFigure

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .column_dialog import ColumnDialog
from .curve import apply_curve
from .curve_control import CurveControl
from .data import StudentRecord, load_csv
from .grade_breakdown import GradeBreakdownWidget
from .grade_table import GradeTable
from .histogram_widget import HistogramWidget
from .stats import build_stats_text


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Curve Tool")
        self.resize(1100, 800)
        self.setAcceptDrops(True)
        self._records: list[StudentRecord] = []
        self._score_headers: list[str] = []
        self._build_ui()
        self._build_toolbar()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # --- histograms ---
        self._hist_before = HistogramWidget("Before Curve", QColor("#4A90D9"))
        self._hist_after = HistogramWidget("After Curve", QColor("#E8823A"))

        self._grade_breakdown = GradeBreakdownWidget()

        hist_layout = QHBoxLayout()
        hist_layout.addWidget(self._hist_before)
        hist_layout.addWidget(self._hist_after)
        hist_layout.addWidget(self._grade_breakdown)

        bin_row = QHBoxLayout()
        bin_row.addStretch()
        bin_row.addWidget(QLabel("Bin width:"))
        self._bin_spin = QSpinBox()
        self._bin_spin.setRange(1, 25)
        self._bin_spin.setValue(5)
        self._bin_spin.setSuffix(" %")
        self._bin_spin.setFixedWidth(72)
        bin_row.addWidget(self._bin_spin)

        hist_widget = QWidget()
        hw_layout = QVBoxLayout(hist_widget)
        hw_layout.setContentsMargins(0, 0, 0, 0)
        hw_layout.setSpacing(2)
        hw_layout.addLayout(bin_row)
        hw_layout.addLayout(hist_layout)

        # --- curve control ---
        curve_group = QGroupBox("Curve  (linear interpolation through two points)")
        self._curve_ctrl = CurveControl()
        self._cap_check = QCheckBox("Cap curved scores at 100%")
        gl = QVBoxLayout(curve_group)
        gl.setContentsMargins(8, 4, 8, 6)
        gl.setSpacing(4)
        gl.addWidget(self._curve_ctrl)
        gl.addWidget(self._cap_check)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(hist_widget, stretch=3)
        top_layout.addWidget(curve_group, stretch=0)

        # --- grade table ---
        self._table = GradeTable()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top_widget)
        splitter.addWidget(self._table)
        splitter.setSizes([480, 320])

        main_layout.addWidget(splitter)

        self._curve_ctrl.curveChanged.connect(self._on_curve_changed)
        self._bin_spin.valueChanged.connect(self._on_bin_width_changed)
        self._cap_check.stateChanged.connect(self._on_cap_changed)

    def _build_toolbar(self) -> None:
        tb = self.addToolBar("Main")
        tb.setMovable(False)

        open_act = QAction("Open CSV…", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_csv)
        tb.addAction(open_act)

        tb.addSeparator()

        save_act = QAction("Save CSV…", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._save_csv)
        tb.addAction(save_act)

        png_act = QAction("Export PNG…", self)
        png_act.triggered.connect(self._export_png)
        tb.addAction(png_act)

        stats_act = QAction("Export Statistics…", self)
        stats_act.triggered.connect(self._export_stats)
        tb.addAction(stats_act)

        all_act = QAction("Export All…", self)
        all_act.setShortcut("Ctrl+Shift+S")
        all_act.triggered.connect(self._export_all)
        tb.addAction(all_act)

        tb.addSeparator()

        copy_act = QAction("Copy Statistics", self)
        copy_act.setShortcut("Ctrl+Shift+C")
        copy_act.triggered.connect(self._copy_stats)
        tb.addAction(copy_act)

    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith(".csv"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        path = event.mimeData().urls()[0].toLocalFile()
        self._load_file(path)

    def _open_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV files (*.csv);;All files (*)"
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        with open(path, newline="", encoding="utf-8-sig") as f:
            headers = next(csv.reader(f))

        dlg = ColumnDialog(headers, self)
        if dlg.exec() != ColumnDialog.DialogCode.Accepted:
            return

        score_cols = dlg.score_cols
        if not score_cols:
            QMessageBox.warning(self, "No Score Columns", "Please check at least one score column.")
            return

        try:
            _, self._records = load_csv(path, dlg.name_col, score_cols)
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", str(exc))
            return

        self._score_headers = [headers[i] for i in score_cols]
        self._apply_smart_defaults()
        self._refresh_all()

    def _apply_smart_defaults(self) -> None:
        if not self._records:
            return
        raw_scores = [r.raw_pct for r in self._records]
        median_raw = round(statistics.median(raw_scores), 1)
        max_raw = round(max(raw_scores), 1)
        self._curve_ctrl.set_points(median_raw, 80.0, max_raw, 100.0)

    # --- writers (no dialogs, no guard checks) -------------------------

    def _write_csv(self, path: str) -> None:
        x1, y1, x2, y2, coeff = self._curve_ctrl.params()
        cap = self._cap_check.isChecked()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Raw %", "Curved %", "Adjustment"])
            for rec in self._records:
                raw = rec.raw_pct
                curved = apply_curve(raw, x1, y1, x2, y2, coeff)
                if cap:
                    curved = min(curved, 100.0)
                writer.writerow([rec.name, f"{raw:.2f}", f"{curved:.2f}", f"{curved - raw:.2f}"])

    def _write_png(self, path: str) -> None:
        fig = MplFigure(figsize=(12, 4), constrained_layout=True)
        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)
        self._hist_before.draw_to_axes(ax1)
        self._hist_after.draw_to_axes(ax2)
        fig.savefig(path, dpi=150)

    def _write_stats(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._stats_text())

    def _stats_text(self) -> str:
        x1, y1, x2, y2, coeff = self._curve_ctrl.params()
        return build_stats_text(
            self._records, self._score_headers,
            x1, y1, x2, y2, coeff,
            self._cap_check.isChecked(),
        )

    # --- dialog-based export actions -----------------------------------

    def _no_data_warning(self) -> bool:
        if not self._records:
            QMessageBox.warning(self, "No Data", "Open a CSV file first.")
            return True
        return False

    def _save_csv(self) -> None:
        if self._no_data_warning():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "CSV files (*.csv);;All files (*)"
        )
        if not path:
            return
        self._write_csv(path)
        QMessageBox.information(self, "Saved", f"Results saved to:\n{path}")

    def _export_png(self) -> None:
        if self._no_data_warning():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Histograms", "", "PNG images (*.png);;All files (*)"
        )
        if not path:
            return
        self._write_png(path)
        QMessageBox.information(self, "Exported", f"Histograms saved to:\n{path}")

    def _export_stats(self) -> None:
        if self._no_data_warning():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Statistics", "", "Text files (*.txt);;All files (*)"
        )
        if not path:
            return
        self._write_stats(path)
        QMessageBox.information(self, "Exported", f"Statistics saved to:\n{path}")

    def _export_all(self) -> None:
        if self._no_data_warning():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export All  (extensions added automatically)", "", "All files (*)"
        )
        if not path:
            return
        base = os.path.splitext(path)[0]
        self._write_csv(f"{base}.csv")
        self._write_png(f"{base}.png")
        self._write_stats(f"{base}.txt")
        QMessageBox.information(
            self, "Exported",
            f"Saved:\n  {base}.csv\n  {base}.png\n  {base}.txt"
        )

    def _copy_stats(self) -> None:
        if self._no_data_warning():
            return
        QApplication.clipboard().setText(self._stats_text())

    # ------------------------------------------------------------------
    def _refresh_all(self) -> None:
        x1, y1, x2, y2, coeff = self._curve_ctrl.params()
        cap = self._cap_check.isChecked()
        raw = [r.raw_pct for r in self._records]
        curved = self._curved(raw, x1, y1, x2, y2, coeff, cap)
        self._hist_before.update_scores(raw)
        self._hist_after.update_scores(curved)
        self._grade_breakdown.update_counts(raw, curved)
        self._table.update_data(self._records, x1, y1, x2, y2, coeff, cap)

    def _on_bin_width_changed(self, width: int) -> None:
        self._hist_before.set_bin_width(float(width))
        self._hist_after.set_bin_width(float(width))

    def _on_curve_changed(self, x1: float, y1: float, x2: float, y2: float, coeff: float) -> None:
        if not self._records:
            return
        cap = self._cap_check.isChecked()
        raw = [r.raw_pct for r in self._records]
        curved = self._curved(raw, x1, y1, x2, y2, coeff, cap)
        self._hist_after.update_scores(curved)
        self._grade_breakdown.update_counts(raw, curved)
        self._table.update_data(self._records, x1, y1, x2, y2, coeff, cap)

    def _on_cap_changed(self) -> None:
        if not self._records:
            return
        x1, y1, x2, y2, coeff = self._curve_ctrl.params()
        self._on_curve_changed(x1, y1, x2, y2, coeff)

    @staticmethod
    def _curved(
        raw: list[float],
        x1: float, y1: float,
        x2: float, y2: float,
        coeff: float,
        cap: bool,
    ) -> list[float]:
        scores = [apply_curve(s, x1, y1, x2, y2, coeff) for s in raw]
        if cap:
            scores = [min(s, 100.0) for s in scores]
        return scores
