import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUTS_DIR = ROOT / "outputs"
PUBLIC_DIR = ROOT / "public"

MAJOR_GROUPS = [
    {
        "id": "thai",
        "name": "กลุ่มวิชาภาษาไทย",
        "subjects": ["ภาษาไทย"],
    },
    {
        "id": "math",
        "name": "กลุ่มวิชาคณิตศาสตร์",
        "subjects": ["คณิตศาสตร์"],
    },
    {
        "id": "foreign",
        "name": "กลุ่มวิชาภาษาต่างประเทศ",
        "subjects": ["ภาษาอังกฤษ"],
    },
    {
        "id": "social",
        "name": "กลุ่มวิชาสังคมศึกษา ศาสนา และวัฒนธรรม",
        "subjects": ["สังคม ศาสนา และวัฒนธรรม"],
    },
    {
        "id": "science",
        "name": "กลุ่มวิชาวิทยาศาสตร์และเทคโนโลยี",
        "subjects": ["วิทยาศาสตร์", "วิทยาศาสตร์ทั่วไป", "ฟิสิกส์", "เคมี", "ชีววิทยา", "เทคโนโลยี", "คอมพิวเตอร์"],
    },
    {
        "id": "health",
        "name": "กลุ่มวิชาสุขศึกษาและพลศึกษา",
        "subjects": ["สุขศึกษา", "พลศึกษา"],
    },
    {
        "id": "art",
        "name": "กลุ่มวิชาศิลปศึกษา",
        "subjects": ["ทัศนศิลป์", "ดนตรี", "นาฏศิลป์"],
    },
    {
        "id": "career",
        "name": "กลุ่มวิชาการงานอาชีพ",
        "subjects": ["คหกรรม", "เกษตรกรรม", "อุตสาหกรรม", "วิชาชีพ/การงานอาชีพอื่นๆ"],
    },
]


def normalize_code(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def safe_int(value):
    if pd.isna(value):
        return 0
    return int(value)


def read_metrics():
    path = OUTPUTS_DIR / "ml_model_metrics.json"
    if not path.exists():
        return {
            "future_metrics": [],
            "risk_metrics": [],
            "future_best": {"model": "-"},
            "risk_best": {"model": "-"},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def subject_key(group_id, subject):
    return f"{group_id}::{subject}"


def main():
    schools = pd.read_excel(DATA_DIR / "schools.xlsx", dtype={"school_code": str, "area_code": str})
    analysis = pd.read_excel(DATA_DIR / "school_math_analysis.xlsx", sheet_name="school_math_analysis", dtype={"school_code": str})
    teachers = pd.read_excel(DATA_DIR / "teachers.xlsx", dtype={"school_code": str, "teacher_id": str})
    metrics = read_metrics()

    schools["school_code"] = schools["school_code"].map(normalize_code)
    analysis["school_code"] = analysis["school_code"].map(normalize_code)
    teachers["school_code"] = teachers["school_code"].map(normalize_code)
    teachers["subject_group_id"] = teachers["subject_group_id"].fillna("other")
    teachers["subject_group"] = teachers["subject_group"].fillna("ไม่เข้ากลุ่มมาตรฐาน")
    teachers["subject_major"] = teachers["subject_major"].fillna("ไม่ระบุ")
    teachers["teacher_id"] = teachers["teacher_id"].fillna("").map(normalize_code)
    teachers["teacher_major"] = teachers["teacher_major"].fillna("ไม่ระบุ")

    merged = schools.merge(analysis, on="school_code", how="left")
    merged["future_shortage_prediction"] = merged["future_shortage_prediction"].fillna(0).astype(int)
    merged["sudden_shortage_risk_level"] = merged["sudden_shortage_risk_level"].fillna("ไม่ระบุ")
    merged["actual_math_teachers"] = merged["actual_math_teachers"].fillna(0).astype(int)
    merged["calculated_min_math"] = merged["calculated_min_math"].fillna(0).astype(int)
    merged["math_gap"] = merged["actual_math_teachers"] - merged["calculated_min_math"]

    school_codes = set(merged["school_code"])
    teachers = teachers[teachers["school_code"].isin(school_codes)]
    school_teacher_counts = teachers.groupby("school_code").size().to_dict()
    teacher_group_counts = teachers.groupby(["school_code", "subject_group_id"]).size().to_dict()
    teacher_subject_counts = teachers.groupby(["school_code", "subject_group_id", "subject_major"]).size().to_dict()
    teacher_roster = defaultdict(list)
    for teacher in teachers.sort_values(["school_code", "subject_group", "subject_major", "teacher_id"]).to_dict(orient="records"):
        teacher_roster[normalize_code(teacher["school_code"])].append({
            "teacher_id": normalize_code(teacher.get("teacher_id")),
            "subject_group_id": normalize_code(teacher.get("subject_group_id")),
            "subject_group": teacher.get("subject_group", "ไม่ระบุ"),
            "subject_major": teacher.get("subject_major", "ไม่ระบุ"),
            "teacher_major": teacher.get("teacher_major", "ไม่ระบุ"),
        })

    subject_summary_map = {}
    group_summary = []
    total_shortage_slots = 0
    total_group_pairs = 0
    complete_group_pairs = 0

    for group in MAJOR_GROUPS:
        group_shortages = Counter()
        group_actual = 0
        group_required = 0
        complete_schools = 0
        partial_schools = 0
        missing_schools = 0

        for _, school in merged.iterrows():
            school_code = normalize_code(school["school_code"])
            has_records = school_teacher_counts.get(school_code, 0) > 0
            counts = {
                subject: int(teacher_subject_counts.get((school_code, group["id"], subject), 0))
                for subject in group["subjects"]
            }
            missing = [subject for subject, count in counts.items() if count == 0]
            actual = int(teacher_group_counts.get((school_code, group["id"]), 0))
            required = len(group["subjects"]) if has_records else 0

            group_actual += actual
            group_required += required
            total_shortage_slots += len(missing) if has_records else 0
            total_group_pairs += 1 if has_records else 0

            if not has_records:
                missing_schools += 1
            elif missing:
                partial_schools += 1
                group_shortages.update(missing)
            else:
                complete_schools += 1
                complete_group_pairs += 1

            for subject, count in counts.items():
                key = subject_key(group["id"], subject)
                if key not in subject_summary_map:
                    subject_summary_map[key] = {
                        "group_id": group["id"],
                        "group_name": group["name"],
                        "subject": subject,
                        "total_teachers": 0,
                        "schools_with_teacher": 0,
                        "shortage_schools": 0,
                    }
                subject_summary_map[key]["total_teachers"] += count
                if count > 0:
                    subject_summary_map[key]["schools_with_teacher"] += 1
                elif has_records:
                    subject_summary_map[key]["shortage_schools"] += 1

        group_summary.append({
            "group_id": group["id"],
            "group_name": group["name"],
            "subjects": group["subjects"],
            "actual_teachers": group_actual,
            "required_subject_slots": group_required,
            "shortage_subject_slots": sum(group_shortages.values()),
            "complete_schools": complete_schools,
            "partial_schools": partial_schools,
            "missing_record_schools": missing_schools,
            "top_shortage_subjects": [
                {"subject": subject, "schools": int(count)}
                for subject, count in group_shortages.most_common(5)
            ],
        })

    area_summary = []
    for area, group in merged.groupby("area_name"):
        area_school_codes = set(group["school_code"].map(normalize_code))
        area_teachers = teachers[teachers["school_code"].isin(area_school_codes)]
        area_summary.append({
            "area_name": area,
            "schools": int(len(group)),
            "teacher_records": int(len(area_teachers)),
            "covered_schools": int(sum(1 for code in area_school_codes if school_teacher_counts.get(code, 0) > 0)),
            "future_shortage_total": int(group["future_shortage_prediction"].sum()),
            "high_risk": int((group["sudden_shortage_risk_level"] == "สูง").sum()),
        })
    area_summary.sort(key=lambda row: row["area_name"])

    school_rows = []
    for row in merged.sort_values(["area_name", "school_name"]).to_dict(orient="records"):
        school_code = normalize_code(row["school_code"])
        has_records = school_teacher_counts.get(school_code, 0) > 0
        subject_groups = []
        all_missing_subjects = []
        for group in MAJOR_GROUPS:
            subject_rows = []
            missing_subjects = []
            for subject in group["subjects"]:
                count = int(teacher_subject_counts.get((school_code, group["id"], subject), 0))
                if has_records and count == 0:
                    missing_subjects.append(subject)
                subject_rows.append({
                    "subject": subject,
                    "teacher_count": count,
                    "status": "มี" if count > 0 else "ขาด" if has_records else "ไม่มีข้อมูล",
                })
            actual = int(teacher_group_counts.get((school_code, group["id"]), 0))
            all_missing_subjects.extend([f"{group['name']}: {subject}" for subject in missing_subjects])
            subject_groups.append({
                "group_id": group["id"],
                "group_name": group["name"],
                "actual_teachers": actual,
                "required_subjects": len(group["subjects"]) if has_records else 0,
                "covered_subjects": len(group["subjects"]) - len(missing_subjects) if has_records else 0,
                "missing_subjects": missing_subjects,
                "status": "ไม่มีข้อมูล" if not has_records else "ครบ" if not missing_subjects else "ขาดบางวิชา",
                "subjects": subject_rows,
            })

        school_rows.append({
            "school_code": school_code,
            "school_name": row["school_name"],
            "area_name": row["area_name"],
            "school_size": row["school_size"],
            "total_students": safe_int(row["total_students"]),
            "actual_teachers": safe_int(row["actual_teachers"]),
            "hired_teachers": safe_int(row["hired_teachers"]),
            "teacher_records": int(school_teacher_counts.get(school_code, 0)),
            "has_teacher_records": has_records,
            "calculated_min_math": safe_int(row["calculated_min_math"]),
            "actual_math_teachers": safe_int(row["actual_math_teachers"]),
            "math_gap": safe_int(row["math_gap"]),
            "current_math_status": row["current_math_status"],
            "future_shortage_prediction": safe_int(row["future_shortage_prediction"]),
            "sudden_shortage_risk_level": row["sudden_shortage_risk_level"],
            "subject_groups": subject_groups,
            "teacher_roster": teacher_roster.get(school_code, []),
            "missing_subject_preview": all_missing_subjects[:8],
        })

    status_counts = Counter(merged["current_math_status"])
    risk_counts = Counter(merged["sudden_shortage_risk_level"])
    top_subject_shortage = sorted(
        subject_summary_map.values(),
        key=lambda row: (row["shortage_schools"], row["total_teachers"]),
        reverse=True,
    )[:12]

    payload = {
        "generated_at": date.today().isoformat(),
        "version": "2.0",
        "taxonomy_source": "กลุ่มวิชาเอก.pdf",
        "overview": {
            "total_schools": int(len(merged)),
            "target_areas": int(merged["area_name"].nunique()),
            "total_students": int(merged["total_students"].sum()),
            "teacher_records": int(len(teachers)),
            "covered_schools": int(sum(1 for count in school_teacher_counts.values() if count > 0)),
            "official_major_groups": len(MAJOR_GROUPS),
            "official_subjects": sum(len(group["subjects"]) for group in MAJOR_GROUPS),
            "subject_shortage_slots": int(total_shortage_slots),
            "complete_group_school_pairs": int(complete_group_pairs),
            "total_group_school_pairs": int(total_group_pairs),
            "actual_math_teachers": int(merged["actual_math_teachers"].sum()),
            "required_math_teachers": int(merged["calculated_min_math"].sum()),
            "future_shortage_total": int(merged["future_shortage_prediction"].sum()),
            "high_risk_schools": int(risk_counts.get("สูง", 0)),
        },
        "major_groups": group_summary,
        "subject_summary": list(subject_summary_map.values()),
        "top_subject_shortage": top_subject_shortage,
        "area_summary": area_summary,
        "schools": school_rows,
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
        "teacher_record_coverage": {
            "teacher_rows": int(len(teachers)),
            "schools_with_teacher_records": int(sum(1 for count in school_teacher_counts.values() if count > 0)),
            "note": "Version 2 นับครูจากไฟล์ teachers.xlsx ตามกลุ่มวิชาเอกและวิชาเอกย่อยในกลุ่มวิชาเอก.pdf โรงเรียนที่ไม่มี record ครูจะไม่ถูกตัดสินว่าขาดรายวิชา",
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
