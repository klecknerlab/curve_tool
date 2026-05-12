import csv
from dataclasses import dataclass


@dataclass
class StudentRecord:
    name: str
    raw_scores: list[float]
    max_scores: list[float]

    @property
    def raw_pct(self) -> float:
        total_max = sum(self.max_scores)
        if total_max == 0:
            return 0.0
        return sum(self.raw_scores) / total_max * 100.0


_TEST_STUDENT_NAMES = {"student, test", "test student", "test, student"}


def _is_test_student(name: str) -> bool:
    return name.strip().lower() in _TEST_STUDENT_NAMES


def load_csv(
    path: str, name_col: int, score_cols: list[int]
) -> tuple[list[str], list[StudentRecord]]:
    """Load a Canvas-style CSV. Row 0 = headers, row 1 = max scores, row 2+ = students."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if len(rows) < 3:
        raise ValueError("CSV needs at least 3 rows (header, points possible, student data)")

    headers = rows[0]
    max_row = rows[1]

    max_scores: list[float] = []
    for col in score_cols:
        try:
            val = max_row[col].strip() if col < len(max_row) else ""
            max_scores.append(float(val) if val else 0.0)
        except ValueError:
            max_scores.append(0.0)

    records: list[StudentRecord] = []
    for row in rows[2:]:
        if not any(cell.strip() for cell in row):
            continue
        name = row[name_col].strip() if name_col < len(row) else ""
        if _is_test_student(name):
            continue
        raw_scores: list[float] = []
        for col in score_cols:
            try:
                val = row[col].strip() if col < len(row) else ""
                raw_scores.append(float(val) if val else 0.0)
            except ValueError:
                raw_scores.append(0.0)
        records.append(StudentRecord(name=name, raw_scores=raw_scores, max_scores=max_scores))

    return headers, records
