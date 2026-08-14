"use client";

import { useEffect, useMemo, useState } from "react";

type SubjectRow = {
  subject: string;
  teacher_count: number;
  status: "มี" | "ขาด" | "ไม่มีข้อมูล";
};

type SchoolSubjectGroup = {
  group_id: string;
  group_name: string;
  actual_teachers: number;
  required_subjects: number;
  covered_subjects: number;
  missing_subjects: string[];
  status: "ครบ" | "ขาดบางวิชา" | "ไม่มีข้อมูล";
  subjects: SubjectRow[];
};

type SchoolRow = {
  school_code: string;
  school_name: string;
  area_name: string;
  school_size: string;
  total_students: number;
  actual_teachers: number;
  teacher_records: number;
  has_teacher_records: boolean;
  future_shortage_prediction: number;
  sudden_shortage_risk_level: "สูง" | "ปานกลาง" | "ต่ำ" | "ไม่ระบุ";
  subject_groups: SchoolSubjectGroup[];
};

type MajorGroup = {
  group_id: string;
  group_name: string;
  subjects: string[];
  actual_teachers: number;
  required_subject_slots: number;
  shortage_subject_slots: number;
  complete_schools: number;
  partial_schools: number;
  missing_record_schools: number;
  top_shortage_subjects: { subject: string; schools: number }[];
};

type SubjectSummary = {
  group_id: string;
  group_name: string;
  subject: string;
  total_teachers: number;
  schools_with_teacher: number;
  shortage_schools: number;
};

type AreaSummary = {
  area_name: string;
  schools: number;
  teacher_records: number;
  covered_schools: number;
  future_shortage_total: number;
  high_risk: number;
};

type DashboardData = {
  generated_at: string;
  version: string;
  taxonomy_source: string;
  overview: {
    total_schools: number;
    target_areas: number;
    total_students: number;
    teacher_records: number;
    covered_schools: number;
    official_major_groups: number;
    official_subjects: number;
    subject_shortage_slots: number;
    complete_group_school_pairs: number;
    total_group_school_pairs: number;
    future_shortage_total: number;
    high_risk_schools: number;
  };
  major_groups: MajorGroup[];
  subject_summary: SubjectSummary[];
  top_subject_shortage: SubjectSummary[];
  area_summary: AreaSummary[];
  schools: SchoolRow[];
  teacher_record_coverage: {
    teacher_rows: number;
    schools_with_teacher_records: number;
    note: string;
  };
};

const navItems = [
  { id: "overview", label: "ภาพรวม" },
  { id: "groups", label: "กลุ่มวิชา" },
  { id: "schools", label: "รายโรงเรียน" },
  { id: "notes", label: "ข้อมูล/ข้อจำกัด" },
] as const;

const schoolStatusOrder = ["ทั้งหมด", "ขาดบางวิชา", "ครบ", "ไม่มีข้อมูล"];

function numberFormat(value: number) {
  return new Intl.NumberFormat("th-TH").format(value);
}

function percent(value: number, total: number) {
  if (!total) return "0.0%";
  return `${((value / total) * 100).toFixed(1)}%`;
}

function statusClass(status: string) {
  if (status === "ขาด" || status === "ขาดบางวิชา" || status === "สูง") return "tone-danger";
  if (status === "ไม่มีข้อมูล" || status === "ปานกลาง") return "tone-warn";
  return "tone-good";
}

function MetricCard({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  tone: string;
}) {
  return (
    <article className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  );
}

function ProgressBar({ value, max, tone }: { value: number; max: number; tone: string }) {
  return (
    <div className="bar-track" aria-hidden="true">
      <div className={`bar-fill ${tone}`} style={{ width: `${Math.max(3, (value / Math.max(max, 1)) * 100)}%` }} />
    </div>
  );
}

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [activeView, setActiveView] = useState<(typeof navItems)[number]["id"]>("overview");
  const [selectedGroupId, setSelectedGroupId] = useState("science");
  const [selectedSubject, setSelectedSubject] = useState("ทั้งหมด");
  const [area, setArea] = useState("ทั้งหมด");
  const [schoolStatus, setSchoolStatus] = useState("ทั้งหมด");
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch("/dashboard-data.json")
      .then((response) => response.json())
      .then((payload: DashboardData) => {
        setData(payload);
        setSelectedGroupId(payload.major_groups[0]?.group_id ?? "science");
      });
  }, []);

  const selectedGroup = useMemo(() => {
    if (!data) return null;
    return data.major_groups.find((group) => group.group_id === selectedGroupId) ?? data.major_groups[0];
  }, [data, selectedGroupId]);

  const selectedSubjectRows = useMemo(() => {
    if (!data || !selectedGroup) return [];
    return data.subject_summary
      .filter((row) => row.group_id === selectedGroup.group_id)
      .sort((a, b) => b.shortage_schools - a.shortage_schools || b.total_teachers - a.total_teachers);
  }, [data, selectedGroup]);

  const areas = useMemo(() => {
    if (!data) return ["ทั้งหมด"];
    return ["ทั้งหมด", ...data.area_summary.map((row) => row.area_name)];
  }, [data]);

  const filteredSchools = useMemo(() => {
    if (!data || !selectedGroup) return [];
    const needle = query.trim().toLowerCase();
    return data.schools.filter((school) => {
      const group = school.subject_groups.find((item) => item.group_id === selectedGroup.group_id);
      const subject = group?.subjects.find((item) => item.subject === selectedSubject);
      const matchesArea = area === "ทั้งหมด" || school.area_name === area;
      const matchesStatus = schoolStatus === "ทั้งหมด" || group?.status === schoolStatus;
      const matchesSubject =
        selectedSubject === "ทั้งหมด" ||
        subject?.status === "ขาด" ||
        (selectedSubject !== "ทั้งหมด" && (subject?.teacher_count ?? 0) > 0);
      const matchesQuery =
        !needle ||
        school.school_name.toLowerCase().includes(needle) ||
        school.school_code.includes(needle);
      return matchesArea && matchesStatus && matchesSubject && matchesQuery;
    });
  }, [area, data, query, schoolStatus, selectedGroup, selectedSubject]);

  if (!data || !selectedGroup) {
    return (
      <main className="loading-shell">
        <div className="loading-block" />
      </main>
    );
  }

  const completionRate = percent(data.overview.complete_group_school_pairs, data.overview.total_group_school_pairs);
  const maxGroupShortage = Math.max(1, ...data.major_groups.map((group) => group.shortage_subject_slots));
  const maxSubjectShortage = Math.max(1, ...selectedSubjectRows.map((row) => row.shortage_schools));

  return (
    <main className="dashboard">
      <section className="top-band">
        <div className="title-group">
          <p>ระบบต้นแบบวิเคราะห์อัตรากำลังครู Version 2</p>
          <h1>แดชบอร์ดกลุ่มวิชาเอกครู</h1>
          <span>
            วิเคราะห์จากไฟล์ครูตามวิชาเอก · {numberFormat(data.overview.target_areas)} เขตพื้นที่ · อัปเดต {data.generated_at}
          </span>
        </div>
        <div className="hero-stat">
          <span>ช่องว่างรายวิชาเอก</span>
          <strong>{numberFormat(data.overview.subject_shortage_slots)}</strong>
          <small>จาก {numberFormat(data.overview.official_subjects)} วิชาเอกย่อยใน {numberFormat(data.overview.official_major_groups)} กลุ่ม</small>
        </div>
      </section>

      <nav className="view-tabs" aria-label="Dashboard sections">
        {navItems.map((item) => (
          <button
            className={activeView === item.id ? "active" : ""}
            key={item.id}
            onClick={() => setActiveView(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      {activeView === "overview" && (
        <>
          <section className="metrics-grid">
            <MetricCard
              label="โรงเรียนในชุดข้อมูล"
              value={numberFormat(data.overview.total_schools)}
              hint={`มี record ครู ${numberFormat(data.overview.covered_schools)} โรงเรียน`}
              tone="accent-blue"
            />
            <MetricCard
              label="ครูที่นำมานับ"
              value={numberFormat(data.overview.teacher_records)}
              hint="นับจากตำแหน่งครูในไฟล์ครู"
              tone="accent-green"
            />
            <MetricCard
              label="ความครบถ้วนรายกลุ่ม"
              value={completionRate}
              hint={`${numberFormat(data.overview.complete_group_school_pairs)} คู่โรงเรียน-กลุ่มวิชาครบ`}
              tone="accent-purple"
            />
            <MetricCard
              label="ความเสี่ยงสูงเดิม"
              value={numberFormat(data.overview.high_risk_schools)}
              hint="ใช้ร่วมกับโมเดลเดิมสำหรับจัดลำดับติดตาม"
              tone="accent-red"
            />
          </section>

          <section className="content-grid">
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>กลุ่มวิชาที่ควรดูต่อ</h2>
                  <span>เรียงตามจำนวนช่องว่างวิชาเอกย่อย</span>
                </div>
              </div>
              <div className="rank-list">
                {data.major_groups.map((group) => (
                  <button
                    className="rank-row"
                    key={group.group_id}
                    onClick={() => {
                      setSelectedGroupId(group.group_id);
                      setSelectedSubject("ทั้งหมด");
                      setActiveView("groups");
                    }}
                    type="button"
                  >
                    <div>
                      <strong>{group.group_name}</strong>
                      <span>{numberFormat(group.actual_teachers)} ครู · ครบ {numberFormat(group.complete_schools)} โรงเรียน</span>
                    </div>
                    <b>{numberFormat(group.shortage_subject_slots)}</b>
                    <ProgressBar value={group.shortage_subject_slots} max={maxGroupShortage} tone="fill-danger" />
                  </button>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>วิชาเอกย่อยที่ขาดบ่อย</h2>
                  <span>นับโรงเรียนที่ยังไม่มีครูวิชาเอกนั้นใน record</span>
                </div>
              </div>
              <div className="subject-list">
                {data.top_subject_shortage.map((subject) => (
                  <button
                    className="subject-row"
                    key={`${subject.group_id}-${subject.subject}`}
                    onClick={() => {
                      setSelectedGroupId(subject.group_id);
                      setSelectedSubject(subject.subject);
                      setActiveView("schools");
                    }}
                    type="button"
                  >
                    <span>{subject.group_name}</span>
                    <strong>{subject.subject}</strong>
                    <b>{numberFormat(subject.shortage_schools)} โรงเรียน</b>
                  </button>
                ))}
              </div>
            </section>
          </section>
        </>
      )}

      {activeView === "groups" && (
        <section className="panel">
          <div className="panel-head split-head">
            <div>
              <h2>เจาะกลุ่มวิชา</h2>
              <span>เลือกกลุ่มเพื่อดูวิชาเอกย่อย เช่น วิทยาศาสตร์และเทคโนโลยี ไปยัง เคมี/ฟิสิกส์/ชีววิทยา</span>
            </div>
            <select value={selectedGroupId} onChange={(event) => {
              setSelectedGroupId(event.target.value);
              setSelectedSubject("ทั้งหมด");
            }}>
              {data.major_groups.map((group) => (
                <option key={group.group_id} value={group.group_id}>{group.group_name}</option>
              ))}
            </select>
          </div>

          <div className="group-summary-band">
            <MetricCard label="ครูในกลุ่มนี้" value={numberFormat(selectedGroup.actual_teachers)} hint="นับจากวิชาเอกในไฟล์ครู" tone="accent-green" />
            <MetricCard label="โรงเรียนที่ครบ" value={numberFormat(selectedGroup.complete_schools)} hint={`${numberFormat(selectedGroup.partial_schools)} โรงเรียนยังขาดบางวิชา`} tone="accent-blue" />
            <MetricCard label="ช่องว่างวิชาย่อย" value={numberFormat(selectedGroup.shortage_subject_slots)} hint="baseline อย่างน้อย 1 คนต่อวิชาย่อย" tone="accent-red" />
          </div>

          <div className="drill-grid">
            {selectedSubjectRows.map((subject) => (
              <button
                className={`drill-card ${selectedSubject === subject.subject ? "selected" : ""}`}
                key={subject.subject}
                onClick={() => {
                  setSelectedSubject(subject.subject);
                  setActiveView("schools");
                }}
                type="button"
              >
                <div>
                  <strong>{subject.subject}</strong>
                  <span>{numberFormat(subject.total_teachers)} ครู · มีใน {numberFormat(subject.schools_with_teacher)} โรงเรียน</span>
                </div>
                <b>{numberFormat(subject.shortage_schools)}</b>
                <ProgressBar value={subject.shortage_schools} max={maxSubjectShortage} tone="fill-danger" />
              </button>
            ))}
          </div>
        </section>
      )}

      {activeView === "schools" && (
        <section className="panel">
          <div className="panel-head controls-head">
            <div>
              <h2>รายโรงเรียน</h2>
              <span>{numberFormat(filteredSchools.length)} โรงเรียนตามเงื่อนไข · กลุ่มที่เลือก: {selectedGroup.group_name}</span>
            </div>
            <div className="controls">
              <label>
                <span>กลุ่มวิชา</span>
                <select value={selectedGroupId} onChange={(event) => {
                  setSelectedGroupId(event.target.value);
                  setSelectedSubject("ทั้งหมด");
                }}>
                  {data.major_groups.map((group) => (
                    <option key={group.group_id} value={group.group_id}>{group.group_name}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>วิชาย่อย</span>
                <select value={selectedSubject} onChange={(event) => setSelectedSubject(event.target.value)}>
                  <option>ทั้งหมด</option>
                  {selectedGroup.subjects.map((subject) => (
                    <option key={subject}>{subject}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>เขต</span>
                <select value={area} onChange={(event) => setArea(event.target.value)}>
                  {areas.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>สถานะกลุ่ม</span>
                <select value={schoolStatus} onChange={(event) => setSchoolStatus(event.target.value)}>
                  {schoolStatusOrder.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label className="search-control">
                <span>ค้นหา</span>
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="รหัสหรือชื่อโรงเรียน" />
              </label>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>โรงเรียน</th>
                  <th>เขต</th>
                  <th>ครูทั้งหมดในไฟล์</th>
                  <th>ครูกลุ่มนี้</th>
                  <th>ครบวิชาย่อย</th>
                  <th>สถานะ</th>
                  <th>วิชาที่ต้องเติม</th>
                  <th>เสี่ยงเดิม</th>
                </tr>
              </thead>
              <tbody>
                {filteredSchools.map((school) => {
                  const group = school.subject_groups.find((item) => item.group_id === selectedGroup.group_id);
                  const missing = selectedSubject === "ทั้งหมด"
                    ? group?.missing_subjects ?? []
                    : (group?.subjects.find((item) => item.subject === selectedSubject)?.status === "ขาด" ? [selectedSubject] : []);
                  return (
                    <tr key={school.school_code}>
                      <td>
                        <strong>{school.school_name}</strong>
                        <span className="subtle mono">{school.school_code}</span>
                      </td>
                      <td>{school.area_name}</td>
                      <td>{numberFormat(school.teacher_records)}</td>
                      <td>{numberFormat(group?.actual_teachers ?? 0)}</td>
                      <td>{numberFormat(group?.covered_subjects ?? 0)} / {numberFormat(group?.required_subjects ?? 0)}</td>
                      <td>
                        <span className={`pill ${statusClass(group?.status ?? "ไม่มีข้อมูล")}`}>{group?.status ?? "ไม่มีข้อมูล"}</span>
                      </td>
                      <td>
                        <div className="chip-line">
                          {missing.length ? missing.slice(0, 4).map((subject) => <span className="chip" key={subject}>{subject}</span>) : <span className="subtle">ไม่มีช่องว่างในเงื่อนไขนี้</span>}
                          {missing.length > 4 && <span className="chip muted-chip">+{numberFormat(missing.length - 4)}</span>}
                        </div>
                      </td>
                      <td>
                        <span className={`pill ${statusClass(school.sudden_shortage_risk_level)}`}>{school.sudden_shortage_risk_level}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeView === "notes" && (
        <section className="notes-grid">
          <article className="panel">
            <h2>นิยาม Version 2</h2>
            <p>
              ระบบนับครูจากไฟล์ครูโดยดูวิชาเอกเป็นหลัก แล้วจัดเข้ากลุ่มตามรายการใน {data.taxonomy_source}
              สำหรับรายวิชาเอกย่อย ถ้ามีครู 1 คนจะแสดง 1 ถ้ามี 2 คนจะแสดง 2 และถ้าไม่มี record ในวิชานั้นจะแสดงเป็นช่องว่างที่ต้องติดตาม
            </p>
          </article>
          <article className="panel">
            <h2>ข้อควรอ่าน</h2>
            <p>{data.teacher_record_coverage.note}</p>
            <p>
              ช่องว่างรายวิชาเอกย่อยใน v2 เป็น baseline เพื่อช่วยชี้เป้าวิชาที่ไม่มีครูตามวิชาเอกในข้อมูล ไม่ใช่คำสั่งจัดสรรอัตรากำลังขั้นสุดท้าย
              หากต้องใช้ตัดสินเชิงนโยบายควรเพิ่มเกณฑ์ภาระงาน ชั่วโมงสอน ระดับชั้น และแผนการเปิดรายวิชาของแต่ละโรงเรียน
            </p>
          </article>
          <article className="panel area-panel">
            <h2>สรุปรายเขตพื้นที่</h2>
            <div className="area-grid">
              {data.area_summary.map((row) => (
                <div className="area-card" key={row.area_name}>
                  <strong>{row.area_name}</strong>
                  <span>{numberFormat(row.schools)} โรงเรียน · {numberFormat(row.teacher_records)} records ครู</span>
                  <small>ครอบคลุม {numberFormat(row.covered_schools)} โรงเรียน · เสี่ยงสูง {numberFormat(row.high_risk)}</small>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </main>
  );
}
