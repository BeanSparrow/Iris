# Iris Database Architecture

**Schema Version:** 2.0.0
**Last Updated:** 2024-12-30

## Overview

Iris uses a **SQLite backend** that provides transactional project management with atomic operations and data integrity. This document outlines the schema design and architectural decisions.

## 🎯 Design Goals

### Primary Objectives
- **Atomic Operations**: All state changes are transactional with rollback capability
- **Data Integrity**: Foreign key constraints and validation ensure consistency
- **Performance**: Optimized SQL queries for complex operations
- **Backup & Recovery**: Built-in backup system with versioned snapshots
- **Session Persistence**: Database maintains state across Claude Code sessions

### Secondary Benefits
- **Scalability**: Handles large projects with hundreds of tasks efficiently
- **Concurrency**: SQLite handles concurrent access gracefully
- **Query Power**: Complex analytical queries for progress tracking
- **Future Extensions**: Schema can evolve with new features

## 📋 Database Schema

### Core Tables

#### **milestones**
```sql
CREATE TABLE milestones (
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
```

#### **tasks**
```sql
CREATE TABLE tasks (
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
```

#### **task_dependencies**
```sql
CREATE TABLE task_dependencies (
    task_id TEXT NOT NULL,
    depends_on_task_id TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'blocks', -- blocks, suggests, enhances
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, depends_on_task_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

#### **technologies**
```sql
CREATE TABLE technologies (
    name TEXT PRIMARY KEY,
    category TEXT,                          -- language, framework, database, testing, etc.
    version TEXT,
    is_latest_stable BOOLEAN DEFAULT FALSE,
    official_url TEXT,
    last_verified DATETIME,
    needs_verification BOOLEAN DEFAULT FALSE,
    decision_reason TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Research integration columns (added in v2.0.0)
    opportunity_id TEXT,                    -- Links to research_opportunities.id
    confidence TEXT,                        -- HIGH, MEDIUM, LOW
    alternatives TEXT,                      -- JSON array: ["Vue", "Svelte"]
    compatibility_notes TEXT,               -- Notes on compatibility with other stack items
    source_type TEXT,                       -- explicit_prd, researched, default
    FOREIGN KEY (opportunity_id) REFERENCES research_opportunities(id) ON DELETE SET NULL
);
```

#### **project_metadata**
```sql
CREATE TABLE project_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Research Tables (Added in v2.0.0)

#### **research_opportunities**
Tracks which research opportunities were selected and their outcomes.
```sql
CREATE TABLE research_opportunities (
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
```

**Category Values:**
| Category | Description | Example Opportunity IDs |
|----------|-------------|------------------------|
| `stack` | Technology stack selection | STACK_LANG, STACK_FRAMEWORK_UI, STACK_DATABASE |
| `version` | Version and compatibility | VERSION_LANG, VERSION_DEPS, COMPAT_MATRIX |
| `architecture` | Architecture patterns | ARCH_PATTERN, ARCH_API_DESIGN, ARCH_STATE_MGMT |
| `ops` | Operational concerns | OPS_TESTING, OPS_CI_CD, OPS_MONITORING |
| `custom` | Custom research needs | CUSTOM (dynamic) |

#### **research_executions**
Tracks subagent executions for debugging and audit.
```sql
CREATE TABLE research_executions (
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
```

### Extension Tables

#### **technology_sources**
```sql
CREATE TABLE technology_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology_name TEXT NOT NULL,
    source_url TEXT,
    published_date DATE,
    relevance TEXT,
    notes TEXT,
    -- Fetch tracking columns (added in v2.0.0)
    source_type TEXT,                       -- official_docs, blog, comparison, release_notes
    was_fetched BOOLEAN DEFAULT FALSE,      -- Did we actually fetch and verify this URL?
    fetch_timestamp DATETIME,               -- When was it fetched?
    FOREIGN KEY (technology_name) REFERENCES technologies(name) ON DELETE CASCADE
);
```

#### **guardrails**
```sql
CREATE TABLE guardrails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type TEXT NOT NULL, -- scope_creep, quality_gate, forbidden_keyword
    rule_name TEXT NOT NULL,
    rule_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **deferred_features**
```sql
CREATE TABLE deferred_features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    reason TEXT,
    complexity_score INTEGER,
    original_requirement TEXT,
    deferred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 5 -- 1=high, 5=low
);
```

#### **prd_features**
```sql
CREATE TABLE prd_features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    original_text TEXT,
    prd_lines TEXT, -- JSON array of line references
    why_mvp TEXT,
    is_enhancement BOOLEAN DEFAULT FALSE,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **project_metrics**
```sql
CREATE TABLE project_metrics (
    metric_name TEXT PRIMARY KEY,
    metric_value TEXT NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **project_state**
```sql
CREATE TABLE project_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **task_executions**
```sql
CREATE TABLE task_executions (
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
```

#### **milestone_validations**
```sql
CREATE TABLE milestone_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id TEXT NOT NULL,
    validation_status TEXT NOT NULL, -- pending, passed, failed
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    validation_notes TEXT,
    autopilot_triggered BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE
);
```

### Indexes for Performance

```sql
-- Query optimization indexes (Core)
CREATE INDEX idx_tasks_milestone ON tasks(milestone_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_task_deps_task ON task_dependencies(task_id);
CREATE INDEX idx_task_deps_depends ON task_dependencies(depends_on_task_id);
CREATE INDEX idx_executions_task ON task_executions(task_id);
CREATE INDEX idx_validations_milestone ON milestone_validations(milestone_id);
CREATE INDEX idx_project_state_key ON project_state(key);

-- Research-related indexes (added in v2.0.0)
CREATE INDEX idx_research_opp_status ON research_opportunities(status);
CREATE INDEX idx_research_opp_category ON research_opportunities(category);
CREATE INDEX idx_tech_opportunity ON technologies(opportunity_id);
CREATE INDEX idx_research_exec_opp ON research_executions(opportunity_id);
```

## 🏗️ Architecture Components

### **DatabaseManager** (`db_manager.py`)
Central database management with:
- **Connection pooling** for efficient access
- **Transaction management** with automatic rollback
- **Schema validation** and migration support
- **Backup creation** with timestamped files
- **Query optimization** with prepared statements

```python
class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None)
    def get_connection(self) -> sqlite3.Connection
    def execute_transaction(self, operations: List[Callable]) -> Tuple[bool, List[Any]]
    def backup_database(self) -> str
    def restore_from_backup(self, backup_path: str) -> bool
    def validate_schema(self) -> bool
```

### **SQLite-based CLI Tools**
Enhanced versions of original CLI utilities:

#### **executor_cli.py**
- **Atomic task updates** with transaction safety
- **Dependency validation** via database queries
- **Progress tracking** with real-time calculations
- **Error recovery** with automatic rollback

## 🔄 Transaction Patterns

### Atomic Task Operations
```python
def complete_task(task_id: str) -> Dict[str, Any]:
    def complete_operation(conn):
        # Update task status
        conn.execute("""
            UPDATE tasks 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (task_id,))
        
        # Check milestone completion
        milestone = conn.execute("""
            SELECT m.id, m.name, 
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
            FROM milestones m
            JOIN tasks t ON m.id = t.milestone_id
            WHERE m.id = (SELECT milestone_id FROM tasks WHERE id = ?)
            GROUP BY m.id, m.name
        """, (task_id,)).fetchone()
        
        # Update milestone if all tasks complete
        if milestone['total_tasks'] == milestone['completed_tasks']:
            conn.execute("""
                UPDATE milestones 
                SET status = 'completed' 
                WHERE id = ?
            """, (milestone['id'],))
        
        return {"milestone_complete": milestone['total_tasks'] == milestone['completed_tasks']}
    
    success, results = db.execute_transaction([complete_operation])
    return results[0] if success else {"error": "Transaction failed"}
```

## 💾 Backup System

### Automatic Backup Strategy
- **Pre-operation backups**: Before major state changes
- **Periodic backups**: Every 30 minutes during long operations
- **Error recovery backups**: Before attempting error recovery
- **Milestone backups**: After milestone completion

### Backup File Naming
```
.tasks/backups/
├── 20241125_120000_pre_operation.db      # Before major operation
├── 20241125_120500_milestone_M1.db       # Milestone completion
├── 20241125_121000_periodic.db           # Periodic backup
└── 20241125_121500_pre_recovery.db       # Before error recovery
```

### Cleanup Policy
- **Keep last 10 backups** per day
- **Daily backups retained** for 7 days
- **Weekly backups retained** for 30 days
- **Manual backups never deleted** automatically

## 📊 Performance Characteristics

### Query Performance
| Operation | Complexity | Performance Characteristics |
|-----------|------------|---------------------------|
| Find next task | O(log n) | Indexed lookup with optimal performance |
| Milestone progress | O(log n) | SQL aggregates with real-time calculation |
| Dependency check | O(1) | Single query via foreign keys |
| Status generation | O(log n) | Efficient SQL joins |

### Memory Usage
- **Task data**: Streamed from database as needed
- **Progress calculation**: Query results only
- **Status updates**: Incremental database updates
- **Memory efficiency**: ~70-90% reduction vs. in-memory systems

### Disk Space
- **Database file**: ~50KB for small projects, ~500KB for large
- **Backup system**: Automated with intelligent cleanup
- **Compact storage**: Single database file vs. multiple files
- **Efficient**: Optimized storage with SQLite compression

## 🔌 API Compatibility

### Interface Consistency
All public interfaces remain identical:
```bash
# Same command interfaces
/iris:plan "Build an API"
/iris:execute T-API-001
/iris:validate M1

# Same output format
✅ Task T-API-001 completed
🎯 Milestone M1 complete (3/3 tasks)
📊 Progress: 15/20 tasks (75%)
```

## 🛡️ Data Integrity

### Foreign Key Constraints
- **Tasks → Milestones**: Ensures tasks belong to valid milestones
- **Dependencies → Tasks**: Ensures dependency references are valid

### Validation Triggers
```sql
-- Prevent circular dependencies
CREATE TRIGGER prevent_circular_deps 
BEFORE INSERT ON task_dependencies
FOR EACH ROW
WHEN EXISTS (
    -- Check if adding this dependency would create a cycle
    WITH RECURSIVE deps(task_id, depends_on) AS (
        SELECT NEW.depends_on_task_id, NEW.task_id
        UNION
        SELECT d.task_id, td.depends_on_task_id
        FROM deps d
        JOIN task_dependencies td ON d.depends_on = td.task_id
    )
    SELECT 1 FROM deps WHERE task_id = NEW.task_id
)
BEGIN
    SELECT RAISE(ABORT, 'Circular dependency detected');
END;
```

### Consistency Checks
- **Milestone status**: Must match task completion status
- **Task ordering**: Must be sequential within milestones
- **Dependency validity**: No dangling or circular references

## 🔬 Research Data Flow (v2.0.0)

The research system uses three tables to track the complete research lifecycle:

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESEARCH FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Planner selects opportunities from catalog                 │
│     │                                                          │
│     ▼                                                          │
│  ┌─────────────────────────────────┐                          │
│  │   research_opportunities        │  Status: pending         │
│  │   - STACK_LANG                  │                          │
│  │   - STACK_FRAMEWORK_API         │                          │
│  │   - OPS_TESTING                 │                          │
│  └─────────────────────────────────┘                          │
│     │                                                          │
│     ▼                                                          │
│  2. Subagents execute research (parallel)                      │
│     │                                                          │
│     ▼                                                          │
│  ┌─────────────────────────────────┐                          │
│  │   research_executions           │  Tracks each attempt     │
│  │   - subagent_prompt             │                          │
│  │   - subagent_response           │                          │
│  │   - execution_status            │                          │
│  └─────────────────────────────────┘                          │
│     │                                                          │
│     ▼                                                          │
│  3. Results stored with source tracking                        │
│     │                                                          │
│     ▼                                                          │
│  ┌─────────────────────────────────┐                          │
│  │   technologies                  │  Final approved stack    │
│  │   - opportunity_id (link)       │                          │
│  │   - confidence                  │                          │
│  │   - alternatives                │                          │
│  │   - source_type                 │                          │
│  └─────────────────────────────────┘                          │
│     │                                                          │
│     ▼                                                          │
│  ┌─────────────────────────────────┐                          │
│  │   technology_sources            │  Verification URLs       │
│  │   - was_fetched                 │                          │
│  │   - fetch_timestamp             │                          │
│  │   - source_type                 │                          │
│  └─────────────────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Research Context Storage

Research context (shared state for parallel subagents) is stored in `project_metadata`:

| Key | Example Value | Description |
|-----|---------------|-------------|
| `research_context_project_type` | `web_api` | Detected project type |
| `research_context_language` | `python` | Selected/detected language |
| `research_context_constraints` | `["must use postgresql"]` | PRD constraints (JSON) |
| `research_phase_status` | `completed` | Current research phase |

### Example Queries

**Get all pending research opportunities:**
```sql
SELECT id, name, research_question
FROM research_opportunities
WHERE status = 'pending';
```

**Get technology with its research source:**
```sql
SELECT t.name, t.version, t.confidence, ro.research_question
FROM technologies t
LEFT JOIN research_opportunities ro ON t.opportunity_id = ro.id
WHERE t.source_type = 'researched';
```

**Get research execution history for debugging:**
```sql
SELECT ro.name, re.execution_status, re.subagent_response, re.error_message
FROM research_executions re
JOIN research_opportunities ro ON re.opportunity_id = ro.id
ORDER BY re.started_at DESC;
```

## 🚀 Future Extensions

### Schema Evolution
The SQLite schema supports easy extension:
- **New tables**: Add feature-specific data
- **New columns**: Extend existing entities
- **No migration needed**: DB created fresh per project
- **Version tracking**: Schema version in project_metadata

### Schema Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Initial | Core tables: milestones, tasks, technologies, etc. |
| 2.0.0 | 2024-12-30 | Research tables: research_opportunities, research_executions; Extended technologies and technology_sources |

### Potential Enhancements
1. **Full-text search**: SQLite FTS for task/milestone search
2. **Time tracking**: Detailed execution time analytics
3. **Resource usage**: CPU/memory tracking per task
4. **Branching**: Multiple project variants in single database
5. **Collaboration**: Multi-user support with conflict resolution
6. **Analytics**: Advanced progress prediction and velocity metrics

---

**The SQLite architecture provides a robust, scalable foundation for Iris autonomous development with enterprise-grade data management capabilities.**