import json
from pathlib import Path

import pandas as pd
import plotly.express as px
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
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(223, 246, 166, 0.36), transparent 32vw),
                radial-gradient(circle at top right, rgba(185, 173, 255, 0.22), transparent 34vw),
                {COLORS["background"]};
            color: {COLORS["ink"]};
        }}
        h1, h2, h3, p, span, label {{
            letter-spacing: 0 !important;
        }}
        div[data-testid="stHeader"] {{
            background: transparent;
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
            background: #fbfbf5;
            border: 1px solid #deddd2;
            border-radius: 8px;
            padding: 28px 30px;
            margin-bottom: 16px;
            box-shadow: 0 18px 36px rgba(58, 58, 45, 0.14);
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
        .stTabs [data-baseweb="tab-list"] {{
            background: rgba(247, 247, 240, 0.92);
            border: 1px solid {COLORS["line"]};
            border-radius: 8px;
            padding: 8px;
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 6px;
            color: {COLORS["muted"]};
            font-weight: 800;
        }}
        .stTabs [aria-selected="true"] {{
            background: {COLORS["purple"]};
            color: white;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid {COLORS["line"]};
            border-radius: 8px;
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


def plot_grouped_3d_like(df):
    plot_df = (
        df.groupby("วิชาเอกย่อย", as_index=False)["โรงเรียนที่ยังไม่พบครูวิชานี้"]
        .sum()
        .sort_values("โรงเรียนที่ยังไม่พบครูวิชานี้", ascending=False)
        .head(6)
        .merge(df, on="วิชาเอกย่อย", suffixes=("_รวม", ""))
    )
    fig = px.bar(
        plot_df,
        x="วิชาเอกย่อย",
        y="โรงเรียนที่ยังไม่พบครูวิชานี้",
        color="พื้นที่",
        barmode="group",
        text="โรงเรียนที่ยังไม่พบครูวิชานี้",
        color_discrete_sequence=CHART_COLORS,
        hover_data=["จำนวนครูที่พบ", "โรงเรียนที่พบครู"],
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        height=520,
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor="#f7f7f0",
        font={"color": COLORS["ink"]},
        legend_title_text="พื้นที่",
        margin=dict(l=30, r=20, t=20, b=70),
        yaxis_title="โรงเรียนที่ยังไม่พบครูวิชานี้",
        xaxis_title="วิชาเอกย่อย",
    )
    return fig


def pie_chart(title, df, names, values):
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.48,
        color_discrete_sequence=CHART_COLORS,
        title=title,
    )
    fig.update_layout(
        height=360,
        paper_bgcolor=COLORS["panel"],
        font={"color": COLORS["ink"]},
        margin=dict(l=10, r=10, t=55, b=10),
    )
    return fig


def render_downloads(df, basename):
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "ดาวน์โหลด CSV",
        csv,
        file_name=f"{basename}.csv",
        mime="text/csv",
        use_container_width=True,
    )


inject_css()
data = load_data()

areas = ["ทั้งหมด"] + [row["area_name"] for row in data["area_summary"]]
area_options = [row["area_name"] for row in data["area_summary"]]
group_options = {group["group_name"]: group["group_id"] for group in data["major_groups"]}

st.markdown(
    f"""
    <section class="hero">
      <p>ระบบต้นแบบวิเคราะห์อัตรากำลังครู</p>
      <h1>แดชบอร์ดกลุ่มวิชาเอกครู</h1>
      <div class="prototype">
        <strong>Prototype (ระบบต้นแบบ)</strong>
        <span>ใช้เพื่อทดลองวิเคราะห์และช่วยชี้เป้าเบื้องต้น ไม่ใช่ระบบตัดสินหรือจัดสรรอัตรากำลังจริง</span>
      </div>
      <span class="small-muted">วิเคราะห์จากไฟล์ครูตามวิชาเอก · ครอบคลุม {nf(data["overview"]["target_areas"])} เขตพื้นที่ · อัปเดต {data["generated_at"]}</span>
    </section>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(["ภาพรวม", "กลุ่มวิชา", "กราฟและพื้นที่", "รายโรงเรียน", "ข้อมูล/ข้อจำกัด"])

with tabs[0]:
    overview = data["overview"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("โรงเรียนในชุดข้อมูล", nf(overview["total_schools"]), f"มีข้อมูลครูใน {nf(overview['covered_schools'])} โรงเรียน")
    c2.metric("ครูที่นำมานับ", nf(overview["teacher_records"]), "นับจากรายการตำแหน่งครูในไฟล์ครู")
    complete_rate = overview["complete_group_school_pairs"] / overview["total_group_school_pairs"] * 100
    c3.metric("ความครบถ้วนรายกลุ่ม", f"{complete_rate:.1f}%", f"{nf(overview['complete_group_school_pairs'])} คู่โรงเรียน-กลุ่มวิชาครบ")
    c4.metric("โรงเรียนเสี่ยงสูงจากโมเดลเดิม", nf(overview["high_risk_schools"]), "ตัวช่วยจัดลำดับตรวจสอบ ไม่ใช่ผลยืนยัน")

    left, right = st.columns([1, 1])
    with left:
        st.subheader("กลุ่มวิชาที่ควรติดตามก่อน")
        group_df = pd.DataFrame(
            [
                {
                    "กลุ่มวิชา": group["group_name"],
                    "พบครู": group["actual_teachers"],
                    "โรงเรียนที่ครบ": group["complete_schools"],
                    "ช่องว่างวิชาเอกย่อย": group["shortage_subject_slots"],
                }
                for group in data["major_groups"]
            ]
        ).sort_values("ช่องว่างวิชาเอกย่อย", ascending=False)
        st.dataframe(group_df, use_container_width=True, hide_index=True)
    with right:
        st.subheader("วิชาเอกย่อยที่ควรติดตามบ่อย")
        subject_df = pd.DataFrame(
            [
                {
                    "กลุ่มวิชา": row["group_name"],
                    "วิชาเอกย่อย": row["subject"],
                    "โรงเรียนที่ยังไม่พบครูวิชานี้": row["shortage_schools"],
                }
                for row in data["top_subject_shortage"]
            ]
        )
        st.dataframe(subject_df, use_container_width=True, hide_index=True)

with tabs[1]:
    selected_group_name = st.selectbox("เลือกกลุ่มวิชา", list(group_options.keys()), key="group_tab")
    selected_group = get_group(data, group_options[selected_group_name])
    c1, c2, c3 = st.columns(3)
    c1.metric("ครูในกลุ่มนี้", nf(selected_group["actual_teachers"]), "จำนวนครูที่พบจากวิชาเอกในไฟล์ครู")
    c2.metric("โรงเรียนที่ครบ", nf(selected_group["complete_schools"]), f"{nf(selected_group['partial_schools'])} โรงเรียนยังขาดบางวิชา")
    c3.metric("ช่องว่างวิชาย่อย", nf(selected_group["shortage_subject_slots"]), "baseline อย่างน้อย 1 คนต่อวิชาย่อย")

    st.subheader("รายละเอียดวิชาเอกย่อย")
    group_subject_df = selected_group_subject_summary(data, selected_group["group_id"])
    st.dataframe(group_subject_df, use_container_width=True, hide_index=True)
    render_downloads(group_subject_df, f"subject-summary-{selected_group['group_id']}")

with tabs[2]:
    st.subheader("กราฟรายวิชาเอกย่อย เปรียบเทียบพื้นที่")
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
        st.plotly_chart(plot_grouped_3d_like(compare_df), use_container_width=True)
        with st.expander("อ่านกราฟนี้อย่างไร"):
            st.write(
                "แต่ละกลุ่มแท่งคือ 1 วิชาเอกย่อย สีของแท่งคือพื้นที่ที่เลือกไว้ "
                "ความสูงของแท่งคือจำนวนโรงเรียนในพื้นที่นั้นที่ยังไม่พบครูวิชาเอกย่อยนั้นในข้อมูลครู "
                "ถ้าแท่งสูงกว่า แปลว่าพื้นที่นั้นมีโรงเรียนที่ควรตรวจสอบต่อในวิชาเอกย่อยนั้นมากกว่า"
            )
        st.dataframe(compare_df, use_container_width=True, hide_index=True)
        render_downloads(compare_df, f"area-subject-compare-{graph_group['group_id']}")

    st.divider()
    st.subheader("Pie Chart วิเคราะห์รายพื้นที่")
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

    p1, p2, p3 = st.columns(3)
    p1.plotly_chart(pie_chart("สถานะของโรงเรียน", pd.DataFrame(status_rows), "สถานะ", "จำนวนโรงเรียน"), use_container_width=True)
    p2.plotly_chart(pie_chart("วิชาเอกย่อยที่ควรติดตาม", pd.DataFrame(shortage_rows), "วิชาเอกย่อย", "จำนวนโรงเรียน"), use_container_width=True)
    p3.plotly_chart(pie_chart("โครงสร้างครูตามกลุ่มวิชา", pd.DataFrame(teacher_rows), "กลุ่มวิชา", "จำนวนครูที่พบ"), use_container_width=True)

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
