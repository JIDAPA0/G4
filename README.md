# Teacher Major Workforce Dashboard

Prototype web dashboard for analyzing teacher major coverage across the target education service areas.

## What It Shows

- Coverage across 108 schools, 4 education service areas, 8 official subject groups, and 20 teacher-major subjects
- Teacher counts, covered subjects, and shortage signals by subject group, area, and school
- School-level drilldowns with privacy-preserving teacher reference IDs
- 3D comparison chart, pie charts, supporting tables, and CSV/Excel/PNG export
- Risk indicators used only as a prioritization aid, not as final staffing decisions

The web app reads its deployed dashboard data from `public/dashboard-data.json`, which is generated from the transformed Excel analysis files in the local project workflow.

## Development

```bash
pnpm install
pnpm run build
```
