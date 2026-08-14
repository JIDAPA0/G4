import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = new URL("../", import.meta.url);
const dataDir = new URL("data/", root);
const outputDir = new URL("outputs/validation/", root);
const payloadPath = new URL("transformed_payload.json", dataDir);

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));

const schoolHeaders = [
  "school_code",
  "school_name",
  "area_code",
  "area_name",
  "total_students",
  "actual_teachers",
  "school_size",
  "hired_teachers",
];

const teacherHeaders = [
  "teacher_id",
  "school_code",
  "teacher_major",
  "subject_group_id",
  "subject_group",
  "subject_major",
  "birth_date",
  "retirement_date",
  "start_date",
  "condition_of_tenure",
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

async function buildWorkbook(rows, headers, sheetName, fileName) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;

  const values = [
    headers,
    ...rows.map((row) => headers.map((header) => row[header] ?? "")),
  ];
  const lastColumn = columnLetter(headers.length - 1);
  const lastRow = values.length;
  const usedRange = `A1:${lastColumn}${lastRow}`;

  sheet.getRange(usedRange).values = values;
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: "#1F4E79",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: false,
  };
  sheet.getRange(usedRange).format.borders = {
    preset: "all",
    style: "thin",
    color: "#D9E2F3",
  };
  sheet.freezePanes.freezeRows(1);
  sheet.getRange(usedRange).format.autofitColumns();
  sheet.getRange(usedRange).format.autofitRows();

  if (fileName === "schools.xlsx") {
    sheet.getRange(`A2:C${lastRow}`).format.numberFormat = "@";
    sheet.getRange(`E2:F${lastRow}`).format.numberFormat = "#,##0";
    sheet.getRange(`H2:H${lastRow}`).format.numberFormat = "#,##0";
    sheet.getRange("A:A").format.columnWidthPx = 112;
    sheet.getRange("C:C").format.columnWidthPx = 112;
  } else {
    sheet.getRange(`A2:B${lastRow}`).format.numberFormat = "@";
    sheet.getRange("A:A").format.columnWidthPx = 120;
    sheet.getRange("B:B").format.columnWidthPx = 120;
  }

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 50 },
    summary: `${fileName} formula error scan`,
  });
  console.log(errors.ndjson);

  const preview = await workbook.render({
    sheetName,
    range: `A1:${lastColumn}${Math.min(lastRow, 12)}`,
    scale: 1,
    format: "png",
  });
  await fs.mkdir(outputDir, { recursive: true });
  await fs.writeFile(
    new URL(`${fileName.replace(".xlsx", "")}_preview.png`, outputDir),
    new Uint8Array(await preview.arrayBuffer()),
  );

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(new URL(fileName, dataDir).pathname);
  console.log(JSON.stringify({ fileName, rows: rows.length, columns: headers.length }));
}

await buildWorkbook(payload.schools, schoolHeaders, "schools", "schools.xlsx");
await buildWorkbook(payload.teachers, teacherHeaders, "teachers", "teachers.xlsx");
