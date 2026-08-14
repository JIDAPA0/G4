import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = new URL("../", import.meta.url);
const dataDir = new URL("data/", root);
const outputDir = new URL("outputs/validation/", root);
const payloadPath = new URL("outputs/tmp/school_math_analysis_payload.json", root);
const outputPath = new URL("school_math_analysis.xlsx", dataDir);

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));

const analysisHeaders = [
  "school_code",
  "calculated_min_math",
  "actual_math_teachers",
  "current_math_status",
  "future_shortage_prediction",
  "sudden_shortage_risk_level",
];

function columnLetter(index) {
  let n = index + 1;
  let result = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    result = String.fromCharCode(65 + r) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

function styleHeader(range) {
  range.format = {
    fill: "#1F4E79",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: false,
  };
}

function styleTable(range) {
  range.format.borders = {
    preset: "all",
    style: "thin",
    color: "#D9E2F3",
  };
}

const workbook = Workbook.create();
const analysis = workbook.worksheets.add("school_math_analysis");
analysis.showGridLines = false;

const analysisValues = [
  analysisHeaders,
  ...payload.analysis.map((row) => analysisHeaders.map((header) => row[header] ?? "")),
];
const analysisLastRow = analysisValues.length;
const analysisLastCol = columnLetter(analysisHeaders.length - 1);
analysis.getRange(`A1:${analysisLastCol}${analysisLastRow}`).values = analysisValues;
styleHeader(analysis.getRange(`A1:${analysisLastCol}1`));
styleTable(analysis.getRange(`A1:${analysisLastCol}${analysisLastRow}`));
analysis.getRange(`A2:A${analysisLastRow}`).format.numberFormat = "@";
analysis.getRange(`B2:C${analysisLastRow}`).format.numberFormat = "#,##0";
analysis.getRange(`A1:${analysisLastCol}${analysisLastRow}`).format.autofitColumns();
analysis.getRange(`A1:${analysisLastCol}${analysisLastRow}`).format.autofitRows();
analysis.getRange("A:A").format.columnWidthPx = 120;
analysis.getRange("E:F").format.columnWidthPx = 210;
analysis.freezePanes.freezeRows(1);

analysis.getRange(`D2:D${analysisLastRow}`).conditionalFormats.add("containsText", {
  text: "ขาด",
  format: { fill: "#FCE4D6", font: { color: "#C00000", bold: true } },
});
analysis.getRange(`D2:D${analysisLastRow}`).conditionalFormats.add("containsText", {
  text: "ตามเกณฑ์",
  format: { fill: "#E2F0D9", font: { color: "#375623", bold: true } },
});
analysis.getRange(`D2:D${analysisLastRow}`).conditionalFormats.add("containsText", {
  text: "เกิน",
  format: { fill: "#DDEBF7", font: { color: "#1F4E79", bold: true } },
});

const summary = workbook.worksheets.add("summary");
summary.showGridLines = false;
summary.getRange("A1:B5").values = [
  ["metric", "count"],
  ["โรงเรียนทั้งหมด", payload.summary.total_schools],
  ["ขาด", payload.summary.shortage],
  ["ตามเกณฑ์", payload.summary.met],
  ["เกิน", payload.summary.surplus],
];
styleHeader(summary.getRange("A1:B1"));
styleTable(summary.getRange("A1:B5"));
summary.getRange("B2:B5").format.numberFormat = "#,##0";
summary.getRange("A1:B5").format.autofitColumns();

const rules = workbook.worksheets.add("rules");
rules.showGridLines = false;
rules.getRange("A1:C1").values = [["actual_teachers_min", "actual_teachers_max", "calculated_min_math"]];
rules.getRange(`A2:C${payload.rules.length + 1}`).values = payload.rules.map((rule) => [
  rule.actual_teachers_min,
  rule.actual_teachers_max ?? "234+",
  rule.calculated_min_math,
]);
styleHeader(rules.getRange("A1:C1"));
styleTable(rules.getRange(`A1:C${payload.rules.length + 1}`));
rules.getRange(`A2:C${payload.rules.length + 1}`).format.numberFormat = "#,##0";
rules.getRange(`A1:C${payload.rules.length + 1}`).format.autofitColumns();

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "school_math_analysis formula error scan",
});
console.log(errors.ndjson);

await fs.mkdir(outputDir, { recursive: true });
const preview = await workbook.render({
  sheetName: "school_math_analysis",
  range: `A1:${analysisLastCol}${Math.min(analysisLastRow, 14)}`,
  scale: 1,
  format: "png",
});
await fs.writeFile(
  new URL("school_math_analysis_preview.png", outputDir),
  new Uint8Array(await preview.arrayBuffer()),
);

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath.pathname);
console.log(JSON.stringify({ output: outputPath.pathname, rows: payload.analysis.length, summary: payload.summary }));
