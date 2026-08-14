import json
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path("public/dashboard-data.json")

COLORS = {
    "background": "#e7e7df",
    "panel": "#fffef8",
    "soft": "#f7f7f0",
    "line": "#e3e1d7",
    "ink": "#171914",
    "muted": "#74776b",
    "purple": "#6849ee",
    "green": "#36a37d",
    "orange": "#f0834a",
    "red": "#ff5a3d",
    "blue": "#5f9df7",
}

CHART_COLORS = [
    "#36a37d",
    "#f0834a",
    "#6849ee",
    "#9dcf3f",
    "#ff5a3d",
    "#5f9df7",
    "#d042b8",
    "#f2c241",
    "#50b8b1",
]


st.set_page_config(
    page_title="แดชบอร์ดกลุ่มวิชาเอกครู",
    page_icon="📊",
    layout="wide",
)


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;600;700;800;900&display=swap');
        :root {{
            --background: {COLORS["background"]};
            --foreground: {COLORS["ink"]};
            --panel: {COLORS["panel"]};
            --line: {COLORS["line"]};
            --muted: {COLORS["muted"]};
            --blue: {COLORS["blue"]};
            --green: {COLORS["green"]};
            --purple: {COLORS["purple"]};
            --red: {COLORS["red"]};
            --orange: {COLORS["orange"]};
            --soft: {COLORS["soft"]};
        }}
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(223, 246, 166, 0.36), transparent 32vw),
                radial-gradient(circle at top right, rgba(185, 173, 255, 0.22), transparent 34vw),
                {COLORS["background"]};
            color: {COLORS["ink"]};
            font-family: "Noto Sans Thai", Arial, Helvetica, sans-serif;
        }}
        #MainMenu, footer, header, div[data-testid="stToolbar"], div[data-testid="stDecoration"] {{
            display: none !important;
        }}
        .block-container {{
            width: min(1500px, calc(100vw - 32px));
            max-width: 1500px;
            padding: 24px 0 40px !important;
        }}
        h1, h2, h3, p, span, label {{
            letter-spacing: 0 !important;
        }}
        h1, h2, h3 {{
            color: var(--foreground);
            font-weight: 900;
        }}
        p {{
            color: #4f5248;
            line-height: 1.72;
        }}
        div[data-testid="stMetric"] {{
            background: {COLORS["panel"]};
            border: 1px solid {COLORS["line"]};
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 12px 28px rgba(70, 70, 56, 0.08);
        }}
        div[data-testid="stMetricLabel"] {{
            color: {COLORS["muted"]};
            font-weight: 800;
        }}
        .hero {{
            min-height: 214px;
            background: #fbfbf5;
            border: 1px solid #deddd2;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 16px;
            box-shadow: 0 18px 36px rgba(58, 58, 45, 0.14);
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 24px;
        }}
        .hero p {{
            margin: 0 0 10px;
            color: {COLORS["muted"]};
            font-weight: 800;
        }}
        .hero h1 {{
            margin: 0 0 14px;
            color: {COLORS["ink"]};
            font-size: 48px;
            line-height: 1.05;
        }}
        .hero-title {{
            min-width: 0;
        }}
        .hero-stat {{
            width: min(330px, 100%);
            border: 1px solid #deddd2;
            border-radius: 8px;
            padding: 18px;
            background: #ffffff;
            flex: 0 0 330px;
        }}
        .hero-stat span,
        .hero-stat small {{
            color: var(--muted);
            font-weight: 800;
        }}
        .hero-stat strong {{
            display: block;
            margin: 8px 0;
            font-size: 48px;
            line-height: 1;
            color: var(--foreground);
        }}
        .prototype {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
            width: fit-content;
            max-width: 100%;
            border: 1px solid #deddd2;
            border-radius: 8px;
            padding: 10px 12px;
            background: #f0f1e8;
            margin-bottom: 14px;
        }}
        .prototype strong {{
            color: {COLORS["ink"]};
        }}
        .prototype span {{
            color: {COLORS["muted"]};
        }}
        .card {{
            background: {COLORS["panel"]};
            border: 1px solid {COLORS["line"]};
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 12px 28px rgba(70, 70, 56, 0.08);
            margin-bottom: 16px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 16px;
        }}
        .metric-card {{
            background: #fffefb;
            border: 1px solid var(--line);
            border-top: 4px solid var(--blue);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 12px 28px rgba(70, 70, 56, 0.08);
            min-height: 134px;
        }}
        .metric-card.accent-green {{ border-top-color: var(--green); }}
        .metric-card.accent-purple {{ border-top-color: var(--purple); }}
        .metric-card.accent-red {{ border-top-color: var(--red); }}
        .metric-card span {{
            color: var(--muted);
            font-weight: 800;
        }}
        .metric-card strong {{
            display: block;
            margin-top: 8px;
            color: var(--foreground);
            font-size: 34px;
            line-height: 1;
            font-weight: 900;
        }}
        .metric-card small {{
            display: block;
            margin-top: 10px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.35;
            font-weight: 700;
        }}
        .panel {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 12px 28px rgba(70, 70, 56, 0.08);
            margin-bottom: 16px;
        }}
        .panel-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 16px;
        }}
        .panel-head h2 {{
            margin: 0 0 4px;
            font-size: 21px;
            letter-spacing: 0;
        }}
        .panel-head span {{
            color: var(--muted);
            font-weight: 700;
        }}
        .callout {{
            background: #fff8ed;
            border: 1px solid #efc89d;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 14px;
            color: #4d3928;
        }}
        .small-muted {{
            color: {COLORS["muted"]};
            font-size: 0.92rem;
        }}
        div[data-testid="stSelectbox"] label,
        div[data-testid="stMultiSelect"] label,
        div[data-testid="stTextInput"] label {{
            color: var(--muted) !important;
            font-size: 12px !important;
            font-weight: 800 !important;
        }}
        .stSelectbox div[data-baseweb="select"],
        .stMultiSelect div[data-baseweb="select"],
        .stTextInput input {{
            min-height: 40px;
            border-radius: 8px;
            border-color: var(--line);
            background: #fffef8;
        }}
        .stButton button,
        .stDownloadButton button {{
            min-height: 38px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #fffef8;
            color: var(--foreground);
            font-weight: 900;
        }}
        .stButton button:hover,
        .stDownloadButton button:hover {{
            border-color: var(--blue);
            color: var(--foreground);
        }}
        .stTabs [data-baseweb="tab-list"] {{
            position: sticky;
            top: 0;
            z-index: 5;
            background: rgba(247, 247, 240, 0.92);
            backdrop-filter: blur(10px);
            border: 1px solid {COLORS["line"]};
            border-radius: 8px;
            padding: 8px;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 6px;
            color: {COLORS["muted"]};
            font-weight: 800;
            min-height: 42px;
            padding: 0 16px;
        }}
        .stTabs [aria-selected="true"] {{
            background: {COLORS["purple"]};
            color: white;
        }}
        .stTabs [data-baseweb="tab-highlight"] {{
            display: none;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid {COLORS["line"]};
            border-radius: 8px;
        }}
        .rank-list,
        .subject-list,
        .drill-grid {{
            display: grid;
            gap: 10px;
        }}
        .rank-row,
        .subject-row,
        .drill-card {{
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #ffffff;
            padding: 14px;
        }}
        .rank-row {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 10px 14px;
            align-items: center;
        }}
        .rank-row strong,
        .subject-row strong,
        .drill-card strong {{
            display: block;
            color: var(--foreground);
            font-weight: 900;
        }}
        .rank-row span,
        .subject-row span,
        .drill-card span {{
            color: var(--muted);
            font-size: 13px;
            font-weight: 700;
        }}
        .rank-row b,
        .drill-card b {{
            font-size: 24px;
            color: var(--red);
        }}
        .subject-row {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 4px 12px;
        }}
        .subject-row b {{
            color: var(--red);
            white-space: nowrap;
        }}
        .bar-track {{
            grid-column: 1 / -1;
            height: 9px;
            background: #edf1f5;
            border-radius: 999px;
            overflow: hidden;
        }}
        .bar-fill {{
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, var(--orange), var(--red));
        }}
        .drill-grid {{
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }}
        .drill-card {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 10px;
            align-items: center;
        }}
        .viz-3d-scene {{
            min-height: 470px;
            padding: 48px 24px 34px;
            display: flex;
            align-items: flex-end;
            justify-content: flex-start;
            gap: 20px;
            overflow-x: auto;
            perspective: 980px;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0), rgba(157, 207, 63, 0.09)),
                repeating-linear-gradient(0deg, #ecebe0 0 1px, transparent 1px 64px);
            border: 1px solid var(--line);
            border-radius: 8px;
            margin-bottom: 14px;
        }}
        .bar3d-group {{
            min-width: max-content;
            min-height: 398px;
            display: grid;
            grid-template-rows: 1fr auto;
            align-items: end;
            justify-items: center;
        }}
        .bar3d-set {{
            display: flex;
            align-items: flex-end;
            gap: 10px;
        }}
        .bar3d-group > strong {{
            width: 100%;
            max-width: 280px;
            min-height: 38px;
            margin-top: 12px;
            color: var(--foreground);
            font-size: 14px;
            line-height: 1.25;
            text-align: center;
            overflow-wrap: anywhere;
        }}
        .bar3d-wrap {{
            width: 72px;
            min-width: 72px;
            min-height: 350px;
            border: 0;
            background: transparent;
            display: grid;
            grid-template-rows: 32px 1fr auto auto;
            align-items: end;
            justify-items: center;
            text-align: center;
            transform: rotateX(0deg) rotateY(-8deg);
            transform-style: preserve-3d;
            animation: bar-rise 420ms ease-out both;
            animation-delay: var(--delay);
        }}
        .bar3d-value {{
            min-width: 56px;
            min-height: 34px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 3px solid var(--bar-front);
            border-radius: 999px;
            background: #ffffff;
            color: var(--bar-side);
            font-size: 20px;
            font-weight: 900;
            line-height: 1;
            box-shadow: 0 10px 20px rgba(24, 34, 48, 0.16);
            transform: translateY(10px);
            position: relative;
            z-index: 3;
        }}
        .bar3d {{
            position: relative;
            width: 42px;
            height: var(--bar-height);
            min-height: 34px;
            background: linear-gradient(180deg, var(--bar-top), var(--bar-front));
            transform: skewY(-2deg);
            box-shadow: 0 16px 20px rgba(32, 47, 67, 0.24);
        }}
        .bar3d::before,
        .bar3d::after {{
            content: "";
            position: absolute;
            display: block;
        }}
        .bar3d::before {{
            left: 0;
            top: -18px;
            width: 42px;
            height: 18px;
            background: var(--bar-top);
            transform: skewX(-42deg);
            transform-origin: bottom left;
        }}
        .bar3d::after {{
            right: -16px;
            top: -18px;
            width: 16px;
            height: calc(var(--bar-height) + 18px);
            background: linear-gradient(180deg, var(--bar-side), color-mix(in srgb, var(--bar-side), #000000 18%));
            transform: skewY(-40deg);
            transform-origin: left top;
        }}
        .bar3d-wrap small {{
            color: var(--muted);
            font-size: 12px;
            font-weight: 800;
            line-height: 1.2;
        }}
        .bar3d-wrap em {{
            width: 100%;
            min-height: 34px;
            margin-top: 6px;
            color: var(--muted);
            font-size: 11px;
            font-style: normal;
            font-weight: 800;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }}
        @keyframes bar-rise {{
            from {{ opacity: 0; transform: translateY(18px) rotateY(-8deg); }}
            to {{ opacity: 1; transform: translateY(0) rotateY(-8deg); }}
        }}
        .pie-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
        }}
        .pie-card {{
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px;
            background: #fffef8;
        }}
        .pie-card h3 {{
            margin: 0 0 4px;
            font-size: 17px;
            letter-spacing: 0;
        }}
        .pie-card > span {{
            color: var(--muted);
            font-size: 13px;
            line-height: 1.35;
            font-weight: 700;
        }}
        .pie-body {{
            margin-top: 16px;
            display: grid;
            grid-template-columns: 180px minmax(0, 1fr);
            gap: 16px;
            align-items: center;
        }}
        .pie-chart {{
            width: 180px;
            aspect-ratio: 1;
            border-radius: 50%;
            display: grid;
            place-items: center;
            box-shadow: inset 0 0 0 1px rgba(72, 72, 56, 0.06), 0 18px 28px rgba(70, 70, 56, 0.12);
        }}
        .pie-chart > div {{
            width: 96px;
            aspect-ratio: 1;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: #fffef8;
            color: var(--foreground);
            box-shadow: 0 8px 18px rgba(70, 70, 56, 0.12);
        }}
        .pie-chart strong {{
            align-self: end;
            font-size: 24px;
        }}
        .pie-chart small {{
            align-self: start;
            color: var(--muted);
            font-weight: 800;
        }}
        .pie-legend {{
            display: grid;
            gap: 8px;
        }}
        .legend-row {{
            display: grid;
            grid-template-columns: 12px minmax(0, 1fr) auto auto;
            gap: 8px;
            align-items: center;
            font-size: 13px;
        }}
        .legend-row i {{
            width: 12px;
            aspect-ratio: 1;
            border-radius: 50%;
        }}
        .legend-row span {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .legend-row strong {{
            font-variant-numeric: tabular-nums;
        }}
        .legend-row small {{
            color: var(--muted);
            font-weight: 800;
        }}
        .explain-strip {{
            margin: -4px 0 16px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            color: var(--muted);
            font-size: 13px;
            font-weight: 800;
        }}
        .explain-pill {{
            min-height: 36px;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 7px 12px;
            background: #fffef8;
            color: var(--ink);
            font-weight: 900;
        }}
        @media (max-width: 980px) {{
            .hero {{
                display: grid;
                padding: 22px;
            }}
            .hero h1 {{
                font-size: 36px;
            }}
            .hero-stat {{
                width: 100%;
                flex-basis: auto;
            }}
            .metric-grid,
            .pie-grid,
            .drill-grid {{
                grid-template-columns: 1fr;
            }}
            .pie-body {{
                grid-template-columns: 1fr;
                justify-items: center;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        st.error("ไม่พบไฟล์ public/dashboard-data.json")
        st.stop()
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def nf(value):
    return f"{int(value):,}"


def teacher_count_text(value):
    return f"พบครู {nf(value)} คน"


def get_group(data, group_id):
    return next(group for group in data["major_groups"] if group["group_id"] == group_id)


def school_group(school, group_id):
    return next((item for item in school["subject_groups"] if item["group_id"] == group_id), None)


def subject_status_row(school, group_id, subject):
    group = school_group(school, group_id)
    if not group:
        return None
    return next((item for item in group["subjects"] if item["subject"] == subject), None)


def subject_rows_by_area(data, selected_group, selected_areas):
    rows = []
    for subject in selected_group["subjects"]:
        for area_name in selected_areas:
            schools = [school for school in data["schools"] if school["area_name"] == area_name]
            total_teachers = 0
            schools_with_teacher = 0
            shortage_schools = 0
            for school in schools:
                subject_row = subject_status_row(school, selected_group["group_id"], subject)
                count = subject_row.get("teacher_count", 0) if subject_row else 0
                total_teachers += count
                if count > 0:
                    schools_with_teacher += 1
                if subject_row and subject_row.get("status") == "ขาด":
                    shortage_schools += 1
            rows.append(
                {
                    "วิชาเอกย่อย": subject,
                    "พื้นที่": area_name,
                    "จำนวนครูที่พบ": total_teachers,
                    "โรงเรียนที่พบครู": schools_with_teacher,
                    "โรงเรียนที่ยังไม่พบครูวิชานี้": shortage_schools,
                }
            )
    return pd.DataFrame(rows)


def selected_group_subject_summary(data, group_id):
    rows = [row for row in data["subject_summary"] if row["group_id"] == group_id]
    return pd.DataFrame(
        [
            {
                "วิชาเอกย่อย": row["subject"],
                "จำนวนครูที่พบ": row["total_teachers"],
                "โรงเรียนที่พบครู": row["schools_with_teacher"],
                "โรงเรียนที่ยังไม่พบครูวิชานี้": row["shortage_schools"],
            }
            for row in rows
        ]
    ).sort_values("โรงเรียนที่ยังไม่พบครูวิชานี้", ascending=False)


def make_school_table(data, group_id, area_name, status_name, subject_name, query):
    rows = []
    query = query.strip().lower()
    for school in data["schools"]:
        group = school_group(school, group_id)
        if area_name != "ทั้งหมด" and school["area_name"] != area_name:
            continue
        if status_name != "ทั้งหมด" and (group or {}).get("status", "ไม่มีข้อมูล") != status_name:
            continue
        if query and query not in school["school_name"].lower() and query not in school["school_code"]:
            continue

        if subject_name == "ทั้งหมด":
            missing = (group or {}).get("missing_subjects", [])
        else:
            subject_row = subject_status_row(school, group_id, subject_name)
            has_subject = (subject_row or {}).get("teacher_count", 0) > 0
            is_missing = (subject_row or {}).get("status") == "ขาด"
            if not (has_subject or is_missing):
                continue
            missing = [subject_name] if is_missing else []

        rows.append(
            {
                "รหัสโรงเรียน": school["school_code"],
                "ชื่อโรงเรียน": school["school_name"],
                "เขต": school["area_name"],
                "ขนาดโรงเรียน": school.get("school_size") or "ไม่ระบุ",
                "ข้อมูลครูในไฟล์": school["teacher_records"],
                "ครูที่พบในกลุ่มนี้": (group or {}).get("actual_teachers", 0),
                "ครบวิชาย่อย": f"{(group or {}).get('covered_subjects', 0)} / {(group or {}).get('required_subjects', 0)}",
                "สถานะ": (group or {}).get("status", "ไม่มีข้อมูล"),
                "วิชาที่ควรติดตาม": " | ".join(missing[:4]) if missing else "ไม่พบวิชาที่ต้องติดตามตามตัวกรองนี้",
                "ความเสี่ยงจากโมเดลเดิม": school.get("sudden_shortage_risk_level", "ไม่ระบุ"),
                "จำนวนรายการครู": len(school.get("teacher_roster", [])),
            }
        )
    return pd.DataFrame(rows)


def render_downloads(df, basename):
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "ดาวน์โหลด CSV",
        csv,
        file_name=f"{basename}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def metric_card(label, value, hint, tone="accent-blue"):
    return (
        f'<article class="metric-card {tone}">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(str(value))}</strong>"
        f"<small>{escape(hint)}</small>"
        "</article>"
    )


def progress_row(title, subtitle, value, max_value):
    width = max(3, (value / max(max_value, 1)) * 100)
    return (
        '<div class="rank-row">'
        f"<div><strong>{escape(title)}</strong><span>{escape(subtitle)}</span></div>"
        f"<b>{nf(value)}</b>"
        '<div class="bar-track">'
        f'<div class="bar-fill" style="width:{width:.1f}%"></div>'
        "</div></div>"
    )


def subject_card(subject, teacher_count, schools_with_teacher, shortage, max_shortage):
    width = max(3, (shortage / max(max_shortage, 1)) * 100)
    return (
        '<div class="drill-card">'
        f"<div><strong>{escape(subject)}</strong>"
        f"<span>{escape(teacher_count_text(teacher_count))} · พบใน {nf(schools_with_teacher)} โรงเรียน</span></div>"
        f"<b>{nf(shortage)}</b>"
        '<div class="bar-track">'
        f'<div class="bar-fill" style="width:{width:.1f}%"></div>'
        "</div></div>"
    )


def render_3d_chart(df):
    totals = (
        df.groupby("วิชาเอกย่อย", as_index=False)["โรงเรียนที่ยังไม่พบครูวิชานี้"]
        .sum()
        .sort_values("โรงเรียนที่ยังไม่พบครูวิชานี้", ascending=False)
        .head(6)
    )
    if totals.empty:
        st.info("ไม่พบวิชาที่ต้องติดตามตามตัวกรองนี้")
        return

    subjects = totals["วิชาเอกย่อย"].tolist()
    chart_df = df[df["วิชาเอกย่อย"].isin(subjects)]
    max_value = max(int(chart_df["โรงเรียนที่ยังไม่พบครูวิชานี้"].max()), 1)
    area_order = list(dict.fromkeys(chart_df["พื้นที่"].tolist()))
    bars = []
    for subject_index, subject in enumerate(subjects):
        area_rows = chart_df[chart_df["วิชาเอกย่อย"] == subject]
        bar_items = []
        for area_index, (_, row) in enumerate(area_rows.iterrows()):
            palette = CHART_COLORS[area_order.index(row["พื้นที่"]) % len(CHART_COLORS)]
            top = lighten_color(palette, 0.48)
            side = darken_color(palette, 0.28)
            value = int(row["โรงเรียนที่ยังไม่พบครูวิชานี้"])
            height = max(34, (value / max_value) * 250)
            delay = (subject_index * max(len(area_order), 1) + area_index) * 28
            short_area = str(row["พื้นที่"]).replace("สำนักงานเขตพื้นที่การศึกษา", "สพท.")
            bar_items.append(
                '<div class="bar3d-wrap" '
                f'style="--bar-height:{height:.1f}px;--delay:{delay}ms;--bar-front:{palette};--bar-top:{top};--bar-side:{side};" '
                f'title="{escape(str(row["พื้นที่"]))}: {nf(value)} โรงเรียน">'
                f'<span class="bar3d-value">{nf(value)}</span>'
                '<span class="bar3d"></span>'
                f'<small>{escape(teacher_count_text(row["จำนวนครูที่พบ"]))}</small>'
                f'<em>{escape(short_area)}</em>'
                "</div>"
            )
        bars.append(
            '<div class="bar3d-group">'
            f'<div class="bar3d-set">{"".join(bar_items)}</div>'
            f"<strong>{escape(subject)}</strong>"
            "</div>"
        )
    st.markdown(f'<div class="viz-3d-scene">{"".join(bars)}</div>', unsafe_allow_html=True)


def hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, int(v))):02x}" for v in rgb)


def lighten_color(color, amount):
    r, g, b = hex_to_rgb(color)
    return rgb_to_hex((r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount))


def darken_color(color, amount):
    r, g, b = hex_to_rgb(color)
    return rgb_to_hex((r * (1 - amount), g * (1 - amount), b * (1 - amount)))


def pie_card(title, subtitle, rows, label_key, value_key):
    filtered = [row for row in rows if int(row[value_key]) > 0]
    total = sum(int(row[value_key]) for row in filtered)
    if total == 0:
        gradient = "#edf1f5 0deg 360deg"
    else:
        cursor = 0
        parts = []
        for index, row in enumerate(filtered):
            value = int(row[value_key])
            start = cursor
            cursor += (value / total) * 360
            parts.append(f"{CHART_COLORS[index % len(CHART_COLORS)]} {start:.2f}deg {cursor:.2f}deg")
        gradient = ", ".join(parts)

    legend = []
    for index, row in enumerate(filtered[:7]):
        value = int(row[value_key])
        pct = (value / total * 100) if total else 0
        legend.append(
            '<div class="legend-row">'
            f'<i style="background:{CHART_COLORS[index % len(CHART_COLORS)]}"></i>'
            f'<span>{escape(str(row[label_key]))}</span>'
            f"<strong>{nf(value)}</strong>"
            f"<small>{pct:.1f}%</small>"
            "</div>"
        )
    if len(filtered) > 7:
        legend.append(f'<div class="legend-row"><span></span><span>อื่นๆ</span><strong>+{len(filtered)-7}</strong><small></small></div>')

    return (
        '<article class="pie-card">'
        f"<h3>{escape(title)}</h3>"
        f"<span>{escape(subtitle)}</span>"
        '<div class="pie-body">'
        f'<div class="pie-chart" style="background:conic-gradient({gradient})"><div><strong>{nf(total)}</strong><small>รวม</small></div></div>'
        f'<div class="pie-legend">{"".join(legend) or "<span class=\"small-muted\">ไม่มีข้อมูลตามตัวกรอง</span>"}</div>'
        "</div></article>"
    )


inject_css()
data = load_data()

areas = ["ทั้งหมด"] + [row["area_name"] for row in data["area_summary"]]
area_options = [row["area_name"] for row in data["area_summary"]]
group_options = {group["group_name"]: group["group_id"] for group in data["major_groups"]}

st.markdown(
    f"""
    <section class="hero">
      <div class="hero-title">
        <p>ระบบต้นแบบวิเคราะห์อัตรากำลังครู</p>
        <h1>แดชบอร์ดกลุ่มวิชาเอกครู</h1>
        <div class="prototype">
          <strong>Prototype (ระบบต้นแบบ)</strong>
          <span>ใช้เพื่อทดลองวิเคราะห์และช่วยชี้เป้าเบื้องต้น ไม่ใช่ระบบตัดสินหรือจัดสรรอัตรากำลังจริง</span>
        </div>
        <span class="small-muted">วิเคราะห์จากไฟล์ครูตามวิชาเอก · ครอบคลุม {nf(data["overview"]["target_areas"])} เขตพื้นที่ · อัปเดต {data["generated_at"]}</span>
      </div>
      <div class="hero-stat">
        <span>ช่องว่างรายวิชาเอก</span>
        <strong>{nf(data["overview"]["subject_shortage_slots"])}</strong>
        <small>จาก {nf(data["overview"]["official_subjects"])} วิชาเอกย่อยใน {nf(data["overview"]["official_major_groups"])} กลุ่ม</small>
      </div>
    </section>
    <div class="explain-strip">
      <span>ต้องการดูที่มาหรือวิธีคำนวณ?</span>
      <span class="explain-pill">แหล่งข้อมูล</span>
      <span class="explain-pill">กราฟแสดงอะไร</span>
      <span class="explain-pill">การส่งออกไฟล์</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(["ภาพรวม", "กลุ่มวิชา", "กราฟและพื้นที่", "รายโรงเรียน", "ข้อมูล/ข้อจำกัด"])

with tabs[0]:
    overview = data["overview"]
    complete_rate = overview["complete_group_school_pairs"] / overview["total_group_school_pairs"] * 100
    st.markdown(
        '<section class="metric-grid">'
        + metric_card("โรงเรียนในชุดข้อมูล", nf(overview["total_schools"]), f"มีข้อมูลครูใน {nf(overview['covered_schools'])} โรงเรียน", "accent-blue")
        + metric_card("ครูที่นำมานับ", nf(overview["teacher_records"]), "นับจากรายการตำแหน่งครูในไฟล์ครู", "accent-green")
        + metric_card("ความครบถ้วนรายกลุ่ม", f"{complete_rate:.1f}%", f"{nf(overview['complete_group_school_pairs'])} คู่โรงเรียน-กลุ่มวิชาครบ", "accent-purple")
        + metric_card("โรงเรียนเสี่ยงสูงจากโมเดลเดิม", nf(overview["high_risk_schools"]), "ตัวช่วยจัดลำดับตรวจสอบ ไม่ใช่ผลยืนยัน", "accent-red")
        + "</section>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])
    with left:
        max_group_shortage = max(group["shortage_subject_slots"] for group in data["major_groups"])
        group_rows = [
            progress_row(
                group["group_name"],
                f"{teacher_count_text(group['actual_teachers'])} · ข้อมูลครบ {nf(group['complete_schools'])} โรงเรียน",
                group["shortage_subject_slots"],
                max_group_shortage,
            )
            for group in sorted(data["major_groups"], key=lambda item: item["shortage_subject_slots"], reverse=True)
        ]
        st.markdown(
            '<section class="panel"><div class="panel-head"><div><h2>กลุ่มวิชาที่ควรดูต่อ</h2>'
            '<span>เรียงตามจำนวนช่องว่างวิชาเอกย่อย</span></div></div>'
            f'<div class="rank-list">{"".join(group_rows)}</div></section>',
            unsafe_allow_html=True,
        )
    with right:
        subject_rows = [
            '<div class="subject-row">'
            f'<span>{escape(row["group_name"])}</span>'
            f'<strong>{escape(row["subject"])}</strong>'
            f'<b>{nf(row["shortage_schools"])} โรงเรียน</b>'
            "</div>"
            for row in data["top_subject_shortage"]
        ]
        st.markdown(
            '<section class="panel"><div class="panel-head"><div><h2>วิชาเอกย่อยที่ขาดบ่อย</h2>'
            '<span>นับโรงเรียนที่ยังไม่พบครูวิชาเอกนั้นในข้อมูลครู</span></div></div>'
            f'<div class="subject-list">{"".join(subject_rows)}</div></section>',
            unsafe_allow_html=True,
        )

with tabs[1]:
    selected_group_name = st.selectbox("เลือกกลุ่มวิชา", list(group_options.keys()), key="group_tab")
    selected_group = get_group(data, group_options[selected_group_name])
    st.markdown(
        '<section class="metric-grid" style="grid-template-columns:repeat(3,minmax(0,1fr));">'
        + metric_card("ครูในกลุ่มนี้", nf(selected_group["actual_teachers"]), "จำนวนครูที่พบจากวิชาเอกในไฟล์ครู", "accent-green")
        + metric_card("โรงเรียนที่ครบ", nf(selected_group["complete_schools"]), f"{nf(selected_group['partial_schools'])} โรงเรียนยังขาดบางวิชา", "accent-blue")
        + metric_card("ช่องว่างวิชาย่อย", nf(selected_group["shortage_subject_slots"]), "baseline อย่างน้อย 1 คนต่อวิชาย่อย", "accent-red")
        + "</section>",
        unsafe_allow_html=True,
    )

    group_subject_df = selected_group_subject_summary(data, selected_group["group_id"])
    max_subject_shortage = int(group_subject_df["โรงเรียนที่ยังไม่พบครูวิชานี้"].max()) if len(group_subject_df) else 1
    drill_cards = [
        subject_card(
            row["วิชาเอกย่อย"],
            int(row["จำนวนครูที่พบ"]),
            int(row["โรงเรียนที่พบครู"]),
            int(row["โรงเรียนที่ยังไม่พบครูวิชานี้"]),
            max_subject_shortage,
        )
        for _, row in group_subject_df.iterrows()
    ]
    st.markdown(f'<section class="drill-grid">{"".join(drill_cards)}</section>', unsafe_allow_html=True)
    st.markdown('<div class="panel-head"><div><h2>รายละเอียดวิชาเอกย่อย</h2><span>ข้อมูลชุดเดียวกับการ์ดด้านบน</span></div></div>', unsafe_allow_html=True)
    st.dataframe(group_subject_df, use_container_width=True, hide_index=True)
    render_downloads(group_subject_df, f"subject-summary-{selected_group['group_id']}")

with tabs[2]:
    st.markdown(
        '<section class="panel"><div class="panel-head"><div><h2>กราฟ 3 มิติรายวิชาเอกย่อย</h2>'
        '<span>ติ๊กหลายพื้นที่เพื่อเทียบจำนวนโรงเรียนที่ยังไม่มีครูวิชาเอกนั้นในแต่ละเขต</span></div></div></section>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 2])
    with c1:
        graph_group_name = st.selectbox("เลือกกลุ่มวิชา", list(group_options.keys()), key="graph_group")
    with c2:
        compare_areas = st.multiselect(
            "เลือกพื้นที่ที่ต้องการเปรียบเทียบ",
            area_options,
            default=area_options[:3],
        )
    if not compare_areas:
        st.warning("กรุณาเลือกอย่างน้อย 1 พื้นที่")
    else:
        graph_group = get_group(data, group_options[graph_group_name])
        compare_df = subject_rows_by_area(data, graph_group, compare_areas)
        render_3d_chart(compare_df)
        with st.expander("อ่านกราฟนี้อย่างไร"):
            st.write(
                "แต่ละกลุ่มแท่งคือ 1 วิชาเอกย่อย สีของแท่งคือพื้นที่ที่เลือกไว้ "
                "ความสูงของแท่งคือจำนวนโรงเรียนในพื้นที่นั้นที่ยังไม่พบครูวิชาเอกย่อยนั้นในข้อมูลครู "
                "ถ้าแท่งสูงกว่า แปลว่าพื้นที่นั้นมีโรงเรียนที่ควรตรวจสอบต่อในวิชาเอกย่อยนั้นมากกว่า"
            )
        st.dataframe(compare_df, use_container_width=True, hide_index=True)
        render_downloads(compare_df, f"area-subject-compare-{graph_group['group_id']}")

    st.divider()
    st.markdown(
        '<section class="panel"><div class="panel-head"><div><h2>Pie Chart วิเคราะห์รายพื้นที่</h2>'
        '<span>เลือกพื้นที่เพื่อดูสัดส่วนสถานะ วิชาที่ขาด และโครงสร้างครูตามกลุ่มวิชา</span></div></div></section>',
        unsafe_allow_html=True,
    )
    pie_group = get_group(data, group_options[st.selectbox("กลุ่มวิชาสำหรับ Pie Chart", list(group_options.keys()), key="pie_group")])
    pie_area = st.selectbox("พื้นที่สำหรับ Pie Chart", areas, key="pie_area")
    pie_schools = data["schools"] if pie_area == "ทั้งหมด" else [school for school in data["schools"] if school["area_name"] == pie_area]

    status_rows = []
    for status in ["ครบ", "ขาดบางวิชา", "ไม่มีข้อมูล"]:
        status_rows.append(
            {
                "สถานะ": status,
                "จำนวนโรงเรียน": sum(
                    1 for school in pie_schools if (school_group(school, pie_group["group_id"]) or {}).get("status", "ไม่มีข้อมูล") == status
                ),
            }
        )
    shortage_rows = []
    for subject in pie_group["subjects"]:
        shortage_rows.append(
            {
                "วิชาเอกย่อย": subject,
                "จำนวนโรงเรียน": sum(
                    1
                    for school in pie_schools
                    if (subject_status_row(school, pie_group["group_id"], subject) or {}).get("status") == "ขาด"
                ),
            }
        )
    teacher_rows = []
    for group in data["major_groups"]:
        teacher_rows.append(
            {
                "กลุ่มวิชา": group["group_name"].replace("กลุ่มวิชา", ""),
                "จำนวนครูที่พบ": sum((school_group(school, group["group_id"]) or {}).get("actual_teachers", 0) for school in pie_schools),
            }
        )

    st.markdown(
        '<section class="pie-grid">'
        + pie_card("สถานะของโรงเรียน", f"{pie_group['group_name']} · {pie_area}", status_rows, "สถานะ", "จำนวนโรงเรียน")
        + pie_card("วิชาเอกย่อยที่ควรติดตาม", "สัดส่วนช่องว่างภายในกลุ่มที่เลือก", shortage_rows, "วิชาเอกย่อย", "จำนวนโรงเรียน")
        + pie_card("โครงสร้างครูตามกลุ่มวิชา", f"จำนวนครูที่พบใน {pie_area}", teacher_rows, "กลุ่มวิชา", "จำนวนครูที่พบ")
        + "</section>",
        unsafe_allow_html=True,
    )

with tabs[3]:
    st.subheader("รายโรงเรียน")
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1.5])
    school_group_name = c1.selectbox("กลุ่มวิชา", list(group_options.keys()), key="school_group")
    school_group_selected = get_group(data, group_options[school_group_name])
    school_area = c2.selectbox("พื้นที่", areas, key="school_area")
    school_status = c3.selectbox("สถานะ", schoolStatusOrder, key="school_status")
    school_subject = c4.selectbox("วิชาเอกย่อย", ["ทั้งหมด"] + school_group_selected["subjects"], key="school_subject")
    school_query = st.text_input("ค้นหาด้วยรหัสหรือชื่อโรงเรียน")

    school_df = make_school_table(
        data,
        school_group_selected["group_id"],
        school_area,
        school_status,
        school_subject,
        school_query,
    )
    st.caption(f"{nf(len(school_df))} โรงเรียนตามตัวกรองปัจจุบัน")
    st.dataframe(school_df, use_container_width=True, hide_index=True)
    render_downloads(school_df, f"schools-{school_group_selected['group_id']}")

    with st.expander("ดูบัญชีครูรายโรงเรียนแบบรหัสปิดบัง"):
        if len(school_df) == 0:
            st.info("ไม่พบโรงเรียนตามตัวกรองนี้")
        else:
            school_options = {
                f"{row['ชื่อโรงเรียน']} ({row['รหัสโรงเรียน']})": row["รหัสโรงเรียน"]
                for _, row in school_df.iterrows()
            }
            selected_school_code = st.selectbox("เลือกโรงเรียน", list(school_options.keys()))
            selected_school = next(school for school in data["schools"] if school["school_code"] == school_options[selected_school_code])
            roster_df = pd.DataFrame(
                [
                    {
                        "รหัสอ้างอิงปิดบัง": teacher.get("teacher_ref") or "ไม่ระบุ",
                        "กลุ่มวิชา": teacher.get("subject_group", ""),
                        "วิชาเอกย่อย": teacher.get("subject_major", ""),
                        "วิชาเอกต้นทางในไฟล์ครู": teacher.get("teacher_major", ""),
                    }
                    for teacher in selected_school.get("teacher_roster", [])
                ]
            )
            st.write(f"{selected_school['area_name']} · มีข้อมูลครู {nf(len(roster_df))} รายการในไฟล์")
            st.dataframe(roster_df, use_container_width=True, hide_index=True)
            render_downloads(roster_df, f"teacher-roster-{selected_school['school_code']}")
            st.caption("รหัสนี้เป็นรหัสอ้างอิงปิดบังสำหรับหน้าเว็บ public ไม่ใช่รหัสครูหรือตำแหน่งจริง")

with tabs[4]:
    st.subheader("ข้อมูลและข้อจำกัด")
    st.markdown(
        """
        <div class="callout">
          <strong>Prototype (ระบบต้นแบบ)</strong><br/>
          ML Model ในเว็บนี้ใช้เป็นตัวช่วยจัดลำดับโรงเรียนที่ควรตรวจสอบก่อนเท่านั้น
          ไม่ได้ใช้แทนข้อมูลครูจริง และไม่ใช่ผลตัดสินว่าต้องจัดสรรอัตรากำลังทันที
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown("### ใช้ข้อมูลจากไหน")
        st.write("ข้อมูลหลักมาจาก `public/dashboard-data.json` ซึ่งสร้างจากไฟล์ครูและไฟล์โรงเรียนเดิม")
        st.write("ใช้ `กลุ่มวิชาเอก.pdf` เป็นรายการมาตรฐานสำหรับจัดกลุ่มวิชาเอกและวิชาเอกย่อย")
        st.markdown("### ข้อมูลครูจริง")
        st.write("ใช้บอกว่าโรงเรียนยังไม่พบครูวิชาเอกย่อยใด เช่น เคมี ฟิสิกส์ ชีววิทยา หรือคอมพิวเตอร์")
    with right:
        st.markdown("### ML Model")
        st.write("ใช้ช่วยเรียงลำดับว่าโรงเรียนใดควรตรวจสอบก่อน โดยดูผลความเสี่ยงและการคาดการณ์จากชุดข้อมูลเดิม")
        st.markdown("### ข้อควรอ่าน")
        st.write(
            "ช่องว่างรายวิชาเอกย่อยเป็น baseline เพื่อช่วยชี้เป้าเบื้องต้น "
            "ไม่ใช่คำสั่งจัดสรรอัตรากำลังขั้นสุดท้าย หากต้องใช้ตัดสินเชิงนโยบายควรเพิ่มเกณฑ์ภาระงาน ชั่วโมงสอน ระดับชั้น และแผนการเปิดรายวิชาของแต่ละโรงเรียน"
        )
