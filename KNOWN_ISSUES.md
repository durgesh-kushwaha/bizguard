# KNOWN ISSUES — BizGuard

**Last Updated:** 2026-10-03

## Critical
None.

## Major
None.

## Minor
- Streamlit Community Cloud does not guarantee local-file persistence across app restarts or redeployments. Decision History works with the configured SQLite database, but durable cloud history needs a separately configured remote database.

## Notes
- The sample data is synthetic and intentionally small; Spark demonstrates the processing flow, not production-scale throughput.
- The PySpark test skips when a working local Spark and Java runtime is unavailable.
- Presentation screenshots have not been added to the repository.
