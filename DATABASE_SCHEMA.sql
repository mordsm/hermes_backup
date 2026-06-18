CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tasks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    title               TEXT NOT NULL,
    description         TEXT,

    status              TEXT NOT NULL DEFAULT 'active',
    -- active / archived / cancelled

    priority            TEXT NOT NULL DEFAULT 'normal',
    -- low / normal / high / urgent

    category            TEXT,

    task_type           TEXT NOT NULL DEFAULT 'single',
    -- single / recurring / backlog / appointment

    due_at              TIMESTAMPTZ,
    deadline_at         TIMESTAMPTZ,

    recurrence_rule     TEXT,
    timezone            TEXT NOT NULL DEFAULT 'Asia/Jerusalem',

    source              TEXT NOT NULL DEFAULT 'local',
    source_object_id    TEXT,
    source_url          TEXT,

    metadata            JSONB NOT NULL DEFAULT '{}',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at         TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS task_instances (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    task_id             UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,

    occurrence_date     DATE,
    scheduled_at        TIMESTAMPTZ,
    deadline_at         TIMESTAMPTZ,

    status              TEXT NOT NULL DEFAULT 'pending',
    -- pending / done / skipped / missed / cancelled

    completed_at        TIMESTAMPTZ,
    skipped_at          TIMESTAMPTZ,
    snoozed_until       TIMESTAMPTZ,

    alert_count         INT NOT NULL DEFAULT 0,
    last_alerted_at     TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(task_id, occurrence_date)
);

CREATE TABLE IF NOT EXISTS external_links (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    task_id             UUID REFERENCES tasks(id) ON DELETE CASCADE,

    source              TEXT NOT NULL,
    source_object_id    TEXT NOT NULL,
    source_etag         TEXT,
    source_updated_at   TIMESTAMPTZ,
    source_payload      JSONB NOT NULL DEFAULT '{}',

    last_synced_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(source, source_object_id)
);

CREATE TABLE IF NOT EXISTS sync_state (
    source              TEXT PRIMARY KEY,
    sync_token          TEXT,
    last_full_sync_at   TIMESTAMPTZ,
    last_incremental_sync_at TIMESTAMPTZ,
    status              TEXT NOT NULL DEFAULT 'ok',
    error_message       TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    task_instance_id    UUID REFERENCES task_instances(id) ON DELETE CASCADE,

    channel             TEXT NOT NULL,
    alert_type          TEXT NOT NULL,

    sent_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at     TIMESTAMPTZ,
    payload             JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type         TEXT NOT NULL,
    entity_id           UUID,
    action              TEXT NOT NULL,
    source              TEXT,
    details             JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS settings (
    key                 TEXT PRIMARY KEY,
    value               JSONB NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_task_instances_due
ON task_instances(status, scheduled_at, deadline_at);

CREATE INDEX IF NOT EXISTS idx_task_instances_snooze
ON task_instances(status, snoozed_until);

CREATE INDEX IF NOT EXISTS idx_tasks_source
ON tasks(source, source_object_id);

CREATE INDEX IF NOT EXISTS idx_tasks_metadata
ON tasks USING GIN(metadata);

CREATE INDEX IF NOT EXISTS idx_external_links_source
ON external_links(source, source_object_id);

CREATE OR REPLACE VIEW v_today AS
SELECT
    ti.id AS instance_id,
    t.title,
    t.priority,
    ti.scheduled_at,
    ti.deadline_at,
    ti.status,
    t.source,
    t.source_url
FROM task_instances ti
JOIN tasks t ON t.id = ti.task_id
WHERE ti.status = 'pending'
  AND (
      ti.scheduled_at::date = CURRENT_DATE
      OR ti.deadline_at::date = CURRENT_DATE
  );

CREATE OR REPLACE VIEW v_overdue AS
SELECT
    ti.id AS instance_id,
    t.title,
    t.priority,
    ti.scheduled_at,
    ti.deadline_at,
    ti.last_alerted_at,
    ti.alert_count
FROM task_instances ti
JOIN tasks t ON t.id = ti.task_id
WHERE ti.status = 'pending'
  AND (
      ti.scheduled_at < now()
      OR ti.deadline_at < now()
  );

CREATE OR REPLACE VIEW v_stale_backlog AS
SELECT *
FROM tasks
WHERE task_type = 'backlog'
  AND status = 'active'
  AND due_at IS NULL
  AND created_at < now() - interval '14 days';
