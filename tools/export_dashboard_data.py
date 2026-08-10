import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUTS_DIR = ROOT / "outputs"
PUBLIC_DIR = ROOT / "public"


def normalize_code(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def main():
    schools = pd.read_excel(DATA_DIR / "schools.xlsx", dtype={"school_code": str, "area_code": str})
    analysis = pd.read_excel(DATA_DIR / "school_math_analysis.xlsx", sheet_name="school_math_analysis", dtype={"school_code": str})
    teachers = pd.read_excel(DATA_DIR / "teachers.xlsx", dtype={"school_code": str, "teacher_id": str})
    metrics = json.loads((OUTPUTS_DIR / "ml_model_metrics.json").read_text(encoding="utf-8"))

    schools["school_code"] = schools["school_code"].map(normalize_code)
    analysis["school_code"] = analysis["school_code"].map(normalize_code)
    teachers["school_code"] = teachers["school_code"].map(normalize_code)

    merged = schools.merge(analysis, on="school_code", how="left")
    merged["future_shortage_prediction"] = merged["future_shortage_prediction"].fillna(0).astype(int)
    merged["sudden_shortage_risk_level"] = merged["sudden_shortage_risk_level"].fillna("ไม่ระบุ")
    merged["actual_math_teachers"] = merged["actual_math_teachers"].fillna(0).astype(int)
    merged["calculated_min_math"] = merged["calculated_min_math"].fillna(0).astype(int)
    merged["math_gap"] = merged["actual_math_teachers"] - merged["calculated_min_math"]

    status_counts = Counter(merged["current_math_status"])
    risk_counts = Counter(merged["sudden_shortage_risk_level"])
    area_summary = []
    for area, group in merged.groupby("area_name"):
        area_summary.append({
            "area_name": area,
            "schools": int(len(group)),
            "shortage": int((group["current_math_status"] == "ขาด").sum()),
            "met": int((group["current_math_status"] == "ตามเกณฑ์").sum()),
            "surplus": int((group["current_math_status"] == "เกิน").sum()),
            "future_shortage_total": int(group["future_shortage_prediction"].sum()),
            "high_risk": int((group["sudden_shortage_risk_level"] == "สูง").sum()),
            "actual_math_teachers": int(group["actual_math_teachers"].sum()),
            "required_math_teachers": int(group["calculated_min_math"].sum()),
        })
    area_summary.sort(key=lambda row: row["area_name"])

    school_rows = []
    for row in merged.sort_values(["area_name", "school_name"]).to_dict(orient="records"):
        school_rows.append({
            "school_code": normalize_code(row["school_code"]),
            "school_name": row["school_name"],
            "area_name": row["area_name"],
            "school_size": row["school_size"],
            "total_students": int(row["total_students"]),
            "actual_teachers": int(row["actual_teachers"]),
            "hired_teachers": int(row["hired_teachers"]),
            "calculated_min_math": int(row["calculated_min_math"]),
            "actual_math_teachers": int(row["actual_math_teachers"]),
            "math_gap": int(row["math_gap"]),
            "current_math_status": row["current_math_status"],
            "future_shortage_prediction": int(row["future_shortage_prediction"]),
            "sudden_shortage_risk_level": row["sudden_shortage_risk_level"],
        })

    teacher_counts = teachers.groupby("school_code").size().to_dict()
    top_future_shortage = sorted(
        school_rows,
        key=lambda row: (row["future_shortage_prediction"], row["calculated_min_math"], row["total_students"]),
        reverse=True,
    )[:10]
    top_risk = [
        row for row in school_rows
        if row["sudden_shortage_risk_level"] in {"สูง", "ปานกลาง"}
    ][:12]

    payload = {
        "generated_at": date.today().isoformat(),
        "overview": {
            "total_schools": int(len(merged)),
            "target_areas": int(merged["area_name"].nunique()),
            "total_students": int(merged["total_students"].sum()),
            "actual_math_teachers": int(merged["actual_math_teachers"].sum()),
            "required_math_teachers": int(merged["calculated_min_math"].sum()),
            "future_shortage_total": int(merged["future_shortage_prediction"].sum()),
            "high_risk_schools": int(risk_counts.get("สูง", 0)),
        },
        "status_counts": {
            "ขาด": int(status_counts.get("ขาด", 0)),
            "ตามเกณฑ์": int(status_counts.get("ตามเกณฑ์", 0)),
            "เกิน": int(status_counts.get("เกิน", 0)),
        },
        "risk_counts": {
            "สูง": int(risk_counts.get("สูง", 0)),
            "ปานกลาง": int(risk_counts.get("ปานกลาง", 0)),
            "ต่ำ": int(risk_counts.get("ต่ำ", 0)),
        },
        "area_summary": area_summary,
        "schools": school_rows,
        "top_future_shortage": top_future_shortage,
        "top_risk": top_risk,
        "teacher_record_coverage": {
            "teacher_rows": int(len(teachers)),
            "schools_with_teacher_records": int(len(teacher_counts)),
            "note": "ไฟล์ teachers.xlsx มีข้อมูลครูคณิตศาสตร์รายบุคคลจาก 4 สพม. ในพื้นที่เป้าหมาย",
        },
        "metrics": {
            "future": metrics["future_metrics"],
            "risk": metrics["risk_metrics"],
            "future_best": metrics["future_best"],
            "risk_best": metrics["risk_best"],
        },
    }

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DIR / "dashboard-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["overview"], ensure_ascii=False))


if __name__ == "__main__":
    main()
