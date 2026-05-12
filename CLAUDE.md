# curve_tool — developer notes

## What this is

A PySide6 desktop app for applying grade curves to exam scores exported from Canvas.
Functional; early-stage UI.

## Stack

- **PySide6** — Qt6 widgets, signals/slots
- **matplotlib + numpy** — histograms embedded via `FigureCanvasQTAgg`
- **Python 3.10+**, otherwise stdlib only (no pandas)
- Packaged with `pyproject.toml`; entry point `curve-tool` → `curve_tool.cli:main`

## Running

```bash
python -m curve_tool          # from the repo root, no install needed
curve-tool                    # after: pip install -e .
```

## CSV format expected

Canvas gradebook export:
- **Row 1**: column headers (`Student`, `Problem 1 (...)`, etc.)
- **Row 2**: `Points Possible` — max score per column (used to normalise to %)
- **Row 3+**: one student per row; rows named `Student, Test` / `Test Student` are silently skipped

The user selects which column is the name and which columns are scores via a dialog on open.
Files can also be opened by dragging a CSV onto the window.

Total raw score = `sum(raw_scores) / sum(max_scores) × 100` (percentage; can exceed 100 for extra credit).

## Curve model

Two-point linear interpolation plus optional quadratic term.  User supplies `(x1, y1)` and
`(x2, y2)` in percentage space, and an optional quadratic coefficient `c`:

```
curved = y1 + (y2 - y1) * (s - x1) / (x2 - x1)  +  c * (s - x1)²
```

The quadratic term is zero at Point 1 regardless of `c`, so `(x1, y1)` is always on the curve.
The curve extrapolates outside `[x1, x2]`.

**Smart defaults** when a file loads: Point 1 = (median raw → 80%), Point 2 = (max raw → 100%).

An optional **cap** clamps all curved scores to 100% before grading or export.

The **adjustment** saved to the output CSV is `curved − raw` (percentage points to add).

## Grade scale

Standard ± scale, lower-bound inclusive:
`A+≥97, A≥93, A-≥90, B+≥87, B≥83, B-≥80, C+≥77, C≥73, C-≥70, D+≥67, D≥63, D-≥60, F<60`

## Module map

| File | Purpose |
|---|---|
| `cli.py` | Entry point — creates `QApplication` + `MainWindow` |
| `main_window.py` | Top-level window: toolbar, layout, all signal wiring |
| `data.py` | `load_csv()` → `list[StudentRecord]`; `StudentRecord.raw_pct` property; test-student filter |
| `curve.py` | `apply_curve()` (linear + quadratic), `letter_grade()`, `GRADE_THRESHOLDS` |
| `column_dialog.py` | Modal dialog for picking name column + score columns |
| `histogram_widget.py` | `HistogramWidget` — matplotlib histogram embedded in Qt; adjustable bin width; `draw_to_axes()` for PNG export |
| `curve_control.py` | `CurveControl` — five spinboxes (x1,y1,x2,y2,coeff), emits `curveChanged`; `set_points()` for programmatic update |
| `grade_table.py` | `GradeTable` — sortable `QTableWidget`: Name / Raw % / Curved % / Adjustment / Grade |
| `grade_breakdown.py` | `GradeBreakdownWidget` — compact Before/After count table for each letter grade |
| `stats.py` | `build_stats_text()` — plain-text statistics report (per-problem mean±std, totals, curve formula) |

## Export actions

| Action | Shortcut | Output |
|---|---|---|
| Save CSV… | Ctrl+S | Curved scores + adjustments |
| Export PNG… | — | Side-by-side histogram figure (150 dpi) |
| Export Statistics… | — | Plain-text report (.txt) |
| Export All… | Ctrl+Shift+S | All three from one base filename prompt |
| Copy Statistics | Ctrl+Shift+C | Statistics text to clipboard |

`_export_all` strips any extension from the chosen path with `os.path.splitext`, then appends `.csv`, `.png`, `.txt` and calls the three `_write_*` helpers directly.

## Key design decisions

- **matplotlib via `FigureCanvasQTAgg`** — histograms are proper matplotlib figures; `draw_to_axes()` lets PNG export reuse the same drawing code without touching the live canvas
- **`HistogramWidget` stores its own scores** — `set_bin_width()` can redraw without the caller re-supplying data
- **`_NumericItem`** subclasses `QTableWidgetItem.__lt__` using `UserRole` float so score/grade columns sort numerically, not lexicographically
- **`CurveControl.set_points()`** blocks signals on all spinboxes while setting values to avoid N intermediate redraws; caller owns the single `_refresh_all()` call after
- **`_curved()` static helper** in `MainWindow` centralises cap logic so it is applied consistently across `_refresh_all`, `_on_curve_changed`, and `_save_csv`
- The "before" histogram only updates on file load; the "after" histogram, grade breakdown, and table update on every curve or cap change
- Output CSV columns: `Name, Raw %, Curved %, Adjustment`
