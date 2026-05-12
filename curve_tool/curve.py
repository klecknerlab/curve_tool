GRADE_THRESHOLDS = [
    (97.0, "A+"),
    (93.0, "A"),
    (90.0, "A-"),
    (87.0, "B+"),
    (83.0, "B"),
    (80.0, "B-"),
    (77.0, "C+"),
    (73.0, "C"),
    (70.0, "C-"),
    (67.0, "D+"),
    (63.0, "D"),
    (60.0, "D-"),
    (0.0,  "F"),
]


def apply_curve(
    score: float,
    x1: float, y1: float,
    x2: float, y2: float,
    coeff: float = 0.0,
) -> float:
    """Linear interpolation through (x1,y1)-(x2,y2) plus optional quadratic term.

    The quadratic delta is coeff*(score-x1)^2, so it contributes zero at Point 1
    and grows with distance from it.
    """
    if abs(x2 - x1) < 1e-9:
        linear = y1
    else:
        linear = y1 + (y2 - y1) * (score - x1) / (x2 - x1)
    return linear + coeff * (score - x1) ** 2


def letter_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"
