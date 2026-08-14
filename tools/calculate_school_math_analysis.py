import json
from collections import Counter
from pathlib import Path

import openpyxl


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TMP_DIR = ROOT / "outputs" / "tmp"
SCHOOLS_PATH = DATA_DIR / "schools.xlsx"
TEACHERS_PATH = DATA_DIR / "teachers.xlsx"
PAYLOAD_PATH = TMP_DIR / "school_math_analysis_payload.json"


RULES = [
    (1, 19, 1),
    (20, 28, 2),
    (29, 38, 2),
    (39, 48, 3),
    (49, 58, 4),
    (59, 67, 5),
    (68, 77, 6),
    (78, 87, 7),
    (88, 97, 7),
    (98, 106, 8),
    (107, 116, 9),
    (117, 126, 10),
    (127, 136, 11),
    (137, 145, 11),
    (146, 155, 12),
    (156, 165, 13),
    (166, 175, 14),
    (176, 184, 15),
    (185, 194, 15),
    (195, 204, 16),
    (205, 214, 17),
    (215, 223, 18),
    (224, 233, 19),
    (234, None, 20),
]


def normalize_code(value):
    if value is None:
        return ""
    return str(value).strip()


def to_int(value):
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    return int(float(str(value).replace(",", "").strip()))


def minimum_math_teachers(actual_teachers):
    if actual_teachers <= 0:
        return 0
    for lower, upper, minimum in RULES:
        if actual_teachers >= lower and (upper is None or actual_teachers <= upper):
            return minimum
    return 0


def load_records(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [str(value).strip() for value in next(rows)]
    records = []
    for row in rows:
        if not any(value is not None and str(value).strip() for value in row):
            continue
        records.append({headers[index]: row[index] if index < len(row) else None for index in range(len(headers))})
    return records


def main():
    schools = load_records(SCHOOLS_PATH)
    teachers = load_records(TEACHERS_PATH)
    math_counts = Counter(
        normalize_code(row.get("school_code"))
        for row in teachers
        if normalize_code(row.get("subject_group_id")) == "math" or "คณิต" in normalize_code(row.get("teacher_major"))
    )

    analysis_rows = []
    for school in schools:
        school_code = normalize_code(school.get("school_code"))
        actual_teachers = to_int(school.get("actual_teachers"))
        calculated_min_math = minimum_math_teachers(actual_teachers)
        actual_math_teachers = math_counts.get(school_code, 0)
        variance = actual_math_teachers - calculated_min_math
        status = "ขาด" if variance < 0 else "เกิน" if variance > 0 else "ตามเกณฑ์"
        analysis_rows.append({
            "school_code": school_code,
            "calculated_min_math": calculated_min_math,
            "actual_math_teachers": actual_math_teachers,
            "current_math_status": status,
            "future_shortage_prediction": "",
            "sudden_shortage_risk_level": "",
        })

    summary = Counter(row["current_math_status"] for row in analysis_rows)
    payload = {
        "analysis": analysis_rows,
        "summary": {
            "total_schools": len(analysis_rows),
            "shortage": summary.get("ขาด", 0),
            "met": summary.get("ตามเกณฑ์", 0),
            "surplus": summary.get("เกิน", 0),
        },
        "rules": [
            {
                "actual_teachers_min": lower,
                "actual_teachers_max": upper,
                "calculated_min_math": minimum,
            }
            for lower, upper, minimum in RULES
        ],
    }
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    PAYLOAD_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
