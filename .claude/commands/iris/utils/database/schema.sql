-- Iris Project Database Schema
-- Replaces JSON-based project tracking with SQLite relational database
-- Version: 1.0.0

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Project metadata and configuration
CREATE TABLE IF NOT EXISTS project_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Milestones (equivalent to milestones in task_graph.json)
CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, blocked
    order_index INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    validation_required BOOLEAN DEFAULT FALSE,
    validation_completed BOOLEAN DEFAULT FALSE
);

-- Tasks (equivalent to tasks in task_graph.json)
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    milestone_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, failed, blocked
    order_index INTEGER NOT NULL,
    max_file_changes INTEGER DEFAULT 10,
    scope_boundaries TEXT, -- JSON blob for complex scope rules
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    duration_minutes INTEGER,
    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE
);

-- Task dependencies (replaces manual dependency tracking)
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id TEXT NOT NULL,
    depends_on_task_id TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'blocks', -- blocks, suggests, enhances
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, depends_on_task_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Approved technology stack (replaces techstack_research.json)
CREATE TABLE IF NOT EXISTS technologies (
    name TEXT PRIMARY KEY,
    category TEXT,  -- language, framework, database, testing, etc.
    version TEXT,
    is_latest_stable BOOLEAN DEFAULT FALSE,
    official_url TEXT,
    last_verified DATETIME,
    needs_verification BOOLEAN DEFAULT FALSE,
    decision_reason TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Technology research sources
CREATE TABLE IF NOT EXISTS technology_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology_name TEXT NOT NULL,
    source_url TEXT,
    published_date DATE,
    relevance TEXT,
    notes TEXT,
    FOREIGN KEY (technology_name) REFERENCES technologies(name) ON DELETE CASCADE
);

-- Scope and quality rules (replaces guardrail_config.json)
CREATE TABLE IF NOT EXISTS guardrails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type TEXT NOT NULL, -- scope_creep, quality_gate, forbidden_keyword
    rule_name TEXT NOT NULL,
    rule_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Feature deferrals (replaces deferred.json)
CREATE TABLE IF NOT EXISTS deferred_features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    reason TEXT,
    complexity_score INTEGER,
    original_requirement TEXT,
    deferred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 5 -- 1=high, 5=low
);

-- PRD digest and original requirements (replaces prd_digest.json)
CREATE TABLE IF NOT EXISTS prd_features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    original_text TEXT,
    prd_lines TEXT, -- JSON array of line references
    why_mvp TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Project metrics and protection tracking
CREATE TABLE IF NOT EXISTS project_metrics (
    metric_name TEXT PRIMARY KEY,
    metric_value TEXT NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Current project state (replaces progress_tracker.json)
CREATE TABLE IF NOT EXISTS project_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Task execution attempts and retries
CREATE TABLE IF NOT EXISTS task_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    execution_status TEXT NOT NULL, -- started, completed, failed, retrying
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    autopilot_mode BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Milestone validation history
CREATE TABLE IF NOT EXISTS milestone_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id TEXT NOT NULL,
    validation_status TEXT NOT NULL, -- pending, passed, failed
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    validation_notes TEXT,
    autopilot_triggered BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_tasks_milestone ON tasks(milestone_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_deps_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_deps_depends ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_executions_task ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_validations_milestone ON milestone_validations(milestone_id);
CREATE INDEX IF NOT EXISTS idx_project_state_key ON project_state(key);

-- Schema version tracking
INSERT OR REPLACE INTO project_metadata (key, value) 
VALUES ('schema_version', '1.0.0');

INSERT OR REPLACE INTO project_metadata (key, value) 
VALUES ('database_created', datetime('now'));

-- Default project state values
INSERT OR REPLACE INTO project_state (key, value) 
VALUES ('current_milestone_id', '');

INSERT OR REPLACE INTO project_state (key, value) 
VALUES ('total_tasks', '0');

INSERT OR REPLACE INTO project_state (key, value) 
VALUES ('completed_tasks', '0');

INSERT OR REPLACE INTO project_state (key, value) 
VALUES ('project_status', 'initialized');