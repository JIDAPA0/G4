"use client";

import { useEffect, useMemo, useState } from "react";

type SchoolRow = {
  school_code: string;
  school_name: string;
  area_name: string;
  school_size: string;
  total_students: number;
  actual_teachers: number;
  hired_teachers: number;
  calculated_min_math: number;
  actual_math_teachers: number;
  math_gap: number;
  current_math_status: "ขาด" | "ตามเกณฑ์" | "เกิน";
  future_shortage_prediction: number;
  sudden_shortage_risk_level: "สูง" | "ปานกลาง" | "ต่ำ" | "ไม่ระบุ";
};

type AreaSummary = {
  area_name: string;
  schools: number;
  shortage: number;
  met: number;
  surplus: number;
  future_shortage_total: number;
  high_risk: number;
  actual_math_teachers: number;
  required_math_teachers: number;
};

type MetricRow = {
  model: string;
  mae?: number;
  rmse?: number;
  accuracy?: number;
  macro_f1?: number;
  status: string;
};

type DashboardData = {
  generated_at: string;
  overview: {
    total_schools: number;
    target_areas: number;
    total_students: number;
    actual_math_teachers: number;
    required_math_teachers: number;
    future_shortage_total: number;
    high_risk_schools: number;
  };
  status_counts: Record<string, number>;
  risk_counts: Record<string, number>;
  area_summary: AreaSummary[];
  schools: SchoolRow[];
  top_future_shortage: SchoolRow[];
  top_risk: SchoolRow[];
  teacher_record_coverage: {
    teacher_rows: number;
    schools_with_teacher_records: number;
    note: string;
  };
  metrics: {
    future: MetricRow[];
    risk: MetricRow[];
    future_best: MetricRow;
    risk_best: MetricRow;
  };
};

const statusOrder = ["ขาด", "ตามเกณฑ์", "เกิน"];
const riskOrder = ["สูง", "ปานกลาง", "ต่ำ"];

function numberFormat(value: number) {
  return new Intl.NumberFormat("th-TH").format(value);
}

function percentFormat(value?: number) {
  if (value === undefined || value === null) return "-";
  return `${(value * 100).toFixed(1)}%`;
}

function statusClass(status: string) {
  if (status === "ขาด") return "tone-danger";
  if (status === "เกิน") return "tone-info";
  return "tone-good";
}

function riskClass(risk: string) {
  if (risk === "สูง") return "tone-danger";
  if (risk === "ปานกลาง") return "tone-warn";
  return "tone-good";
}

function MetricCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  accent: string;
}) {
  return (
    <section className={`metric-card ${accent}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </section>
  );
}

function BarList({
  title,
  rows,
  palette,
}: {
  title: string;
  rows: { label: string; value: number }[];
  palette: string;
}) {
  const maxValue = Math.max(1, ...rows.map((row) => row.value));
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>{title}</h2>
      </div>
      <div className="bar-list">
        {rows.map((row) => (
          <div className="bar-row" key={row.label}>
            <div className="bar-meta">
              <span>{row.label}</span>
              <strong>{numberFormat(row.value)}</strong>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill ${palette}`}
                style={{ width: `${Math.max(4, (row.value / maxValue) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [area, setArea] = useState("ทั้งหมด");
  const [status, setStatus] = useState("ทั้งหมด");
  const [risk, setRisk] = useState("ทั้งหมด");
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch("/dashboard-data.json")
      .then((response) => response.json())
      .then((payload: DashboardData) => setData(payload));
  }, []);

  const areas = useMemo(() => {
    if (!data) return ["ทั้งหมด"];
    return ["ทั้งหมด", ...data.area_summary.map((row) => row.area_name)];
  }, [data]);

  const filteredSchools = useMemo(() => {
    if (!data) return [];
    const needle = query.trim().toLowerCase();
    return data.schools.filter((school) => {
      const matchesArea = area === "ทั้งหมด" || school.area_name === area;
      const matchesStatus =
        status === "ทั้งหมด" || school.current_math_status === status;
      const matchesRisk =
        risk === "ทั้งหมด" || school.sudden_shortage_risk_level === risk;
      const matchesQuery =
        !needle ||
        school.school_name.toLowerCase().includes(needle) ||
        school.school_code.includes(needle);
      return matchesArea && matchesStatus && matchesRisk && matchesQuery;
    });
  }, [area, data, query, risk, status]);

  if (!data) {
    return (
      <main className="loading-shell">
        <div className="loading-block" />
      </main>
    );
  }

  const statusRows = statusOrder.map((item) => ({
    label: item,
    value: data.status_counts[item] ?? 0,
  }));
  const riskRows = riskOrder.map((item) => ({
    label: item,
    value: data.risk_counts[item] ?? 0,
  }));

  return (
    <main className="dashboard">
      <section className="top-band">
        <div className="title-group">
          <p>ระบบต้นแบบวิเคราะห์อัตรากำลัง</p>
          <h1>แดชบอร์ดครูคณิตศาสตร์</h1>
          <span>ข้อมูล 3 เขตพื้นที่เป้าหมาย · อัปเดต {data.generated_at}</span>
        </div>
        <div className="model-strip">
          <div>
            <span>Future Model</span>
            <strong>{data.metrics.future_best.model}</strong>
          </div>
          <div>
            <span>Risk Model</span>
            <strong>{data.metrics.risk_best.model}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard
          label="โรงเรียนทั้งหมด"
          value={numberFormat(data.overview.total_schools)}
          hint={`${numberFormat(data.overview.target_areas)} เขตพื้นที่`}
          accent="accent-navy"
        />
        <MetricCard
          label="ครูคณิตจริง"
          value={numberFormat(data.overview.actual_math_teachers)}
          hint={`ขั้นต่ำตามเกณฑ์ ${numberFormat(data.overview.required_math_teachers)}`}
          accent="accent-green"
        />
        <MetricCard
          label="คาดการณ์ขาด 1-5 ปี"
          value={numberFormat(data.overview.future_shortage_total)}
          hint="รวมจำนวนอัตราที่ควรเตรียมรองรับ"
          accent="accent-orange"
        />
        <MetricCard
          label="เสี่ยงสูง"
          value={numberFormat(data.overview.high_risk_schools)}
          hint="โรงเรียนที่ควรติดตามใกล้ชิด"
          accent="accent-red"
        />
      </section>

      <section className="analysis-grid">
        <BarList title="สถานะปัจจุบัน" rows={statusRows} palette="status-palette" />
        <BarList title="ระดับความเสี่ยงฉับพลัน" rows={riskRows} palette="risk-palette" />
      </section>

      <section className="panel wide">
        <div className="panel-head">
          <h2>สรุปรายเขตพื้นที่</h2>
        </div>
        <div className="area-grid">
          {data.area_summary.map((row) => (
            <article className="area-card" key={row.area_name}>
              <div>
                <h3>{row.area_name}</h3>
                <span>{numberFormat(row.schools)} โรงเรียน</span>
              </div>
              <dl>
                <div>
                  <dt>ขาด</dt>
                  <dd>{numberFormat(row.shortage)}</dd>
                </div>
                <div>
                  <dt>ตามเกณฑ์</dt>
                  <dd>{numberFormat(row.met)}</dd>
                </div>
                <div>
                  <dt>เกิน</dt>
                  <dd>{numberFormat(row.surplus)}</dd>
                </div>
                <div>
                  <dt>คาดขาด</dt>
                  <dd>{numberFormat(row.future_shortage_total)}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="panel wide">
        <div className="panel-head controls-head">
          <div>
            <h2>โรงเรียนทั้งหมด</h2>
            <span>{numberFormat(filteredSchools.length)} รายการที่ตรงเงื่อนไข</span>
          </div>
          <div className="controls">
            <label>
              <span>เขต</span>
              <select value={area} onChange={(event) => setArea(event.target.value)}>
                {areas.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <label>
              <span>สถานะ</span>
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option>ทั้งหมด</option>
                {statusOrder.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <label>
              <span>ความเสี่ยง</span>
              <select value={risk} onChange={(event) => setRisk(event.target.value)}>
                <option>ทั้งหมด</option>
                {riskOrder.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="search-control">
              <span>ค้นหา</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="รหัสหรือชื่อโรงเรียน"
              />
            </label>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>รหัส</th>
                <th>โรงเรียน</th>
                <th>เขต</th>
                <th>ขนาด</th>
                <th>ขั้นต่ำ</th>
                <th>ครูคณิตจริง</th>
                <th>สถานะ</th>
                <th>คาดขาด</th>
                <th>เสี่ยง</th>
              </tr>
            </thead>
            <tbody>
              {filteredSchools.map((school) => (
                <tr key={school.school_code}>
                  <td className="mono">{school.school_code}</td>
                  <td>{school.school_name}</td>
                  <td>{school.area_name}</td>
                  <td>{school.school_size}</td>
                  <td>{numberFormat(school.calculated_min_math)}</td>
                  <td>{numberFormat(school.actual_math_teachers)}</td>
                  <td>
                    <span className={`pill ${statusClass(school.current_math_status)}`}>
                      {school.current_math_status}
                    </span>
                  </td>
                  <td>{numberFormat(school.future_shortage_prediction)}</td>
                  <td>
                    <span className={`pill ${riskClass(school.sudden_shortage_risk_level)}`}>
                      {school.sudden_shortage_risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="analysis-grid">
        <section className="panel">
          <div className="panel-head">
            <h2>Performance: Future Shortage</h2>
          </div>
          <div className="metric-table">
            {data.metrics.future.map((row) => (
              <div className="metric-row" key={row.model}>
                <strong>{row.model}</strong>
                <span>MAE {row.mae?.toFixed(3) ?? "-"}</span>
                <span>Accuracy {percentFormat(row.accuracy)}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <div className="panel-head">
            <h2>Performance: Sudden Risk</h2>
          </div>
          <div className="metric-table">
            {data.metrics.risk.map((row) => (
              <div className="metric-row" key={row.model}>
                <strong>{row.model}</strong>
                <span>Accuracy {percentFormat(row.accuracy)}</span>
                <span>Macro F1 {row.macro_f1?.toFixed(3) ?? "-"}</span>
              </div>
            ))}
          </div>
        </section>
      </section>

      <section className="note-band">
        <strong>ข้อจำกัดข้อมูล Prototype</strong>
        <span>{data.teacher_record_coverage.note}</span>
      </section>
    </main>
  );
}
