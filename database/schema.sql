-- ============================================================
-- KrishiMitra AI - Database Schema (SQLite)
-- ============================================================
-- Design notes:
--   * All monetary values stored as INTEGER paise/rupee-cents where
--     precision matters, otherwise REAL for simplicity (capstone scope).
--   * Foreign keys enforce referential integrity; SQLite requires
--     "PRAGMA foreign_keys = ON" per-connection (set in db_manager.py).
--   * Timestamps stored as ISO-8601 TEXT for portability.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------
-- Users: farmer accounts
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name    TEXT NOT NULL,
    phone_hash      TEXT,                 -- hashed, never plaintext phone numbers
    preferred_language TEXT NOT NULL DEFAULT 'en' CHECK (preferred_language IN ('en','ta','hi')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------
-- Farm Profiles: one farmer can have multiple plots/profiles
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS farm_profiles (
    farm_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    farm_name       TEXT NOT NULL,
    region          TEXT NOT NULL,
    district        TEXT,
    state           TEXT,
    soil_type       TEXT NOT NULL CHECK (
                        soil_type IN ('alluvial','black','red','laterite','sandy','clay','loamy','saline')
                    ),
    land_area_acres REAL NOT NULL CHECK (land_area_acres > 0),
    irrigation_source TEXT,               -- e.g. 'borewell', 'canal', 'rainfed'
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_farm_profiles_user ON farm_profiles(user_id);

-- ---------------------------------------------------------------
-- Crop History: what was grown, when, and outcome
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_history (
    history_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id         INTEGER NOT NULL REFERENCES farm_profiles(farm_id) ON DELETE CASCADE,
    crop_name       TEXT NOT NULL,
    season          TEXT NOT NULL CHECK (season IN ('kharif','rabi','zaid','summer')),
    sown_date       TEXT,
    harvest_date    TEXT,
    yield_kg        REAL,
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_crop_history_farm ON crop_history(farm_id);

-- ---------------------------------------------------------------
-- Weather Logs: cached/observed weather pulled by the Weather Agent
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_logs (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    region          TEXT NOT NULL,
    observed_date   TEXT NOT NULL,
    temperature_c   REAL,
    rainfall_mm     REAL,
    humidity_pct    REAL,
    forecast_summary TEXT,
    source          TEXT NOT NULL DEFAULT 'simulated',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_weather_logs_region_date ON weather_logs(region, observed_date);

-- ---------------------------------------------------------------
-- Advisory Logs: every recommendation given, for audit + explainability
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS advisory_logs (
    advisory_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    farm_id         INTEGER REFERENCES farm_profiles(farm_id) ON DELETE SET NULL,
    agent_name      TEXT NOT NULL,
    query_text      TEXT NOT NULL,
    recommendation  TEXT NOT NULL,
    confidence_score REAL CHECK (confidence_score BETWEEN 0 AND 100),
    reasoning_json  TEXT,                  -- JSON blob: factors considered, alternatives
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_advisory_logs_user ON advisory_logs(user_id);

-- ---------------------------------------------------------------
-- Market Data: crop price snapshots
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_data (
    market_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name       TEXT NOT NULL,
    market_name     TEXT NOT NULL,
    region          TEXT NOT NULL,
    price_per_quintal REAL NOT NULL,
    price_date      TEXT NOT NULL,
    trend           TEXT CHECK (trend IN ('rising','falling','stable')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_market_data_crop_region ON market_data(crop_name, region);

-- ---------------------------------------------------------------
-- Government Schemes (reference/knowledge table)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS government_schemes (
    scheme_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_name     TEXT NOT NULL,
    description     TEXT NOT NULL,
    eligibility     TEXT NOT NULL,
    benefits        TEXT NOT NULL,
    applicable_states TEXT,                -- comma-separated, 'ALL' for nationwide
    official_link   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
