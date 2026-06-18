# Premortem

## Failure mode: alert fatigue

Cause:
- Backlog and low-value tasks alert too often.

Mitigation:
- Backlog appears in digest only.
- Fixed-time tasks alert immediately.
- Stale backlog uses age threshold.
- Repeat intervals depend on priority.

## Failure mode: duplicate tasks

Cause:
- Same task appears in Trello, Google Tasks, and Calendar.

Mitigation:
- Use `external_links`.
- Do not create cross-tool duplicates automatically.
- Optional future fuzzy dedup: title + date + source.

## Failure mode: completion semantics unclear

Cause:
- Calendar event in the past is incorrectly treated as done.

Mitigation:
- Past calendar event is not automatically done.
- Google Tasks completed status maps to done.
- Trello dueComplete or Done list maps to done.
- Local done overrides local display.

## Failure mode: hourly scheduler lacks precision

Cause:
- A 09:05 task alerts at 10:00.

Mitigation:
- Accept in MVP or run every 15 minutes.
- For precise alerts, later add background service.

## Failure mode: external API instability

Cause:
- Expired tokens, rate limits, schema changes.

Mitigation:
- Store sync errors.
- Alert user on connector failure.
- Keep local source of truth independent of external availability.

## Failure mode: write-back damages external data

Cause:
- Incorrectly marking Trello/Google Tasks done.

Mitigation:
- Conservative write-back only.
- Audit log every write-back.
- Dry-run mode.
