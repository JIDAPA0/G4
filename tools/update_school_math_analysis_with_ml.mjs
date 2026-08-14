import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = new URL("../", import.meta.url);
const payloadPath = new URL("outputs/tmp/ml_predictions_payload.json", root);
const outputPath = new URL("data/school_math_analysis.xlsx", root);
const previewPath = new URL("outputs/validation/school_math_analysis_ml_preview.png", root);

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));

const analysisHeaders = [
  "school_code",
  "calculated_min_math",
  "actual_math_teachers",
  "current_math_status",
  "future_shortage_prediction",
  "sudden_shortage_risk_level",
];

const rules = [
  [1, 19, 1],
  [20, 28, 2],
  [29, 38, 2],
  [39, 48, 3],
  [49, 58, 4],
  [59, 67, 5],
  [68, 77, 6],
  [78, 87, 7],
  [88, 97, 7],
  [98, 106, 8],
  [107, 116, 9],
  [117, 126, 10],
  [127, 136, 11],
  [137, 145, 11],
  [146, 155, 12],
  [156, 165, 13],
  [166, 175, 14],
  [176, 184, 15],
  [185, 194, 15],
  [195, 204, 16],
  [205, 214, 17],
  [215, 223, 18],
  [224, 233, 19],
  [234, "ขึ้นไป", 20],
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
  };
}

function styleTable(range) {
  range.format.borders = {
    preset: "all",
    style: "thin",
    color: "#D9E2F3",
  };
}

function addMetricSheet(workbook, sheetName, rows, headers) {
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;
  const values = [headers, ...rows.map((row) => headers.map((header) => row[header] ?? ""))];
  const lastCol = columnLetter(headers.length - 1);
  const lastRow = values.length;
  sheet.getRange(`A1:${lastCol}${lastRow}`).values = values;
  styleHeader(sheet.getRange(`A1:${lastCol}1`));
  styleTable(sheet.getRange(`A1:${lastCol}${lastRow}`));
  sheet.getRange(`A1:${lastCol}${lastRow}`).format.autofitColumns();
  sheet.getRange(`A1:${lastCol}${lastRow}`).format.autofitRows();
  sheet.freezePanes.freezeRows(1);
  return sheet;
}

const workbook = Workbook.create();
const analysis = workbook.worksheets.add("school_math_analysis");
analysis.showGridLines = false;

const analysisRows = payload.analysis;
const analysisValues = [
  analysisHeaders,
  ...analysisRows.map((row) => analysisHeaders.map((header) => row[header] ?? "")),
];
const lastRow = analysisValues.length;
const lastCol = columnLetter(analysisHeaders.length - 1);
analysis.getRange(`A1:${lastCol}${lastRow}`).values = analysisValues;
styleHeader(analysis.getRange(`A1:${lastCol}1`));
styleTable(analysis.getRange(`A1:${lastCol}${lastRow}`));
analysis.getRange(`A2:A${lastRow}`).format.numberFormat = "@";
analysis.getRange(`B2:C${lastRow}`).format.numberFormat = "#,##0";
analysis.getRange(`E2:E${lastRow}`).format.numberFormat = "#,##0";
analysis.getRange(`A1:${lastCol}${lastRow}`).format.autofitColumns();
analysis.getRange(`A1:${lastCol}${lastRow}`).format.autofitRows();
analysis.getRange("A:A").format.columnWidthPx = 122;
analysis.getRange("E:F").format.columnWidthPx = 210;
analysis.freezePanes.freezeRows(1);

analysis.getRange(`D2:D${lastRow}`).conditionalFormats.add("containsText", {
  text: "ขาด",
  format: { fill: "#FCE4D6", font: { color: "#C00000", bold: true } },
});
analysis.getRange(`D2:D${lastRow}`).conditionalFormats.add("containsText", {
  text: "ตามเกณฑ์",
  format: { fill: "#E2F0D9", font: { color: "#375623", bold: true } },
});
analysis.getRange(`D2:D${lastRow}`).conditionalFormats.add("containsText", {
  text: "เกิน",
  format: { fill: "#DDEBF7", font: { color: "#1F4E79", bold: true } },
});
analysis.getRange(`F2:F${lastRow}`).conditionalFormats.add("containsText", {
  text: "สูง",
  format: { fill: "#F4CCCC", font: { color: "#990000", bold: true } },
});
analysis.getRange(`F2:F${lastRow}`).conditionalFormats.add("containsText", {
  text: "ปานกลาง",
  format: { fill: "#FFF2CC", font: { color: "#7F6000", bold: true } },
});
analysis.getRange(`F2:F${lastRow}`).conditionalFormats.add("containsText", {
  text: "ต่ำ",
  format: { fill: "#D9EAD3", font: { color: "#274E13", bold: true } },
});

const currentCounts = {};
const riskCounts = {};
for (const row of analysisRows) {
  currentCounts[row.current_math_status] = (currentCounts[row.current_math_status] || 0) + 1;
  riskCounts[row.sudden_shortage_risk_level] = (riskCounts[row.sudden_shortage_risk_level] || 0) + 1;
}

const summary = workbook.worksheets.add("summary");
summary.showGridLines = false;
summary.getRange("A1:B9").values = [
  ["metric", "count"],
  ["โรงเรียนทั้งหมด", analysisRows.length],
  ["สถานะปัจจุบัน: ขาด", currentCounts["ขาด"] || 0],
  ["สถานะปัจจุบัน: ตามเกณฑ์", currentCounts["ตามเกณฑ์"] || 0],
  ["สถานะปัจจุบัน: เกิน", currentCounts["เกิน"] || 0],
  ["ความเสี่ยงฉับพลัน: สูง", riskCounts["สูง"] || 0],
  ["ความเสี่ยงฉับพลัน: ปานกลาง", riskCounts["ปานกลาง"] || 0],
  ["ความเสี่ยงฉับพลัน: ต่ำ", riskCounts["ต่ำ"] || 0],
  ["โมเดล Future ที่ดีที่สุด", payload.future_best.model],
];
styleHeader(summary.getRange("A1:B1"));
styleTable(summary.getRange("A1:B9"));
summary.getRange("B2:B8").format.numberFormat = "#,##0";
summary.getRange("A1:B9").format.autofitColumns();

addMetricSheet(workbook, "ml_future_metrics", payload.future_metrics, [
  "model",
  "mae",
  "rmse",
  "accuracy",
  "status",
]);
addMetricSheet(workbook, "ml_risk_metrics", payload.risk_metrics, [
  "model",
  "accuracy",
  "macro_f1",
  "status",
]);

const rulesSheet = workbook.worksheets.add("rules");
rulesSheet.showGridLines = false;
rulesSheet.getRange(`A1:C${rules.length + 1}`).values = [
  ["actual_teachers_min", "actual_teachers_max", "calculated_min_math"],
  ...rules,
];
styleHeader(rulesSheet.getRange("A1:C1"));
styleTable(rulesSheet.getRange(`A1:C${rules.length + 1}`));
rulesSheet.getRange(`A2:C${rules.length + 1}`).format.numberFormat = "#,##0";
rulesSheet.getRange(`A1:C${rules.length + 1}`).format.autofitColumns();

const notes = workbook.worksheets.add("model_notes");
notes.showGridLines = false;
const noteRows = [
  ["item", "value"],
  ["future_best_model", payload.future_best.model],
  ["risk_best_model", payload.risk_best.model],
  ["future_model_path", payload.model_paths.future_shortage_prediction],
  ["risk_model_path", payload.model_paths.sudden_shortage_risk_level],
  ["risk_target_distribution", JSON.stringify(payload.risk_target_distribution)],
  ["future_target_distribution", JSON.stringify(payload.future_target_distribution)],
  ["note_1", payload.notes[0]],
  ["note_2", payload.notes[1]],
  ["note_3", payload.notes[2]],
];
notes.getRange(`A1:B${noteRows.length}`).values = noteRows;
styleHeader(notes.getRange("A1:B1"));
styleTable(notes.getRange(`A1:B${noteRows.length}`));
notes.getRange(`A1:B${noteRows.length}`).format.autofitColumns();
notes.getRange("B:B").format.columnWidthPx = 620;
notes.getRange("B:B").format.wrapText = true;
notes.getRange(`A1:B${noteRows.length}`).format.autofitRows();

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "school_math_analysis ML final error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "school_math_analysis",
  range: `A1:${lastCol}${Math.min(lastRow, 14)}`,
  scale: 1,
  format: "png",
});
await fs.mkdir(new URL("outputs/validation/", root), { recursive: true });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath.pathname);
console.log(JSON.stringify({ output: outputPath.pathname, rows: analysisRows.length }));
