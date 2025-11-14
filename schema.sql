-- Training Plan Database Schema
-- Core Strava activity tracking

-- ============================================================================
-- RUNNING ACTIVITIES (from Strava)
-- ============================================================================

CREATE TABLE IF NOT EXISTS activities (
    -- Primary identifiers
    id INTEGER PRIMARY KEY,
    strava_id INTEGER UNIQUE NOT NULL,

    -- Basic activity info
    name TEXT NOT NULL,
    date TEXT NOT NULL,  -- ISO format (YYYY-MM-DD HH:MM:SS)
    sport_type TEXT NOT NULL,  -- Run, TrailRun, VirtualRun, etc.
    workout_type INTEGER,  -- Strava workout type: 0=default, 1=race, 2=long, 3=workout

    -- Core metrics
    distance REAL NOT NULL,  -- meters
    moving_time INTEGER NOT NULL,  -- seconds
    elapsed_time INTEGER NOT NULL,  -- seconds (includes stops)

    -- Elevation (critical for mountaineering prep)
    total_elevation_gain REAL,  -- meters
    elev_high REAL,  -- meters
    elev_low REAL,  -- meters

    -- Speed/pace metrics
    average_speed REAL,  -- m/s
    max_speed REAL,  -- m/s

    -- Heart rate (intensity tracking for zone training)
    has_heartrate BOOLEAN DEFAULT 0,
    average_heartrate REAL,  -- bpm
    max_heartrate REAL,  -- bpm

    -- Training load indicators
    suffer_score REAL,  -- Strava's relative intensity metric
    calories REAL,
    perceived_exertion INTEGER,  -- RPE (1-10) if you want to manually add

    -- Context
    device_name TEXT,
    trainer BOOLEAN DEFAULT 0,  -- treadmill
    commute BOOLEAN DEFAULT 0,

    -- Notes
    description TEXT,
    notes TEXT,  -- Your own notes about how you felt, any issues, etc.

    -- Timestamps
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by date range
CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date);
CREATE INDEX IF NOT EXISTS idx_activities_sport_type ON activities(sport_type);


-- ============================================================================
-- ACTIVITY SPLITS (for pace analysis and progression tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_splits (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER NOT NULL,

    -- Split info
    split_number INTEGER NOT NULL,  -- 1, 2, 3, etc.
    split_type TEXT NOT NULL,  -- 'metric' (per km) or 'standard' (per mile)

    -- Metrics
    distance REAL NOT NULL,  -- meters
    elapsed_time INTEGER NOT NULL,  -- seconds
    moving_time INTEGER NOT NULL,  -- seconds
    elevation_difference REAL,  -- meters (+ for gain, - for loss)

    -- Pace
    average_speed REAL,  -- m/s
    average_grade_adjusted_speed REAL,  -- m/s (accounts for elevation)

    -- Heart rate
    average_heartrate REAL,  -- bpm

    -- Zone classification
    pace_zone INTEGER,  -- Strava's pace zone (0-5, typically)

    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_splits_activity ON activity_splits(activity_id);


-- ============================================================================
-- WEIGHTLIFTING / STRENGTH TRAINING
-- ============================================================================

CREATE TABLE IF NOT EXISTS lifting_sessions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,  -- ISO format (YYYY-MM-DD)
    name TEXT NOT NULL,  -- e.g., "Upper B", "Lower A"
    notes TEXT,  -- Session-level notes

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lifting_date ON lifting_sessions(date);


CREATE TABLE IF NOT EXISTS lifting_exercises (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,

    -- Exercise details
    exercise_name TEXT NOT NULL,  -- e.g., "Deadlift", "Squats", "Pull-ups"
    weight REAL,  -- Weight in pounds
    reps_per_set TEXT NOT NULL,  -- JSON array: [10, 10, 9, 9]
    rest_seconds INTEGER,  -- Rest between sets

    -- Notes
    notes TEXT,  -- e.g., "Dropped weight on last set", "Left knee twinge"

    FOREIGN KEY (session_id) REFERENCES lifting_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_exercises_session ON lifting_exercises(session_id);
CREATE INDEX IF NOT EXISTS idx_exercises_name ON lifting_exercises(exercise_name);


-- ============================================================================
-- TRAINING PLANS (Claude-generated workout plans)
-- ============================================================================

-- WEEKLY PLANS (Week-level guidance and context)

CREATE TABLE IF NOT EXISTS weekly_plans (
    id INTEGER PRIMARY KEY,
    week_start_date TEXT NOT NULL,  -- Monday of the week (YYYY-MM-DD)
    week_number INTEGER,  -- e.g., 3 (week 3 of plan)
    total_weeks INTEGER,  -- e.g., 12 (12-week plan)

    -- Week guidance
    objective TEXT,  -- Overarching goal for the week
    description TEXT,  -- Sleep, nutrition, recovery tips, what to watch for

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weekly_plans_date ON weekly_plans(week_start_date);


-- PLANNED RUNS

CREATE TABLE IF NOT EXISTS planned_runs (
    id INTEGER PRIMARY KEY,
    weekly_plan_id INTEGER NOT NULL,

    date TEXT NOT NULL,  -- YYYY-MM-DD
    distance REAL,  -- km (nullable if workout is time-based or unstructured)
    type TEXT NOT NULL,  -- 'recovery', 'base', 'tempo', 'intervals', 'hills', 'long', etc.

    description TEXT,  -- Freeform: terrain, vertical, workout structure, pacing guidance
    priority TEXT DEFAULT 'medium',  -- 'high', 'medium', 'low'

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (weekly_plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_planned_runs_date ON planned_runs(date);
CREATE INDEX IF NOT EXISTS idx_planned_runs_weekly_plan ON planned_runs(weekly_plan_id);


-- PLANNED LIFTING SESSIONS

CREATE TABLE IF NOT EXISTS planned_lifting_sessions (
    id INTEGER PRIMARY KEY,
    weekly_plan_id INTEGER NOT NULL,

    date TEXT NOT NULL,  -- YYYY-MM-DD
    name TEXT NOT NULL,  -- e.g., "Upper A", "Lower B"
    description TEXT,  -- Freeform guidance for the session

    priority TEXT DEFAULT 'medium',  -- 'high', 'medium', 'low'

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (weekly_plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_planned_lifting_date ON planned_lifting_sessions(date);
CREATE INDEX IF NOT EXISTS idx_planned_lifting_weekly_plan ON planned_lifting_sessions(weekly_plan_id);


-- PLANNED LIFTING EXERCISES (within a planned session)

CREATE TABLE IF NOT EXISTS planned_lifting_exercises (
    id INTEGER PRIMARY KEY,
    planned_session_id INTEGER NOT NULL,

    exercise_name TEXT NOT NULL,  -- e.g., "Deadlift", "Squats", "Pull-ups"
    target_weight REAL,  -- Target weight in lbs (nullable for bodyweight or "feel it out")
    reps_per_set TEXT NOT NULL,  -- JSON array: [10, 10, 9, 9]
    rest_seconds INTEGER,  -- Rest between sets

    notes TEXT,  -- Why this exercise, what to focus on, when to skip, etc.

    FOREIGN KEY (planned_session_id) REFERENCES planned_lifting_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_planned_exercises_session ON planned_lifting_exercises(planned_session_id);
CREATE INDEX IF NOT EXISTS idx_planned_exercises_name ON planned_lifting_exercises(exercise_name);
