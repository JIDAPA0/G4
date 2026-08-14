import json
import re
from pathlib import Path

import openpyxl


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_SCHOOLS_PATH = DATA_DIR / "รวม 10 มิย 69.xlsx"
RAW_TEACHERS_PATH = DATA_DIR / "ครูมัธยมในพื้นที่ จ.พะเยา.xlsx"
OUT_JSON = DATA_DIR / "transformed_payload.json"

TARGET_AREAS = {"สพม.นนทบุรี", "สพม.พะเยา", "สพม.หนองคาย", "สพม.เชียงราย"}

MAJOR_TAXONOMY = [
    ("thai", "กลุ่มวิชาภาษาไทย", ["ภาษาไทย"]),
    ("math", "กลุ่มวิชาคณิตศาสตร์", ["คณิตศาสตร์"]),
    ("foreign", "กลุ่มวิชาภาษาต่างประเทศ", ["ภาษาอังกฤษ"]),
    ("social", "กลุ่มวิชาสังคมศึกษา ศาสนา และวัฒนธรรม", ["สังคม ศาสนา และวัฒนธรรม"]),
    (
        "science",
        "กลุ่มวิชาวิทยาศาสตร์และเทคโนโลยี",
        ["วิทยาศาสตร์", "วิทยาศาสตร์ทั่วไป", "ฟิสิกส์", "เคมี", "ชีววิทยา", "เทคโนโลยี", "คอมพิวเตอร์"],
    ),
    ("health", "กลุ่มวิชาสุขศึกษาและพลศึกษา", ["สุขศึกษา", "พลศึกษา"]),
    ("art", "กลุ่มวิชาศิลปศึกษา", ["ทัศนศิลป์", "ดนตรี", "นาฏศิลป์"]),
    ("career", "กลุ่มวิชาการงานอาชีพ", ["คหกรรม", "เกษตรกรรม", "อุตสาหกรรม", "วิชาชีพ/การงานอาชีพอื่นๆ"]),
]

SUBJECT_ALIASES = {
    "ภาษาไทย": ["ภาษาไทย"],
    "คณิตศาสตร์": ["คณิต", "สถิติ"],
    "ภาษาอังกฤษ": ["ภาษาอังกฤษ", "อังกฤษ"],
    "สังคม ศาสนา และวัฒนธรรม": ["สังคม", "ศาสนา", "วัฒนธรรม", "ภูมิศาสตร์", "ประวัติศาสตร์"],
    "วิทยาศาสตร์ทั่วไป": ["วิทยาศาสตร์ทั่วไป", "วิทย์ทั่วไป"],
    "วิทยาศาสตร์": ["วิทยาศาสตร์"],
    "ฟิสิกส์": ["ฟิสิกส์"],
    "เคมี": ["เคมี"],
    "ชีววิทยา": ["ชีววิทยา", "ชีวะ"],
    "เทคโนโลยี": ["เทคโนโลยี"],
    "คอมพิวเตอร์": ["คอมพิวเตอร์"],
    "สุขศึกษา": ["สุขศึกษา"],
    "พลศึกษา": ["พลศึกษา"],
    "ทัศนศิลป์": ["ทัศนศิลป์", "ศิลปะ", "ศิลปศึกษา"],
    "ดนตรี": ["ดนตรี"],
    "นาฏศิลป์": ["นาฏศิลป์"],
    "คหกรรม": ["คหกรรม"],
    "เกษตรกรรม": ["เกษตร"],
    "อุตสาหกรรม": ["อุตสาหกรรม"],
    "วิชาชีพ/การงานอาชีพอื่นๆ": ["การงาน", "อาชีพ", "ธุรกิจ", "พาณิชย์"],
}

GROUP_ALIASES = {
    "thai": ["ภาษาไทย"],
    "math": ["คณิต"],
    "foreign": ["ภาษาต่างประเทศ", "ภาษาอังกฤษ", "อังกฤษ", "ภาษาจีน", "จีน", "ญี่ปุ่น", "ฝรั่งเศส"],
    "social": ["สังคม", "ศาสนา", "วัฒนธรรม", "ประวัติศาสตร์", "ภูมิศาสตร์"],
    "science": ["วิทยาศาสตร์", "วิทย์", "ฟิสิกส์", "เคมี", "ชีววิทยา", "เทคโนโลยี", "คอมพิวเตอร์"],
    "health": ["สุขศึกษา", "พลศึกษา"],
    "art": ["ศิลป", "ทัศนศิลป์", "ดนตรี", "นาฏศิลป์"],
    "career": ["การงาน", "อาชีพ", "คหกรรม", "เกษตร", "อุตสาหกรรม", "ธุรกิจ", "พาณิชย์"],
}

GROUP_LOOKUP = {group_id: group_name for group_id, group_name, _ in MAJOR_TAXONOMY}
SUBJECT_GROUP_LOOKUP = {
    subject: (group_id, group_name)
    for group_id, group_name, subjects in MAJOR_TAXONOMY
    for subject in subjects
}


def cell_text(value):
    if value is None:
        return ""
    return str(value).strip()


def to_int(value):
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if text == "":
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def normalize_school_code(value):
    text = cell_text(value)
    if not text:
        return ""
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def classify_major(values):
    haystack = " ".join(value for value in values if value)
    if not haystack:
        return "other", "ไม่เข้ากลุ่มมาตรฐาน", "ไม่ระบุ"

    for subject, aliases in SUBJECT_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            group_id, group_name = SUBJECT_GROUP_LOOKUP[subject]
            return group_id, group_name, subject

    for group_id, aliases in GROUP_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            group_name = GROUP_LOOKUP[group_id]
            return group_id, group_name, "อื่นๆ"

    return "other", "ไม่เข้ากลุ่มมาตรฐาน", "อื่นๆ"


def load_sheet_rows(path, sheet_name, header_row=1, data_only=True):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=data_only)
    ws = wb[sheet_name]
    rows = ws.iter_rows(values_only=True)
    headers = None
    records = []
    for index, row in enumerate(rows, start=1):
        if index == header_row:
            headers = [cell_text(value) for value in row]
            continue
        if index < header_row or headers is None:
            continue
        if not any(cell_text(value) for value in row):
            continue
        record = {}
        for col_index, header in enumerate(headers):
            if not header:
                continue
            value = row[col_index] if col_index < len(row) else None
            record[header] = value
        records.append(record)
    return records


def build_national_school_lookup():
    rows = load_sheet_rows(RAW_SCHOOLS_PATH, "Sheet2", header_row=2, data_only=True)
    lookup = {}
    for row in rows:
        school_code = normalize_school_code(row.get("รหัสโรงเรียน") or row.get("dmc"))
        if not school_code:
            continue
        lookup[school_code] = {
            "school_code": school_code,
            "school_name": cell_text(row.get("ชื่อโรงเรียน")),
            "area_name": cell_text(row.get("สังกัด")),
            "total_students": to_int(row.get("นร.")),
            "actual_teachers": to_int(row.get("ครู มีตัวจริง (คนครอง)")),
            "school_size": cell_text(row.get("ขนาดโรงเรียนตามเกณฑ์การย้ายของ สพฐ.")),
            "hired_teachers": to_int(row.get("พรก. (ครูผู้สอน)")) + to_int(row.get("อัตราจ้าง (ครูผู้สอน)")),
        }
    return lookup


def transform_schools(national_lookup):
    rows = load_sheet_rows(RAW_TEACHERS_PATH, "ข้อมูลโรงเรียน", header_row=1, data_only=True)
    output = []
    seen = set()
    for row in rows:
        area_name = cell_text(row.get("ชื่อหน่วยงานต้นสังกัด"))
        if area_name not in TARGET_AREAS:
            continue
        school_code = normalize_school_code(row.get("รหัสโรงเรียน (MOE CODE)"))
        if not school_code or school_code in seen:
            continue
        seen.add(school_code)
        national = national_lookup.get(school_code, {})
        output.append({
            "school_code": school_code,
            "school_name": cell_text(row.get("ชื่อสถานศึกษา")) or national.get("school_name", ""),
            "area_code": normalize_school_code(row.get("รหัสหน่วยงาน")),
            "area_name": area_name,
            "total_students": to_int(row.get("จำวน นร. รวม")) or national.get("total_students", 0),
            "actual_teachers": national.get("actual_teachers", 0),
            "school_size": national.get("school_size", ""),
            "hired_teachers": national.get("hired_teachers", 0),
        })
    return output


def transform_teachers():
    rows = load_sheet_rows(RAW_TEACHERS_PATH, "persons", header_row=1, data_only=True)
    output = []
    for row in rows:
        position_name = cell_text(row.get("ชื่อตำแหน่ง"))
        if "ครู" not in position_name:
            continue
        major_candidates = [
            cell_text(row.get("กลุ่มวิชาเอกตามมาตรฐานวิชาเอกในสถานศึกษา")),
            cell_text(row.get("สาขาวิชาเอกที่บรรจุ")),
            cell_text(row.get("วุฒิการศึกษาที่บรรจุ")),
            cell_text(row.get("วุฒิการศึกษาสูงสุด2")),
        ]
        teacher_major = next((value for value in major_candidates if value), "")
        subject_group_id, subject_group, subject_major = classify_major(major_candidates)
        output.append({
            "teacher_id": normalize_school_code(row.get("เลขที่จ่ายตรง")) or normalize_school_code(row.get("ตำแหน่งเลขที่")),
            "school_code": normalize_school_code(row.get("รหัสสถานศึกษา")),
            "teacher_major": teacher_major,
            "subject_group_id": subject_group_id,
            "subject_group": subject_group,
            "subject_major": subject_major,
            "birth_date": cell_text(row.get("วัน เดือน ปีเกิด")),
            "retirement_date": cell_text(row.get("วัน เดือน ปีเกษียณ")),
            "start_date": cell_text(row.get("วัน เดือน ปีบรรจุ")),
            "condition_of_tenure": cell_text(row.get("เงื่อนไขการดำรงตำแหน่ง")),
        })
    return output


def main():
    national_lookup = build_national_school_lookup()
    schools = transform_schools(national_lookup)
    teachers = transform_teachers()
    payload = {
        "schools": schools,
        "teachers": teachers,
        "summary": {
            "schools_rows": len(schools),
            "teachers_rows": len(teachers),
            "target_areas": sorted(TARGET_AREAS),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
