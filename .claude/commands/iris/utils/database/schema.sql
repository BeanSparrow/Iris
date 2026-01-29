-- Iris Project Database Schema
-- Replaces JSON-based project tracking with SQLite relational database
-- Version: 2.1.0
--
-- Changes in 2.1.0:
--   - Added refine_iterations table for Ralph-style refinement loop tracking
--   - Added refine_findings table for review agent findings
--   - Added refine_improvements table for refiner agent improvements
--   - Added indexes for refine tables
--
-- Changes in 2.0.0:
--   - Added research_opportunities table for dynamic research tracking
--   - Added research_executions table for subagent execution history
--   - Extended technologies table with opportunity linking and confidence
--   - Extended technology_sources table with fetch tracking
--   - Updated project_metadata to support research category system

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

-- Research opportunities catalog and tracking
-- Tracks which research opportunities were selected and their outcomes
CREATE TABLE IF NOT EXISTS research_opportunities (
    id TEXT PRIMARY KEY,                    -- STACK_LANG, VERSION_DEPS, OPS_TESTING, etc.
    category TEXT NOT NULL,                 -- stack, version, architecture, ops, custom
    name TEXT NOT NULL,                     -- Human-readable name
    research_question TEXT,                 -- The question being researched
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, skipped
    result_summary TEXT,                    -- Brief summary of findings
    confidence TEXT,                        -- HIGH, MEDIUM, LOW
    researched_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Research execution history
-- Tracks subagent executions for debugging and audit
CREATE TABLE IF NOT EXISTS research_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL,
    execution_status TEXT NOT NULL,         -- started, completed, failed, retrying
    subagent_prompt TEXT,                   -- The prompt sent to subagent
    subagent_response TEXT,                 -- Full response (kept concise via prompt requirements)
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (opportunity_id) REFERENCES research_opportunities(id) ON DELETE CASCADE
);

-- Approved technology stack (replaces techstack_research.json)
CREATE TABLE IF NOT EXISTS technologies (
    name TEXT PRIMARY KEY,
    category TEXT,                          -- language, framework, database, testing, etc.
    version TEXT,
    is_latest_stable BOOLEAN DEFAULT FALSE,
    official_url TEXT,
    last_verified DATETIME,
    needs_verification BOOLEAN DEFAULT FALSE,
    decision_reason TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- New columns for research integration
    opportunity_id TEXT,                    -- Links to research_opportunities.id
    confidence TEXT,                        -- HIGH, MEDIUM, LOW
    alternatives TEXT,                      -- JSON array: ["Vue", "Svelte"]
    compatibility_notes TEXT,               -- Notes on compatibility with other stack items
    source_type TEXT,                       -- explicit_prd, researched, default
    FOREIGN KEY (opportunity_id) REFERENCES research_opportunities(id) ON DELETE SET NULL
);

-- Technology research sources
CREATE TABLE IF NOT EXISTS technology_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology_name TEXT NOT NULL,
    source_url TEXT,
    published_date DATE,
    relevance TEXT,
    notes TEXT,
    -- New columns for fetch tracking
    source_type TEXT,                       -- official_docs, blog, comparison, release_notes
    was_fetched BOOLEAN DEFAULT FALSE,      -- Did we actually fetch and verify this URL?
    fetch_timestamp DATETIME,               -- When was it fetched?
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

-- Research-related indexes
CREATE INDEX IF NOT EXISTS idx_research_opp_status ON research_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_research_opp_category ON research_opportunities(category);
CREATE INDEX IF NOT EXISTS idx_tech_opportunity ON technologies(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_research_exec_opp ON research_executions(opportunity_id);

-- ============================================================================
-- RALPH REFINER TABLES (added in 2.1.0)
-- Implements Ralph Wiggum-style iterative refinement loop
-- ============================================================================

-- Refine iterations - tracks each pass through the refinement loop
CREATE TABLE IF NOT EXISTS refine_iterations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_number INTEGER NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    findings_count INTEGER DEFAULT 0,
    improvements_count INTEGER DEFAULT 0,
    validation_passed BOOLEAN,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed
    summary TEXT                              -- Brief summary of iteration outcome
);

-- Refine findings - stores findings from parallel review agents
CREATE TABLE IF NOT EXISTS refine_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id INTEGER NOT NULL,
    reviewer_focus TEXT NOT NULL,             -- gaps, quality, integration, edge_cases, security, performance
    severity TEXT NOT NULL,                   -- HIGH, MEDIUM, LOW
    category TEXT NOT NULL,                   -- gap, quality, integration, edge_case, security, performance
    file_path TEXT,
    line_number INTEGER,
    description TEXT NOT NULL,
    suggestion TEXT,
    prd_reference TEXT,                       -- Which PRD requirement this relates to
    addressed BOOLEAN DEFAULT FALSE,
    addressed_in_iteration INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iteration_id) REFERENCES refine_iterations(id) ON DELETE CASCADE
);

-- Refine improvements - tracks improvements made by refiner agent
CREATE TABLE IF NOT EXISTS refine_improvements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id INTEGER NOT NULL,
    finding_id INTEGER,                       -- Links to finding that prompted this (nullable for proactive improvements)
    description TEXT NOT NULL,
    files_modified TEXT,                      -- JSON array of file paths
    commit_hash TEXT,
    tests_passing BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iteration_id) REFERENCES refine_iterations(id) ON DELETE CASCADE,
    FOREIGN KEY (finding_id) REFERENCES refine_findings(id) ON DELETE SET NULL
);

-- Refine-related indexes
CREATE INDEX IF NOT EXISTS idx_refine_iterations_status ON refine_iterations(status);
CREATE INDEX IF NOT EXISTS idx_refine_findings_iteration ON refine_findings(iteration_id);
CREATE INDEX IF NOT EXISTS idx_refine_findings_severity ON refine_findings(severity);
CREATE INDEX IF NOT EXISTS idx_refine_findings_addressed ON refine_findings(addressed);
CREATE INDEX IF NOT EXISTS idx_refine_improvements_iteration ON refine_improvements(iteration_id);
CREATE INDEX IF NOT EXISTS idx_refine_improvements_finding ON refine_improvements(finding_id);

-- Schema version tracking
INSERT OR REPLACE INTO project_metadata (key, value)
VALUES ('schema_version', '2.1.0');

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

-- Default refine state values (added in 2.1.0)
INSERT OR REPLACE INTO project_state (key, value)
VALUES ('refine_enabled', 'true');

INSERT OR REPLACE INTO project_state (key, value)
VALUES ('refine_phase_status', 'pending');

INSERT OR REPLACE INTO project_state (key, value)
VALUES ('refine_current_iteration', '0');

INSERT OR REPLACE INTO project_state (key, value)
VALUES ('refine_max_iterations', '5');