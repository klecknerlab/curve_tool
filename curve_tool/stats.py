import statistics as _stats

from .curve import apply_curve
from .data import StudentRecord


def _mean_std(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = _stats.mean(values)
    std = _stats.stdev(values) if n >= 2 else 0.0
    return mean, std


def build_stats_text(
    records: list[StudentRecord],
    score_headers: list[str],
    x1: float, y1: float,
    x2: float, y2: float,
    coeff: float,
    cap: bool,
) -> str:
    lines: list[str] = []
    n = len(records)

    lines.append("Curve Tool Statistics")
    lines.append("=" * 44)
    lines.append("")

    # --- curve ---
    lines.append("Curve:")
    lines.append(f"  Point 1 :  raw {x1:.1f}% → curved {y1:.1f}%")
    lines.append(f"  Point 2 :  raw {x2:.1f}% → curved {y2:.1f}%")
    dx = x2 - x1
    if abs(dx) > 1e-9:
        slope = (y2 - y1) / dx
        lines.append(
            f"  Formula :  curved = {y1:.2f} + {slope:.4f} × (score − {x1:.1f})"
        )
        if coeff != 0.0:
            lines[-1] += f" + {coeff:.4f} × (score − {x1:.1f})²"
    else:
        lines.append(f"  Formula :  curved = {y1:.2f}  (degenerate: x1 == x2)")
        if coeff != 0.0:
            lines[-1] += f" + {coeff:.4f} × (score − {x1:.1f})²"
    if coeff != 0.0:
        lines.append(f"  Quadratic: {coeff:.4f}")
    lines.append(f"  Cap 100% : {'Yes' if cap else 'No'}")
    lines.append("")

    # --- per-problem ---
    if records and records[0].raw_scores:
        n_probs = len(records[0].raw_scores)
        col_w = max((len(h) for h in score_headers[:n_probs]), default=10)

        lines.append(f"Per-Problem Scores  (n = {n}):")
        for i in range(n_probs):
            header = score_headers[i] if i < len(score_headers) else f"Problem {i + 1}"
            max_s = records[0].max_scores[i]
            raw_vals = [r.raw_scores[i] for r in records]
            mean, std = _mean_std(raw_vals)
            pct_mean = mean / max_s * 100.0 if max_s else 0.0
            pct_std  = std  / max_s * 100.0 if max_s else 0.0
            lines.append(
                f"  {header:<{col_w}}  max {max_s:>5.1f} pts"
                f"    {mean:>6.2f} ± {std:>5.2f} pts"
                f"    ({pct_mean:>5.1f}% ± {pct_std:>4.1f}%)"
            )
        lines.append("")

    # --- totals ---
    raw_pcts = [r.raw_pct for r in records]
    curved = [apply_curve(s, x1, y1, x2, y2, coeff) for s in raw_pcts]
    if cap:
        curved = [min(s, 100.0) for s in curved]

    raw_mean, raw_std = _mean_std(raw_pcts)
    cur_mean, cur_std = _mean_std(curved)

    lines.append(f"Total Score  (n = {n}):")
    lines.append(f"  Raw    :  {raw_mean:.2f}% ± {raw_std:.2f}%")
    lines.append(f"  Curved :  {cur_mean:.2f}% ± {cur_std:.2f}%")
    lines.append("")

    return "\n".join(lines)
