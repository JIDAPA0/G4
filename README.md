# Math Teacher Workforce Dashboard

Prototype web dashboard for analyzing math teacher workforce status across the target education service areas.

## What It Shows

- Current math teacher status by school: shortage, met, surplus
- 1-5 year future shortage prediction
- Sudden shortage risk level
- Area-level summaries
- Machine learning model comparison metrics

The web app reads its deployed dashboard data from `public/dashboard-data.json`, which is generated from the transformed Excel analysis files in the local project workflow.

## Development

```bash
pnpm install
pnpm run build
```
