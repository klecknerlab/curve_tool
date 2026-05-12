# curve_tool

A desktop utility for applying grade curves to exam scores exported from Canvas (or any
gradebook CSV with a similar layout).

## What it does

- **Open a CSV** — supports Canvas gradebook exports; you pick which column is the student
  name and which columns are the raw problem scores
- **Score histogram** — shows the distribution before and after the curve, with adjustable
  bin width
- **Grade curve** — two-point linear interpolation with an optional quadratic term; adjust
  the curve live and both the histogram and table update immediately
- **Grade table** — sortable table showing each student's raw score, curved score,
  adjustment, and letter grade (A+ through F)
- **Grade distribution** — per-letter-grade counts (before and after) displayed next to
  the histograms
- **Export** — save curved scores to a CSV, histogram plots as a PNG, or summary
  statistics (mean ± std dev per problem and overall) as a TXT file; **Export All**
  saves all three at once from a single filename prompt; statistics can also be copied
  to the clipboard
- **Drag and drop** — drag a CSV file directly onto the window to open it

## Install

Requires [Anaconda](https://www.anaconda.com/download) (or Miniconda).

Install dependencies, then install the package:

```bash
conda install matplotlib numpy
conda install -c conda-forge pyside6
pip install -e .
```

## Run

After installing:

```bash
curve-tool
```

Or run directly from the source tree without installing:

```bash
python -m curve_tool
```
