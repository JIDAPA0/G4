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

type TeacherRosterRow = {
  teacher_ref: string;
  subject_group_id: string;
  subject_group: string;
  subject_major: string;
  teacher_major: string;
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
  teacher_roster: TeacherRosterRow[];
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

type PieSlice = {
  label: string;
  value: number;
  color: string;
};

const navItems = [
  { id: "overview", label: "ภาพรวม" },
  { id: "groups", label: "กลุ่มวิชา" },
  { id: "visuals", label: "กราฟ 3 มิติ" },
  { id: "schools", label: "รายโรงเรียน" },
  { id: "notes", label: "ข้อมูล/ข้อจำกัด" },
] as const;

const schoolStatusOrder = ["ทั้งหมด", "ขาดบางวิชา", "ครบ", "ไม่มีข้อมูล"];
const chartPalettes = [
  { front: "#2f6f91", top: "#6fa3c7", side: "#1f4a66" },
  { front: "#2f7d5c", top: "#72b892", side: "#1f5a40" },
  { front: "#8467ad", top: "#b497d5", side: "#5c477b" },
  { front: "#b76e28", top: "#e2a35e", side: "#7f4b1c" },
  { front: "#b5413d", top: "#df786d", side: "#7d2f35" },
  { front: "#3f7896", top: "#86b8cf", side: "#2d5368" },
  { front: "#6f7f38", top: "#aab56a", side: "#4d5927" },
  { front: "#9a5b7a", top: "#c58aa8", side: "#6c4057" },
  { front: "#4e668f", top: "#8fa5c8", side: "#374864" },
];
const statusPieColors: Record<string, string> = {
  ครบ: "#2b7a58",
  "ขาดบางวิชา": "#b5413d",
  ไม่มีข้อมูล: "#b76e28",
};

function numberFormat(value: number) {
  return new Intl.NumberFormat("th-TH").format(value);
}

function teacherCountText(value: number) {
  return `พบครู ${numberFormat(value)} คน`;
}

function teacherRecordText(value: number) {
  return `มีข้อมูลครู ${numberFormat(value)} รายการ`;
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

function PieChart({
  title,
  subtitle,
  slices,
}: {
  title: string;
  subtitle: string;
  slices: PieSlice[];
}) {
  const filtered = slices.filter((slice) => slice.value > 0);
  const total = filtered.reduce((sum, slice) => sum + slice.value, 0);
  let cursor = 0;
  const gradient = filtered.length
    ? filtered.map((slice) => {
        const start = cursor;
        cursor += (slice.value / Math.max(total, 1)) * 360;
        return `${slice.color} ${start}deg ${cursor}deg`;
      }).join(", ")
    : "#edf1f5 0deg 360deg";

  return (
    <article className="pie-card">
      <div>
        <h3>{title}</h3>
        <span>{subtitle}</span>
      </div>
      <div className="pie-body">
        <div className="pie-chart" style={{ background: `conic-gradient(${gradient})` }}>
          <div>
            <strong>{numberFormat(total)}</strong>
            <small>รวม</small>
          </div>
        </div>
        <div className="pie-legend">
          {(filtered.length ? filtered : [{ label: "ไม่มีข้อมูล", value: 0, color: "#9ca8b5" }]).map((slice) => (
            <div className="legend-row" key={slice.label}>
              <i style={{ background: slice.color }} />
              <span>{slice.label}</span>
              <strong>{numberFormat(slice.value)}</strong>
              <small>{percent(slice.value, total)}</small>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}

function downloadBlob(fileName: string, mimeType: string, content: BlobPart) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function csvCell(value: string | number) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

function rowsToCsv(headers: string[], rows: (string | number)[][]) {
  return [
    headers.map(csvCell).join(","),
    ...rows.map((row) => row.map(csvCell).join(",")),
  ].join("\n");
}

function rowsToExcelTable(title: string, headers: string[], rows: (string | number)[][]) {
  const cell = (value: string | number, tag = "td") =>
    `<${tag}>${String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</${tag}>`;
  return `
    <html>
      <head><meta charset="utf-8" /></head>
      <body>
        <table>
          <caption>${title}</caption>
          <thead><tr>${headers.map((header) => cell(header, "th")).join("")}</tr></thead>
          <tbody>${rows.map((row) => `<tr>${row.map((item) => cell(item)).join("")}</tr>`).join("")}</tbody>
        </table>
      </body>
    </html>
  `;
}

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [activeView, setActiveView] = useState<(typeof navItems)[number]["id"]>("overview");
  const [selectedGroupId, setSelectedGroupId] = useState("science");
  const [selectedSubject, setSelectedSubject] = useState("ทั้งหมด");
  const [area, setArea] = useState("ทั้งหมด");
  const [visualArea, setVisualArea] = useState("ทั้งหมด");
  const [compareAreas, setCompareAreas] = useState<string[]>([]);
  const [schoolStatus, setSchoolStatus] = useState("ทั้งหมด");
  const [query, setQuery] = useState("");
  const [selectedSchoolCode, setSelectedSchoolCode] = useState<string | null>(null);
  const [explainTopic, setExplainTopic] = useState<"visual" | "data" | "export" | null>(null);

  useEffect(() => {
    fetch("/dashboard-data.json")
      .then((response) => response.json())
      .then((payload: DashboardData) => {
        setData(payload);
        setSelectedGroupId(payload.major_groups[0]?.group_id ?? "science");
        setCompareAreas(payload.area_summary.slice(0, 3).map((row) => row.area_name));
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
  const selectedSchool = selectedSchoolCode
    ? data.schools.find((school) => school.school_code === selectedSchoolCode) ?? null
    : null;
  const visualAreaSchools = visualArea === "ทั้งหมด"
    ? data.schools
    : data.schools.filter((school) => school.area_name === visualArea);
  const compareAreaOptions = data.area_summary.map((row) => row.area_name);
  const activeCompareAreas = compareAreas.length ? compareAreas : compareAreaOptions.slice(0, 3);
  const compareSubjectRows = selectedGroup.subjects.map((subject) => {
    const areaRows = activeCompareAreas.map((areaName) => {
      const schoolsInArea = data.schools.filter((school) => school.area_name === areaName);
      let totalTeachers = 0;
      let schoolsWithTeacher = 0;
      let shortageSchools = 0;

      schoolsInArea.forEach((school) => {
        const group = school.subject_groups.find((item) => item.group_id === selectedGroup.group_id);
        const subjectRow = group?.subjects.find((item) => item.subject === subject);
        const teacherCount = subjectRow?.teacher_count ?? 0;

        totalTeachers += teacherCount;
        if (teacherCount > 0) schoolsWithTeacher += 1;
        if (subjectRow?.status === "ขาด") shortageSchools += 1;
      });

      return {
        area_name: areaName,
        group_id: selectedGroup.group_id,
        group_name: selectedGroup.group_name,
        subject,
        total_teachers: totalTeachers,
        schools_with_teacher: schoolsWithTeacher,
        shortage_schools: shortageSchools,
      };
    });

    return {
      subject,
      total_teachers: areaRows.reduce((sum, row) => sum + row.total_teachers, 0),
      shortage_schools: areaRows.reduce((sum, row) => sum + row.shortage_schools, 0),
      area_rows: areaRows,
    };
  }).sort((a, b) => b.shortage_schools - a.shortage_schools || b.total_teachers - a.total_teachers);
  const chartSubjects = compareSubjectRows.slice(0, 6);
  const chartRows = chartSubjects.flatMap((row) => row.area_rows);
  const maxChartShortage = Math.max(1, ...chartRows.map((row) => row.shortage_schools));
  const exportAreaSlug = activeCompareAreas.join("-").replace(/[\\/:*?"<>|]+/g, "-").replace(/\s+/g, "-");
  const areaGroupStatusSlices: PieSlice[] = ["ครบ", "ขาดบางวิชา", "ไม่มีข้อมูล"].map((status) => ({
    label: status,
    value: visualAreaSchools.filter((school) => {
      const group = school.subject_groups.find((item) => item.group_id === selectedGroup.group_id);
      return (group?.status ?? "ไม่มีข้อมูล") === status;
    }).length,
    color: statusPieColors[status],
  }));
  const areaSubjectShortageSlices: PieSlice[] = selectedGroup.subjects.map((subject, index) => ({
    label: subject,
    value: visualAreaSchools.filter((school) => {
      const group = school.subject_groups.find((item) => item.group_id === selectedGroup.group_id);
      return group?.subjects.find((item) => item.subject === subject)?.status === "ขาด";
    }).length,
    color: chartPalettes[index % chartPalettes.length].front,
  }));
  const areaTeacherGroupSlices: PieSlice[] = data.major_groups.map((group, index) => ({
    label: group.group_name.replace("กลุ่มวิชา", ""),
    value: visualAreaSchools.reduce((sum, school) => {
      const subjectGroup = school.subject_groups.find((item) => item.group_id === group.group_id);
      return sum + (subjectGroup?.actual_teachers ?? 0);
    }, 0),
    color: chartPalettes[index % chartPalettes.length].front,
  }));
  const areaCoverageRows = data.major_groups.map((group) => {
    const rows = visualAreaSchools.map((school) => school.subject_groups.find((item) => item.group_id === group.group_id));
    const shortageSlots = rows.reduce((sum, row) => sum + (row?.missing_subjects.length ?? 0), 0);
    const actualTeachers = rows.reduce((sum, row) => sum + (row?.actual_teachers ?? 0), 0);
    const completeSchools = rows.filter((row) => row?.status === "ครบ").length;
    return {
      group_id: group.group_id,
      group_name: group.group_name,
      actual_teachers: actualTeachers,
      complete_schools: completeSchools,
      shortage_slots: shortageSlots,
    };
  }).sort((a, b) => b.shortage_slots - a.shortage_slots);

  function toggleCompareArea(areaName: string) {
    setCompareAreas((current) => {
      if (current.includes(areaName)) {
        return current.length === 1 ? current : current.filter((item) => item !== areaName);
      }
      return [...current, areaName];
    });
  }

  function exportSubjectCsv() {
    const rows = compareSubjectRows.flatMap((subjectRow) => subjectRow.area_rows).map((row) => [
      row.area_name,
      row.group_name,
      row.subject,
      row.total_teachers,
      row.schools_with_teacher,
      row.shortage_schools,
    ]);
    const csv = rowsToCsv(["พื้นที่", "กลุ่มวิชา", "วิชาเอกย่อย", "จำนวนครูที่พบ", "โรงเรียนที่พบครู", "โรงเรียนที่ยังไม่พบครูวิชานี้"], rows);
    downloadBlob(`subject-major-${selectedGroup.group_id}-${exportAreaSlug}.csv`, "text/csv;charset=utf-8", `\uFEFF${csv}`);
  }

  function exportSubjectExcel() {
    const rows = compareSubjectRows.flatMap((subjectRow) => subjectRow.area_rows).map((row) => [
      row.area_name,
      row.group_name,
      row.subject,
      row.total_teachers,
      row.schools_with_teacher,
      row.shortage_schools,
    ]);
    const html = rowsToExcelTable(
      `สรุปวิชาเอกย่อย - ${selectedGroup.group_name} - เทียบพื้นที่`,
      ["พื้นที่", "กลุ่มวิชา", "วิชาเอกย่อย", "จำนวนครูที่พบ", "โรงเรียนที่พบครู", "โรงเรียนที่ยังไม่พบครูวิชานี้"],
      rows,
    );
    downloadBlob(`subject-major-${selectedGroup.group_id}-${exportAreaSlug}.xls`, "application/vnd.ms-excel;charset=utf-8", html);
  }

  function exportSchoolCsv() {
    const rows = filteredSchools.map((school) => {
      const group = school.subject_groups.find((item) => item.group_id === selectedGroup.group_id);
      return [
        school.school_code,
        school.school_name,
        school.area_name,
        school.school_size,
        school.teacher_records,
        group?.group_name ?? selectedGroup.group_name,
        group?.actual_teachers ?? 0,
        group?.covered_subjects ?? 0,
        group?.required_subjects ?? 0,
        group?.status ?? "ไม่มีข้อมูล",
        (group?.missing_subjects ?? []).join(" | "),
        school.sudden_shortage_risk_level,
      ];
    });
    const csv = rowsToCsv(
      ["รหัสโรงเรียน", "โรงเรียน", "เขต", "ขนาดโรงเรียน", "จำนวนข้อมูลครูในไฟล์", "กลุ่มวิชา", "จำนวนครูในกลุ่มนี้", "วิชาที่พบครู", "วิชาทั้งหมด", "สถานะ", "วิชาที่ต้องติดตาม", "ระดับความเสี่ยงจากโมเดลเดิม"],
      rows,
    );
    downloadBlob(`schools-${selectedGroup.group_id}.csv`, "text/csv;charset=utf-8", `\uFEFF${csv}`);
  }

  function exportTeacherRosterCsv(school: SchoolRow) {
    const rows = school.teacher_roster.map((teacher) => [
      school.school_code,
      school.school_name,
      teacher.teacher_ref,
      teacher.subject_group,
      teacher.subject_major,
      teacher.teacher_major,
    ]);
    const csv = rowsToCsv(
      ["รหัสโรงเรียน", "ชื่อโรงเรียน", "รหัสอ้างอิงปิดบัง", "กลุ่มวิชา", "วิชาเอกย่อย", "วิชาเอกต้นทางในไฟล์ครู"],
      rows,
    );
    downloadBlob(`teacher-roster-${school.school_code}.csv`, "text/csv;charset=utf-8", `\uFEFF${csv}`);
  }

  function downloadChartPng() {
    const groupWidth = Math.max(140, activeCompareAreas.length * 42 + 32);
    const width = Math.max(1200, 160 + chartSubjects.length * groupWidth);
    const height = 720;
    const max = Math.max(1, ...chartRows.map((row) => row.shortage_schools));
    const bars = chartSubjects.map((subjectRow, subjectIndex) => {
      const baseX = 70 + subjectIndex * groupWidth;
      const subjectBars = subjectRow.area_rows.map((row) => {
        const areaColorIndex = Math.max(0, compareAreaOptions.indexOf(row.area_name));
        const palette = chartPalettes[areaColorIndex % chartPalettes.length];
        const barHeight = Math.max(22, (row.shortage_schools / max) * 340);
        const areaIndex = activeCompareAreas.indexOf(row.area_name);
        const x = baseX + areaIndex * 42;
        const y = 540 - barHeight;
        return `
          <g>
            <rect x="${x}" y="${y}" width="28" height="${barHeight}" fill="${palette.front}" />
            <polygon points="${x},${y} ${x + 12},${y - 12} ${x + 40},${y - 12} ${x + 28},${y}" fill="${palette.top}" />
            <polygon points="${x + 28},${y} ${x + 40},${y - 12} ${x + 40},${540 - 12} ${x + 28},540" fill="${palette.side}" />
            <text x="${x + 14}" y="${Math.max(132, y - 20)}" text-anchor="middle" font-size="17" font-weight="800" fill="${palette.side}">${row.shortage_schools}</text>
          </g>
        `;
      }).join("");
      return `
        <g>
          ${subjectBars}
          <text x="${baseX + Math.max(22, activeCompareAreas.length * 21)}" y="590" text-anchor="middle" font-size="18" font-weight="700" fill="#1c2530">${subjectRow.subject}</text>
        </g>
      `;
    }).join("");
    const legend = activeCompareAreas.map((areaName, index) => {
      const areaColorIndex = Math.max(0, compareAreaOptions.indexOf(areaName));
      const palette = chartPalettes[areaColorIndex % chartPalettes.length];
      const x = 60 + index * 180;
      return `<g><rect x="${x}" y="135" width="16" height="16" fill="${palette.front}" /><text x="${x + 24}" y="149" font-size="16" fill="#657181">${areaName}</text></g>`;
    }).join("");
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
        <rect width="${width}" height="${height}" fill="#f4f6f8" />
        <text x="60" y="70" font-size="34" font-weight="800" fill="#1c2530">กราฟ 3 มิติ: ${selectedGroup.group_name}</text>
        <text x="60" y="110" font-size="22" fill="#657181">เทียบพื้นที่ที่เลือก · ความสูงแท่ง = จำนวนโรงเรียนที่ยังไม่พบครูวิชาเอกย่อยนั้น</text>
        ${legend}
        <line x1="70" y1="540" x2="1130" y2="540" stroke="#9ca8b5" stroke-width="2" />
        ${bars}
      </svg>
    `;
    const image = new Image();
    const svgBlob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) return;
      context.drawImage(image, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) downloadBlob(`chart-3d-${selectedGroup.group_id}-${exportAreaSlug}.png`, "image/png", blob);
        URL.revokeObjectURL(url);
      });
    };
    image.src = url;
  }

  return (
    <main className="dashboard">
      <section className="top-band">
        <div className="title-group">
          <p>ระบบต้นแบบวิเคราะห์อัตรากำลังครู Version 2</p>
          <h1>แดชบอร์ดกลุ่มวิชาเอกครู</h1>
          <span>
            วิเคราะห์จากไฟล์ครูตามวิชาเอก · ครอบคลุม {numberFormat(data.overview.target_areas)} เขตพื้นที่ · อัปเดต {data.generated_at}
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

      <div className="explain-strip">
        <span>ต้องการดูที่มาหรือวิธีคำนวณ?</span>
        <button type="button" onClick={() => setExplainTopic("data")}>แหล่งข้อมูล</button>
        <button type="button" onClick={() => setExplainTopic("visual")}>กราฟแสดงอะไร</button>
        <button type="button" onClick={() => setExplainTopic("export")}>การส่งออกไฟล์</button>
      </div>

      {activeView === "overview" && (
        <>
          <section className="metrics-grid">
            <MetricCard
              label="โรงเรียนในชุดข้อมูล"
              value={numberFormat(data.overview.total_schools)}
              hint={`มีข้อมูลครูใน ${numberFormat(data.overview.covered_schools)} โรงเรียน`}
              tone="accent-blue"
            />
            <MetricCard
              label="ครูที่นำมานับ"
              value={numberFormat(data.overview.teacher_records)}
              hint="นับจากรายการตำแหน่งครูในไฟล์ครู"
              tone="accent-green"
            />
            <MetricCard
              label="ความครบถ้วนรายกลุ่ม"
              value={completionRate}
              hint={`${numberFormat(data.overview.complete_group_school_pairs)} คู่โรงเรียน-กลุ่มวิชาครบ`}
              tone="accent-purple"
            />
            <MetricCard
              label="โรงเรียนเสี่ยงสูงจากโมเดลเดิม"
              value={numberFormat(data.overview.high_risk_schools)}
              hint="ตัวช่วยจัดลำดับตรวจสอบ ไม่ใช่ผลยืนยัน"
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
                      <span>{teacherCountText(group.actual_teachers)} · ข้อมูลครบ {numberFormat(group.complete_schools)} โรงเรียน</span>
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
                  <span>นับโรงเรียนที่ยังไม่พบครูวิชาเอกนั้นในข้อมูลครู</span>
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
            <MetricCard label="ครูในกลุ่มนี้" value={numberFormat(selectedGroup.actual_teachers)} hint="จำนวนครูที่พบจากวิชาเอกในไฟล์ครู" tone="accent-green" />
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
                  <span>{teacherCountText(subject.total_teachers)} · พบใน {numberFormat(subject.schools_with_teacher)} โรงเรียน</span>
                </div>
                <b>{numberFormat(subject.shortage_schools)}</b>
                <ProgressBar value={subject.shortage_schools} max={maxSubjectShortage} tone="fill-danger" />
              </button>
            ))}
          </div>
        </section>
      )}

      {activeView === "visuals" && (
        <section className="visual-layout">
          <section className="panel visual-panel">
            <div className="panel-head split-head">
              <div>
                <h2>กราฟ 3 มิติรายวิชาเอกย่อย</h2>
                <span>ติ๊กหลายพื้นที่เพื่อเทียบจำนวนโรงเรียนที่ยังไม่มีครูวิชาเอกนั้นในแต่ละเขต</span>
              </div>
              <div className="visual-actions">
                <select value={selectedGroupId} onChange={(event) => {
                  setSelectedGroupId(event.target.value);
                  setSelectedSubject("ทั้งหมด");
                }}>
                  {data.major_groups.map((group) => (
                    <option key={group.group_id} value={group.group_id}>{group.group_name}</option>
                  ))}
                </select>
                <button type="button" onClick={downloadChartPng}>ภาพ PNG</button>
                <button type="button" onClick={exportSubjectCsv}>CSV</button>
                <button type="button" onClick={exportSubjectExcel}>Excel</button>
                <button type="button" onClick={() => setExplainTopic("visual")}>อธิบายกราฟนี้</button>
              </div>
            </div>

            <div className="compare-toolbar" aria-label="เลือกพื้นที่สำหรับเทียบในกราฟ 3 มิติ">
              <div className="area-checks">
                {compareAreaOptions.map((areaName, index) => (
                  <label key={areaName}>
                    <input
                      checked={activeCompareAreas.includes(areaName)}
                      onChange={() => toggleCompareArea(areaName)}
                      type="checkbox"
                    />
                    <i style={{ ["--area-color" as string]: chartPalettes[index % chartPalettes.length].front }} />
                    <span>{areaName}</span>
                  </label>
                ))}
              </div>
              <div className="compare-actions">
                <button type="button" onClick={() => setCompareAreas(compareAreaOptions)}>เลือกทุกพื้นที่</button>
                <button type="button" onClick={() => setCompareAreas(compareAreaOptions.slice(0, 3))}>เลือก 3 พื้นที่แรก</button>
              </div>
            </div>

            <div className="viz-3d-scene compare-3d-scene" aria-label={`กราฟ 3 มิติ ${selectedGroup.group_name} เทียบพื้นที่`}>
              {chartSubjects.map((subjectRow, subjectIndex) => (
                <div className="bar3d-group" key={subjectRow.subject}>
                  <div className="bar3d-set">
                    {subjectRow.area_rows.map((row, areaIndex) => {
                      const height = Math.max(34, (row.shortage_schools / maxChartShortage) * 250);
                      const areaColorIndex = Math.max(0, compareAreaOptions.indexOf(row.area_name));
                      const palette = chartPalettes[areaColorIndex % chartPalettes.length];
                      return (
                        <button
                          className="bar3d-wrap compare-bar"
                          key={`${row.subject}-${row.area_name}`}
                          onClick={() => {
                            setSelectedSubject(row.subject);
                            setArea(row.area_name);
                            setActiveView("schools");
                          }}
                          style={{
                            ["--bar-height" as string]: `${height}px`,
                            ["--delay" as string]: `${(subjectIndex * activeCompareAreas.length + areaIndex) * 28}ms`,
                            ["--bar-front" as string]: palette.front,
                            ["--bar-top" as string]: palette.top,
                            ["--bar-side" as string]: palette.side,
                          }}
                          title={`${row.area_name}: ${numberFormat(row.shortage_schools)} โรงเรียนที่ยังไม่พบครูวิชา ${row.subject}`}
                          type="button"
                        >
                          <span className="bar3d-value">{numberFormat(row.shortage_schools)}</span>
                          <span className="bar3d" />
                          <small>{teacherCountText(row.total_teachers)}</small>
                          <em>{row.area_name.replace("สำนักงานเขตพื้นที่การศึกษา", "สพท.")}</em>
                        </button>
                      );
                    })}
                  </div>
                  <strong>{subjectRow.subject}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="panel visual-panel">
            <div className="panel-head split-head">
              <div>
                <h2>Pie Chart วิเคราะห์รายพื้นที่</h2>
                <span>เลือกพื้นที่เพื่อดูสัดส่วนสถานะ วิชาที่ขาด และโครงสร้างครูตามกลุ่มวิชา</span>
              </div>
              <div className="visual-actions">
                <select value={visualArea} onChange={(event) => setVisualArea(event.target.value)}>
                  {areas.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="area-insight-strip">
              <MetricCard
                label="โรงเรียนในพื้นที่ที่เลือก"
                value={numberFormat(visualAreaSchools.length)}
                hint={visualArea === "ทั้งหมด" ? "รวมทุกเขตพื้นที่" : visualArea}
                tone="accent-blue"
              />
              <MetricCard
                label="ช่องว่างกลุ่มที่เลือก"
                value={numberFormat(areaSubjectShortageSlices.reduce((sum, row) => sum + row.value, 0))}
                hint={selectedGroup.group_name}
                tone="accent-red"
              />
              <MetricCard
                label="ครูทุกกลุ่มในพื้นที่"
                value={numberFormat(areaTeacherGroupSlices.reduce((sum, row) => sum + row.value, 0))}
                hint="นับจากข้อมูลครูในไฟล์"
                tone="accent-green"
              />
            </div>

            <div className="pie-grid">
              <PieChart
                title="สถานะของโรงเรียนในกลุ่มที่เลือก"
                subtitle={`${selectedGroup.group_name} · ${visualArea}`}
                slices={areaGroupStatusSlices}
              />
              <PieChart
                title="วิชาเอกย่อยที่ยังไม่มีครู"
                subtitle="สัดส่วนช่องว่างภายในกลุ่มที่เลือก"
                slices={areaSubjectShortageSlices}
              />
              <PieChart
                title="โครงสร้างครูตามกลุ่มวิชา"
                subtitle={`จำนวนครูที่พบใน ${visualArea}`}
                slices={areaTeacherGroupSlices}
              />
            </div>
          </section>

          <section className="panel chart-table-panel">
            <div className="panel-head">
              <div>
                <h2>ตารางประกอบกราฟ</h2>
                <span>ข้อมูลชุดเดียวกับกราฟ · เทียบ {numberFormat(activeCompareAreas.length)} พื้นที่ที่ติ๊กไว้</span>
              </div>
            </div>
            <div className="table-wrap compact-table balanced-table">
              <table>
                <thead>
                  <tr>
                    <th>วิชาเอกย่อย</th>
                    <th>พื้นที่</th>
                    <th>จำนวนครูที่พบ</th>
                    <th>โรงเรียนที่พบครู</th>
                    <th>โรงเรียนที่ยังไม่พบครูวิชานี้</th>
                  </tr>
                </thead>
                <tbody>
                  {compareSubjectRows.flatMap((subjectRow) => subjectRow.area_rows).map((row) => (
                    <tr key={`${row.subject}-${row.area_name}`}>
                      <td><strong>{row.subject}</strong></td>
                      <td>{row.area_name}</td>
                      <td>{numberFormat(row.total_teachers)}</td>
                      <td>{numberFormat(row.schools_with_teacher)}</td>
                      <td>{numberFormat(row.shortage_schools)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel chart-table-panel">
            <div className="panel-head">
              <div>
                <h2>ตารางสรุปพื้นที่</h2>
                <span>เรียงกลุ่มวิชาตามจำนวนช่องว่างในพื้นที่ที่เลือก</span>
              </div>
            </div>
            <div className="table-wrap compact-table balanced-table">
              <table>
                <thead>
                  <tr>
                    <th>กลุ่มวิชา</th>
                    <th>จำนวนครูที่พบในพื้นที่</th>
                    <th>โรงเรียนที่ครบ</th>
                    <th>ช่องว่างวิชาเอกย่อย</th>
                  </tr>
                </thead>
                <tbody>
                  {areaCoverageRows.map((row) => (
                    <tr key={row.group_id}>
                      <td><strong>{row.group_name}</strong></td>
                      <td>{numberFormat(row.actual_teachers)}</td>
                      <td>{numberFormat(row.complete_schools)}</td>
                      <td>{numberFormat(row.shortage_slots)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel export-panel">
            <h2>ส่งออกข้อมูลรายโรงเรียน</h2>
            <p>
              ปุ่มนี้ส่งออกตารางโรงเรียนตามตัวกรองปัจจุบัน พร้อมจำนวนครูที่พบในกลุ่มที่เลือก สถานะครบ/ขาดบางวิชา และรายชื่อวิชาที่ควรติดตาม
            </p>
            <div className="export-actions">
              <button type="button" onClick={exportSchoolCsv}>ดาวน์โหลด CSV รายโรงเรียน</button>
              <button type="button" onClick={() => setActiveView("schools")}>ไปดูตารางรายโรงเรียน</button>
            </div>
          </section>
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
                  <th>รหัสโรงเรียน</th>
                  <th>ชื่อโรงเรียน</th>
                  <th>เขต</th>
                  <th>ขนาดโรงเรียน</th>
                  <th>ข้อมูลครูในไฟล์</th>
                  <th>ครูที่พบในกลุ่มนี้</th>
                  <th>ครบวิชาย่อย</th>
                  <th>สถานะ</th>
                  <th>วิชาที่ควรติดตาม</th>
                  <th>ความเสี่ยงจากโมเดลเดิม</th>
                  <th>บัญชีครู</th>
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
                      <td className="mono school-code-cell">{school.school_code}</td>
                      <td>
                        <strong>{school.school_name}</strong>
                      </td>
                      <td>{school.area_name}</td>
                      <td>{school.school_size || "ไม่ระบุ"}</td>
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
                      <td>
                        <button className="table-action" type="button" onClick={() => setSelectedSchoolCode(school.school_code)}>
                          ดูรายชื่อครู {numberFormat(school.teacher_roster.length)} รายการ
                        </button>
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
          <article className="panel guide-panel">
            <h2>คู่มือการใช้แต่ละส่วน</h2>
            <div className="guide-grid">
              <div>
                <strong>ภาพรวม</strong>
                <span>ใช้ดูจำนวนโรงเรียน จำนวนข้อมูลครู ความครบถ้วนรายกลุ่ม และกลุ่มวิชาที่ควรติดตามก่อน</span>
              </div>
              <div>
                <strong>กลุ่มวิชา</strong>
                <span>ใช้เจาะจากกลุ่มใหญ่ไปยังวิชาเอกย่อย เช่น วิทยาศาสตร์และเทคโนโลยี ไปดูเคมี ฟิสิกส์ ชีววิทยา</span>
              </div>
              <div>
                <strong>กราฟ 3 มิติ</strong>
                <span>ใช้ดูภาพรวมเชิงกราฟ เลือกกลุ่ม/พื้นที่ และส่งออกเป็นภาพ PNG, CSV หรือไฟล์ที่เปิดใน Excel ได้</span>
              </div>
              <div>
                <strong>รายโรงเรียน</strong>
                <span>ใช้ค้นโรงเรียน เลือกกลุ่มวิชา ดูวิชาที่ควรติดตาม และเปิดบัญชีครูแบบรหัสปิดบังรายโรงเรียน</span>
              </div>
            </div>
          </article>

          <article className="panel source-panel">
            <h2>แหล่งข้อมูลที่ใช้</h2>
            <dl className="source-list">
              <div>
                <dt>teachers.xlsx</dt>
                <dd>ข้อมูลครูรายบุคคลที่ใช้ระบุกลุ่มวิชาเอก วิชาเอกย่อย และจำนวนครูในแต่ละโรงเรียน</dd>
              </div>
              <div>
                <dt>schools.xlsx</dt>
                <dd>ข้อมูลโรงเรียน เขตพื้นที่ จำนวนนักเรียน จำนวนครูรวม ขนาดโรงเรียน และข้อมูลพื้นฐานระดับโรงเรียน</dd>
              </div>
              <div>
                <dt>school_math_analysis.xlsx</dt>
                <dd>ข้อมูลวิเคราะห์เดิมเรื่องครูคณิต สถานะ ขาด/ตามเกณฑ์/เกิน และผลความเสี่ยงที่ใช้ประกอบการจัดลำดับติดตาม</dd>
              </div>
              <div>
                <dt>กลุ่มวิชาเอก.pdf</dt>
                <dd>รายการมาตรฐานที่ใช้จัดกลุ่มวิชา 8 กลุ่ม และวิชาเอกย่อย 20 รายการ</dd>
              </div>
            </dl>
          </article>

          <article className="panel">
            <h2>นิยาม Version 2</h2>
            <p>
              ระบบนับครูจากไฟล์ครูโดยดูวิชาเอกเป็นหลัก แล้วจัดเข้ากลุ่มตามรายการใน {data.taxonomy_source}
              สำหรับรายวิชาเอกย่อย ถ้าพบครู 1 คนจะแสดง 1 ถ้าพบ 2 คนจะแสดง 2 และถ้าไม่พบข้อมูลครูในวิชานั้นจะแสดงเป็นช่องว่างที่ต้องติดตาม
            </p>
          </article>

          <article className="panel model-panel">
            <h2>โมเดลและตัวชี้วัด</h2>
            <p>
              ค่า “ความเสี่ยงจากโมเดลเดิม” และผลคาดการณ์บางส่วนมาจากโมเดลที่พัฒนาจากชุดข้อมูลเดิม เพื่อช่วยจัดลำดับโรงเรียนที่ควรติดตาม
              ไม่ใช่ผลตัดสินเชิงนโยบายอัตโนมัติ
            </p>
            <div className="model-grid">
              <div>
                <strong>Future Shortage</strong>
                <span>ใช้ประเมินจำนวนครูที่ควรเตรียมเพิ่มในอนาคต โดยอาศัยข้อมูลครูที่มีอยู่และปัจจัยเกษียณ/ความขาดแคลนเดิม</span>
              </div>
              <div>
                <strong>Sudden Risk</strong>
                <span>ใช้จัดระดับความเสี่ยงฉับพลัน เช่น สูง ปานกลาง ต่ำ เพื่อช่วยเลือกโรงเรียนที่ควรตรวจสอบก่อน</span>
              </div>
            </div>
          </article>

          <article className="panel">
            <h2>ข้อควรอ่าน</h2>
            <p>{data.teacher_record_coverage.note}</p>
            <p>
              ช่องว่างรายวิชาเอกย่อยใน v2 เป็น baseline เพื่อช่วยชี้เป้าวิชาที่ไม่มีครูตามวิชาเอกในข้อมูล ไม่ใช่คำสั่งจัดสรรอัตรากำลังขั้นสุดท้าย
              หากต้องใช้ตัดสินเชิงนโยบายควรเพิ่มเกณฑ์ภาระงาน ชั่วโมงสอน ระดับชั้น และแผนการเปิดรายวิชาของแต่ละโรงเรียน
            </p>
            <p>
              รายละเอียดครูรายโรงเรียนบนเว็บ public ใช้รหัสอ้างอิงปิดบัง เช่น REF-001 แทนรหัสครู/ตำแหน่งจริง เพื่อคุ้มครองข้อมูลบุคคล
            </p>
          </article>
          <article className="panel area-panel">
            <h2>สรุปรายเขตพื้นที่</h2>
            <div className="area-grid">
              {data.area_summary.map((row) => (
                <div className="area-card" key={row.area_name}>
                  <strong>{row.area_name}</strong>
                  <span>{numberFormat(row.schools)} โรงเรียน · {teacherRecordText(row.teacher_records)}</span>
                  <small>ครอบคลุม {numberFormat(row.covered_schools)} โรงเรียน · โมเดลเดิม: เสี่ยงสูง {numberFormat(row.high_risk)}</small>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}

      {explainTopic && (
        <div className="modal-backdrop" role="presentation" onClick={() => setExplainTopic(null)}>
          <section className="explain-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <button className="modal-close" type="button" onClick={() => setExplainTopic(null)}>ปิด</button>
            {explainTopic === "data" && (
              <>
                <h2>ใช้ข้อมูลจากไหน</h2>
                <p>
                  ข้อมูลหลักมาจากไฟล์ครูรายบุคคล `teachers.xlsx` ที่แปลงจากไฟล์ครูดิบ และใช้ `กลุ่มวิชาเอก.pdf`
                  เป็นรายการมาตรฐานสำหรับจัดกลุ่มวิชาเอก 8 กลุ่ม และวิชาเอกย่อย 20 รายการ
                </p>
                <p>
                  ระบบนับเฉพาะแถวที่เป็นตำแหน่งครู จากนั้นอ่านคอลัมน์กลุ่มวิชาเอกตามมาตรฐาน สาขาวิชาเอกที่บรรจุ และวุฒิการศึกษา
                  เพื่อ map เป็นกลุ่มวิชาและวิชาเอกย่อย เช่น เคมี ฟิสิกส์ ชีววิทยา เทคโนโลยี หรือคอมพิวเตอร์
                </p>
              </>
            )}
            {explainTopic === "visual" && (
              <>
                <h2>อ่านกราฟ 3 มิติอย่างไร</h2>
                <p>
                  กราฟนี้ใช้ดูว่าแต่ละพื้นที่ยังไม่พบครูวิชาเอกย่อยใดมากน้อยแค่ไหน โดยเริ่มจากเลือกกลุ่มวิชา เช่น
                  วิทยาศาสตร์และเทคโนโลยี จากนั้นติ๊กพื้นที่ที่ต้องการเทียบกัน ระบบจะแสดงวิชาเอกย่อยที่ควรติดตามก่อน
                  เช่น เคมี ฟิสิกส์ ชีววิทยา เทคโนโลยี หรือคอมพิวเตอร์
                </p>
                <p>
                  แต่ละกลุ่มแท่งคือ 1 วิชาเอกย่อย ส่วนสีของแท่งคือพื้นที่ที่เลือกไว้ ความสูงของแท่งคือจำนวนโรงเรียนในพื้นที่นั้น
                  ที่ยังไม่พบครูวิชาเอกย่อยนั้นในข้อมูลครู ตัวเลขบนแท่งคือจำนวนโรงเรียน และข้อความใต้แท่งบอกจำนวนครูที่พบในพื้นที่นั้น
                </p>
                <p>
                  ถ้าแท่งของพื้นที่ใดสูงกว่า แปลว่าพื้นที่นั้นมีโรงเรียนที่ควรตรวจสอบต่อในวิชาเอกย่อยนั้นมากกว่า กดที่แท่งได้เลยเพื่อไปดูรายชื่อโรงเรียน
                  ที่เกี่ยวข้อง พร้อมตัวกรองพื้นที่และวิชาเอกย่อยนั้น
                </p>
                <p>
                  Pie Chart รายพื้นที่ใช้โรงเรียนในเขตที่เลือกเป็นฐาน: วงแรกบอกสถานะครบ/ขาดบางวิชาของกลุ่มวิชาที่เลือก
                  วงที่สองบอกว่าวิชาย่อยใดเป็นสัดส่วนของช่องว่างมากที่สุด และวงที่สามบอกสัดส่วนจำนวนครูจริงตามกลุ่มวิชาในพื้นที่นั้น
                </p>
                <p>
                  การคำนวณช่องว่างรายวิชาใช้ baseline ว่า หากโรงเรียนมีข้อมูลครูแล้ว แต่ไม่มีครูในวิชาเอกย่อยนั้นเลย จะนับเป็น 1 ช่องว่างที่ควรติดตาม
                  วิธีนี้ใช้เพื่อชี้เป้าเบื้องต้น ไม่ใช่เกณฑ์จัดสรรอัตรากำลังขั้นสุดท้าย
                </p>
              </>
            )}
            {explainTopic === "export" && (
              <>
                <h2>ส่งออกไปใช้ต่ออย่างไร</h2>
                <p>
                  ปุ่ม CSV จะได้ไฟล์ข้อความเปิดต่อใน Excel, Google Sheets, BI tools หรือระบบวิเคราะห์อื่นได้ ส่วนปุ่ม Excel จะได้ไฟล์ `.xls`
                  แบบตารางที่ Excel เปิดได้ทันทีโดยคงหัวคอลัมน์ภาษาไทยไว้
                </p>
                <p>
                  ปุ่มภาพ PNG สร้างภาพจากข้อมูลกราฟชุดปัจจุบัน เหมาะสำหรับนำไปใส่รายงาน สไลด์ หรือเอกสารประกอบการประชุม
                </p>
              </>
            )}
          </section>
        </div>
      )}

      {selectedSchool && (
        <div className="modal-backdrop" role="presentation" onClick={() => setSelectedSchoolCode(null)}>
          <section className="detail-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <button className="modal-close" type="button" onClick={() => setSelectedSchoolCode(null)}>ปิด</button>
            <div className="detail-head">
              <div>
                <h2>{selectedSchool.school_name}</h2>
                <span className="mono">รหัสโรงเรียน {selectedSchool.school_code}</span>
                <p>{selectedSchool.area_name} · {teacherRecordText(selectedSchool.teacher_roster.length)} ในไฟล์</p>
              </div>
              <button type="button" onClick={() => exportTeacherRosterCsv(selectedSchool)}>ดาวน์โหลด CSV บัญชีครู</button>
            </div>

            <div className="detail-summary-grid">
              {selectedSchool.subject_groups.map((group) => (
                <article key={group.group_id}>
                  <strong>{group.group_name.replace("กลุ่มวิชา", "")}</strong>
                  <span>{teacherCountText(group.actual_teachers)}</span>
                  <small>{group.status}</small>
                </article>
              ))}
            </div>

            <div className="table-wrap teacher-table">
              <table>
                <thead>
                  <tr>
                    <th>รหัสอ้างอิงปิดบัง</th>
                    <th>กลุ่มวิชา</th>
                    <th>วิชาเอกย่อย</th>
                    <th>วิชาเอกต้นทางในไฟล์ครู</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedSchool.teacher_roster.map((teacher, index) => (
                    <tr key={`${teacher.teacher_ref}-${index}`}>
                      <td className="mono school-code-cell">{teacher.teacher_ref || "ไม่ระบุ"}</td>
                      <td>{teacher.subject_group}</td>
                      <td><strong>{teacher.subject_major}</strong></td>
                      <td>{teacher.teacher_major}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="detail-note">
              รหัสนี้เป็นรหัสอ้างอิงปิดบังสำหรับหน้าเว็บ public ไม่ใช่รหัสครูหรือตำแหน่งจริง และไม่สามารถใช้ย้อนกลับเป็นตัวบุคคลจากหน้าเว็บนี้ได้
            </p>
          </section>
        </div>
      )}
    </main>
  );
}
