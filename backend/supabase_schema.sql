-- ─────────────────────────────────────────────
-- Solace Journal — Supabase SQL Schema
-- Run this in: Supabase Dashboard → SQL Editor
-- ─────────────────────────────────────────────

-- Journal Entries
CREATE TABLE IF NOT EXISTS entries (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(64)  NOT NULL DEFAULT 'default',
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    mood_score  INTEGER      NOT NULL CHECK (mood_score BETWEEN 1 AND 5),
    mood_label  VARCHAR(32)  NOT NULL,
    content     TEXT         NOT NULL,
    emotions    JSONB        NOT NULL DEFAULT '[]',
    ai_response TEXT
);

-- Index for fast user queries
CREATE INDEX IF NOT EXISTS idx_entries_user_id    ON entries (user_id);
CREATE INDEX IF NOT EXISTS idx_entries_created_at ON entries (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entries_mood       ON entries (mood_score);

-- Weekly AI Insights
CREATE TABLE IF NOT EXISTS weekly_insights (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(64) NOT NULL,
    week_start  VARCHAR(20) NOT NULL,
    insight     TEXT        NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_insights_user_id ON weekly_insights (user_id);

-- ─────────────────────────────────────────────
-- Optional: Row Level Security (RLS)
-- Enable if you want per-user data isolation
-- ─────────────────────────────────────────────

-- ALTER TABLE entries         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE weekly_insights ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can only access their own entries"
--   ON entries FOR ALL
--   USING (user_id = current_user);
