# Coding Standards

- Prefer explicit, readable code over clever abstractions.
- Use timezone-aware datetimes only.
- Store all runtime timestamps as TIMESTAMPTZ.
- Default timezone: Asia/Jerusalem.
- External API payloads are stored in JSONB for debugging.
- Every write-back to external tools must be auditable.
- All sync operations must be idempotent.
- Do not send duplicate alerts if the same scheduler command runs twice.
- No cross-tool automatic duplication in MVP.
