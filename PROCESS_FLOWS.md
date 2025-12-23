# IRIS Process Flow Documentation

This document provides visual process flows for each IRIS command, showing expected inputs, outputs, and decision points.

---

## Table of Contents

1. [Command Overview & Relationships](#command-overview--relationships)
2. [/iris:autopilot Flow](#irisautopilot-flow)
3. [/iris:plan Flow](#irisplan-flow)
4. [/iris:execute Flow](#irisexecute-flow)
5. [/iris:validate Flow](#irisvalidate-flow)
6. [/iris:document Flow](#irisdocument-flow)
7. [/iris:audit Flow](#irisaudit-flow)
8. [Database State Transitions](#database-state-transitions)

---

## Command Overview & Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IRIS COMMAND ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     /iris:autopilot                                 │   │
│   │   (Primary Entry - Orchestrates entire development lifecycle)       │   │
│   └───────────────────────────┬─────────────────────────────────────────┘   │
│                               │                                             │
│       ┌───────────────────────┼───────────────────────┐                     │
│       │                       │                       │                     │
│       ▼                       ▼                       ▼                     │
│   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐                   │
│   │  plan   │──▶│ execute │──▶│ validate │──▶│ document │                   │
│   │(Phase 1)│   │(Phase 2)│   │(Phase 3) │   │(Phase 4) │                   │
│   └─────────┘   └────┬────┘   └──────────┘   └────┬─────┘                   │
│                      │                            │                         │
│                      │◀───────────────────────────┘                         │
│                      │     (loop per milestone)                             │
│                      ▼                                                      │
│                  ┌────────┐                                                 │
│                  │  DONE  │                                                 │
│                  └────────┘                                                 │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                     STANDALONE COMMANDS                           │     │
│   ├───────────────────────────────────────────────────────────────────┤     │
│   │                                                                   │     │
│   │  ┌───────────────────────────┐  ┌───────────────────────────┐    │     │
│   │  │     /iris:document       │  │       /iris:audit         │    │     │
│   │  │      (Standalone)        │  │       (Security)          │    │     │
│   │  └───────────────────────────┘  └───────────────────────────┘    │     │
│   │                                                                   │     │
│   │                           │                                       │     │
│   │                           ▼                                       │     │
│   │               ┌───────────────────────┐                           │     │
│   │               │   SQLite Database     │                           │     │
│   │               │  (.tasks/iris_project │                           │     │
│   │               │        .db)           │                           │     │
│   │               └───────────────────────┘                           │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## /iris:autopilot Flow

**Purpose:** Autonomous end-to-end development from PRD to working application.

**Input:** PRD text or "resume" keyword
**Output:** Complete working application with all milestones validated

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         /iris:autopilot <PRD>                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INITIALIZATION PHASE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Run autopilot_init.py                                              │   │
│   │  ├── Detect IRIS directory (local or global ~/.claude)             │   │
│   │  ├── Check permissions (--dangerously-skip-permissions)            │   │
│   │  ├── Detect existing project (.tasks/iris_project.db exists?)      │   │
│   │  └── Output: PROJECT_ROOT, IRIS_DIR, SKIP_PLANNING                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Set Environment Variables                                          │   │
│   │  ├── IRIS_AUTOPILOT_ACTIVE=true                                    │   │
│   │  └── IRIS_PROJECT_ROOT=<path>                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      SKIP_PLANNING?           │
                    └───────────────────────────────┘
                           │              │
                     false │              │ true (resuming)
                           ▼              │
┌──────────────────────────────────────┐  │
│         PHASE 1: PLANNING            │  │
├──────────────────────────────────────┤  │
│                                      │  │
│  ┌────────────────────────────────┐  │  │
│  │ Invoke /iris:plan with PRD    │  │  │
│  │ (See /iris:plan flow below)   │  │  │
│  └────────────────────────────────┘  │  │
│             │                        │  │
│             ▼                        │  │
│  ┌────────────────────────────────┐  │  │
│  │ Verify Planning Success:      │  │  │
│  │ ├── milestones.count > 0      │  │  │
│  │ └── tasks.count > 0           │  │  │
│  └────────────────────────────────┘  │  │
│                                      │  │
└──────────────────────────────────────┘  │
                           │              │
                           └──────┬───────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: EXECUTION LOOP                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      CONTINUOUS LOOP                                │   │
│   │  ┌──────────────────────────────────────────────────────────────┐   │   │
│   │  │                                                              │   │   │
│   │  │  ┌────────────────────────────────────────────────────────┐  │   │   │
│   │  │  │  STEP 1: Get Next Eligible Task                        │  │   │   │
│   │  │  │  ├── Query: pending tasks with satisfied dependencies  │  │   │   │
│   │  │  │  ├── Check current_milestone_id                        │  │   │   │
│   │  │  │  └── Return: task_id, title, description, milestone    │  │   │   │
│   │  │  └────────────────────────────────────────────────────────┘  │   │   │
│   │  │                          │                                   │   │   │
│   │  │          ┌───────────────┼───────────────┐                   │   │   │
│   │  │          │               │               │                   │   │   │
│   │  │          ▼               ▼               ▼                   │   │   │
│   │  │   ┌───────────┐   ┌───────────┐   ┌───────────────────┐      │   │   │
│   │  │   │all_complete│   │milestone_ │   │     found        │      │   │   │
│   │  │   │           │   │complete   │   │                   │      │   │   │
│   │  │   └─────┬─────┘   └─────┬─────┘   └─────────┬─────────┘      │   │   │
│   │  │         │               │                   │                │   │   │
│   │  │         │               │                   ▼                │   │   │
│   │  │         │               │   ┌──────────────────────────────┐ │   │   │
│   │  │         │               │   │ STEP 2: Mark In-Progress    │ │   │   │
│   │  │         │               │   │ UPDATE tasks SET status =   │ │   │   │
│   │  │         │               │   │ 'in_progress'               │ │   │   │
│   │  │         │               │   └──────────────────────────────┘ │   │   │
│   │  │         │               │                   │                │   │   │
│   │  │         │               │                   ▼                │   │   │
│   │  │         │               │   ┌──────────────────────────────┐ │   │   │
│   │  │         │               │   │ STEP 3: IMPLEMENT TASK      │ │   │   │
│   │  │         │               │   │ ├── Read relevant files     │ │   │   │
│   │  │         │               │   │ ├── Write/Edit code         │ │   │   │
│   │  │         │               │   │ ├── Run tests               │ │   │   │
│   │  │         │               │   │ └── Quality checks          │ │   │   │
│   │  │         │               │   └──────────────────────────────┘ │   │   │
│   │  │         │               │                   │                │   │   │
│   │  │         │               │                   ▼                │   │   │
│   │  │         │               │   ┌──────────────────────────────┐ │   │   │
│   │  │         │               │   │ STEP 4: Mark Completed      │ │   │   │
│   │  │         │               │   │ UPDATE tasks SET status =   │ │   │   │
│   │  │         │               │   │ 'completed'                 │ │   │   │
│   │  │         │               │   └──────────────────────────────┘ │   │   │
│   │  │         │               │                   │                │   │   │
│   │  │         │               │                   ▼                │   │   │
│   │  │         │               │   ┌──────────────────────────────┐ │   │   │
│   │  │         │               │   │ STEP 5: Update Status       │ │   │   │
│   │  │         │               │   │ ├── Calculate progress %    │ │   │   │
│   │  │         │               │   │ └── Update PROJECT_STATUS.md│ │   │   │
│   │  │         │               │   └──────────────────────────────┘ │   │   │
│   │  │         │               │                   │                │   │   │
│   │  │         │               ▼                   │                │   │   │
│   │  │         │   ┌──────────────────────────┐    │                │   │   │
│   │  │         │   │ Validate Milestone       │    │                │   │   │
│   │  │         │   │ (if required)            │────┘                │   │   │
│   │  │         │   │ Move to next milestone   │                     │   │   │
│   │  │         │   └──────────────────────────┘                     │   │   │
│   │  │         │               │                                    │   │   │
│   │  │         │               └────────────────────────────────────┘   │   │
│   │  │         │                              ▲                         │   │
│   │  │         │                              │ LOOP                    │   │
│   │  │         │                              │                         │   │
│   │  └─────────┼──────────────────────────────┴─────────────────────────┘   │
│   │            │                                                            │
│   └────────────┼────────────────────────────────────────────────────────────┘
│                │                                                             │
└────────────────┼─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: FINAL VALIDATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Invoke /iris:validate                                              │   │
│   │  (See /iris:validate flow below)                                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Generate Completion Summary                                        │   │
│   │  ├── Total tasks completed                                         │   │
│   │  ├── Milestones completed                                          │   │
│   │  ├── Total execution time                                          │   │
│   │  └── Store autopilot_completed timestamp                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │    AUTOPILOT COMPLETE         │
                    │    Application ready!         │
                    └───────────────────────────────┘
```

### Autopilot Outputs

| Artifact | Description |
|----------|-------------|
| `.tasks/iris_project.db` | Complete project state in SQLite |
| `PROJECT_STATUS.md` | Human-readable progress report |
| `.tasks/backups/` | Automatic database backups |
| Application code | Fully implemented project |

---

## /iris:plan Flow

**Purpose:** Analyze PRD and create adaptive sprint plan with milestones and tasks.

**Input:** PRD text or file
**Output:** Populated database with milestones, tasks, technologies, and configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       /iris:plan <PRD>                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1A: ADAPTIVE ANALYSIS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Run iris_adaptive.py ProjectAnalyzer.analyze(prd)                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  OUTPUT: Complexity Configuration                                   │   │
│   │  ├── COMPLEXITY: micro | small | medium | large | enterprise       │   │
│   │  ├── PROJECT_TYPE: web | api | cli | library | mobile             │   │
│   │  ├── MAX_FEATURES: 2 | 3 | 7 | 10 | 15                            │   │
│   │  ├── RESEARCH_AGENTS: 0 | 2 | 4 | 6 | 8                           │   │
│   │  ├── TASKS_PER_MILESTONE: (min, max)                               │   │
│   │  ├── ENFORCE_TDD: true | false                                     │   │
│   │  └── VALIDATION_FREQUENCY: minimal | major | every | comprehensive │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1B: DATABASE INITIALIZATION                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Initialize SQLite Database                                         │   │
│   │  ├── Create .tasks/ directory                                      │   │
│   │  ├── Run schema.sql (create all tables)                            │   │
│   │  └── Validate schema                                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Store Configuration in project_metadata                            │   │
│   │  ├── analysis_timestamp                                            │   │
│   │  ├── project_complexity                                            │   │
│   │  ├── project_type                                                  │   │
│   │  ├── max_mvp_features                                              │   │
│   │  ├── research_agents_count                                         │   │
│   │  ├── tasks_per_milestone_min/max                                   │   │
│   │  ├── validation_frequency                                          │   │
│   │  ├── enforce_tdd                                                   │   │
│   │  └── skip_common_research                                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │    RESEARCH_AGENTS > 0?       │
                    └───────────────────────────────┘
                           │              │
                      yes  │              │ no (MICRO project)
                           ▼              │
┌──────────────────────────────────────┐  │
│      PHASE 2A: RESEARCH              │  │
├──────────────────────────────────────┤  │
│                                      │  │
│  ┌────────────────────────────────┐  │  │
│  │ Launch Research Sub-Agents     │  │  │
│  │ (parallel Task tool calls)     │  │  │
│  │                                │  │  │
│  │ SMALL (2 agents):              │  │  │
│  │ ├── SA-1-LANG (Language)       │  │  │
│  │ └── SA-3-TEST (Testing)        │  │  │
│  │                                │  │  │
│  │ MEDIUM (4 agents):             │  │  │
│  │ ├── SA-1-LANG                  │  │  │
│  │ ├── SA-2-ARCH (Architecture)   │  │  │
│  │ ├── SA-3-TEST                  │  │  │
│  │ └── SA-4-* (Type-specific)     │  │  │
│  │                                │  │  │
│  │ LARGE/ENTERPRISE (6-8 agents): │  │  │
│  │ ├── All above +                │  │  │
│  │ ├── SA-5-BACKEND               │  │  │
│  │ ├── SA-6-DATABASE              │  │  │
│  │ └── SA-7/8 (Compliance/Sec)    │  │  │
│  └────────────────────────────────┘  │  │
│             │                        │  │
│             ▼                        │  │
│  ┌────────────────────────────────┐  │  │
│  │ Store Research Results         │  │  │
│  │ INSERT INTO technologies       │  │  │
│  │ (name, category, version,      │  │  │
│  │  decision_reason, sources)     │  │  │
│  └────────────────────────────────┘  │  │
│                                      │  │
└──────────────────────────────────────┘  │
                           │              │
                           │              ▼
                           │   ┌──────────────────────────┐
                           │   │ Apply Default Tech Stack │
                           │   │ Python 3.9+ for MICRO   │
                           │   └──────────────────────────┘
                           │              │
                           └──────┬───────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 3A: MILESTONE & TASK CREATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: Analyze PRD & Design Structure                             │   │
│   │  ├── Extract features from requirements                            │   │
│   │  ├── Apply MAX_FEATURES limit                                      │   │
│   │  ├── Identify 2-5 milestones (logical phases)                      │   │
│   │  └── Break into MILESTONE_MIN to MILESTONE_MAX tasks each          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 2: Create Milestones                                          │   │
│   │  INSERT INTO milestones (id, name, description, status, order_index)│   │
│   │                                                                     │   │
│   │  Example:                                                           │   │
│   │  ├── M1: "Project Setup" (order: 0)                                │   │
│   │  ├── M2: "Core Features" (order: 1)                                │   │
│   │  ├── M3: "Integration" (order: 2)                                  │   │
│   │  └── M4: "Polish & Deploy" (order: 3)                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 3: Create Tasks                                               │   │
│   │  INSERT INTO tasks (id, milestone_id, title, description,          │   │
│   │                     status, order_index)                           │   │
│   │                                                                     │   │
│   │  Task ID Format: T-<FEATURE>-<SEQ>                                 │   │
│   │  Example:                                                           │   │
│   │  ├── T-SETUP-1: "Initialize project structure"                     │   │
│   │  ├── T-SETUP-2: "Configure dependencies"                           │   │
│   │  ├── T-AUTH-1: "Implement authentication"                          │   │
│   │  └── T-API-1: "Create API endpoints"                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 4: Set Initial State                                          │   │
│   │  UPDATE project_state SET value = 'M1'                             │   │
│   │  WHERE key = 'current_milestone_id'                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: VERIFICATION & REPORT                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Verify Database State                                              │   │
│   │  ├── SELECT COUNT(*) FROM milestones                               │   │
│   │  ├── SELECT COUNT(*) FROM tasks                                    │   │
│   │  └── SELECT value FROM project_state WHERE key='current_milestone' │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Generate Planning Report                                           │   │
│   │  ├── Project Complexity: [COMPLEXITY]                              │   │
│   │  ├── MVP Features: X of Y                                          │   │
│   │  ├── Research Agents: N                                            │   │
│   │  ├── Milestones: N created                                         │   │
│   │  ├── Tasks: N created                                              │   │
│   │  └── Quality Level: [minimal|basic|strict]                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       PLANNING COMPLETE       │
                    │                               │
                    │  If called from autopilot:    │
                    │  → Continue to Phase 2        │
                    │                               │
                    │  If standalone:               │
                    │  → Ready for /iris:execute    │
                    └───────────────────────────────┘
```

### Planning Outputs

| Table | Records Created |
|-------|-----------------|
| `project_metadata` | ~10 configuration keys |
| `milestones` | 2-5 milestones |
| `tasks` | 5-60+ tasks (based on complexity) |
| `technologies` | 1-10+ technology decisions |
| `project_state` | current_milestone_id set |

---

## /iris:execute Flow

**Purpose:** Execute individual tasks with TDD methodology and quality enforcement.

**Input:** Optional task-id (defaults to next eligible task)
**Output:** Completed task with code changes, tests, and status updates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    /iris:execute [task-id]                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: TASK SELECTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Load Adaptive Configuration                                        │   │
│   │  ├── project_complexity                                            │   │
│   │  ├── project_type                                                  │   │
│   │  ├── enforce_tdd                                                   │   │
│   │  └── validation_frequency                                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Check Sprint Status                                                │   │
│   │  ├── validation_required?                                          │   │
│   │  └── blocked_reason?                                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                  │
│              ▼                                           ▼                  │
│   ┌──────────────────────┐                ┌──────────────────────────────┐  │
│   │  MANUAL MODE         │                │  AUTOPILOT MODE              │  │
│   │  If validation       │                │  Log warning, continue       │  │
│   │  required → BLOCK    │                │  execution                   │  │
│   └──────────────────────┘                └──────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Get Next Eligible Task                                             │   │
│   │  SELECT * FROM tasks                                               │   │
│   │  WHERE status = 'pending'                                          │   │
│   │  AND milestone_id = current_milestone                              │   │
│   │  AND all dependencies satisfied                                    │   │
│   │  ORDER BY order_index LIMIT 1                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: PRE-TASK VALIDATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: Validate Dependencies                                      │   │
│   │  ├── Check task_dependencies table                                 │   │
│   │  ├── Verify all depends_on_task_id have status = 'completed'       │   │
│   │  └── Output: satisfied = true/false                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 2: Check Scope Compliance                                     │   │
│   │  ├── must_implement: [required items]                              │   │
│   │  ├── must_not_implement: [forbidden items]                         │   │
│   │  └── max_files: N (file change limit)                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 3: Validate Tech Stack                                        │   │
│   │  ├── Compare task technologies vs. approved stack                  │   │
│   │  └── Output: compliant = true/false                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: TASK EXECUTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Mark Task In-Progress                                              │   │
│   │  UPDATE tasks SET status = 'in_progress',                          │   │
│   │                   started_at = datetime('now')                     │   │
│   │  WHERE id = task_id                                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│                    ┌───────────────────────────────┐                        │
│                    │       TDD_REQUIRED?           │                        │
│                    └───────────────────────────────┘                        │
│                           │              │                                  │
│                      yes  │              │ no                               │
│                           ▼              ▼                                  │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    TDD EXECUTION CYCLE                            │     │
│   │  ┌──────────────────────────────────────────────────────────────┐ │     │
│   │  │                                                              │ │     │
│   │  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │ │     │
│   │  │   │    RED      │───▶│   GREEN     │───▶│  REFACTOR   │     │ │     │
│   │  │   │             │    │             │    │             │     │ │     │
│   │  │   │ Write tests │    │ Write code  │    │ Clean up    │     │ │     │
│   │  │   │ (failing)   │    │ (pass tests)│    │ (tests pass)│     │ │     │
│   │  │   └─────────────┘    └─────────────┘    └─────────────┘     │ │     │
│   │  │                                                              │ │     │
│   │  └──────────────────────────────────────────────────────────────┘ │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Implementation Steps (Claude executes directly)                    │   │
│   │  ├── Read relevant existing files                                  │   │
│   │  ├── Write new code files                                          │   │
│   │  ├── Edit existing files                                           │   │
│   │  ├── Run tests: npm test / pytest / go test                       │   │
│   │  ├── Run linter: npm run lint / flake8 / golangci-lint            │   │
│   │  └── Run build: npm run build / go build                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: TASK COMPLETION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Quality Gates (must all pass)                                      │   │
│   │  ├── ✅ All tests pass (100% success)                              │   │
│   │  ├── ✅ Test coverage meets threshold                              │   │
│   │  ├── ✅ Zero lint/type errors                                      │   │
│   │  ├── ✅ Build succeeds                                             │   │
│   │  └── ✅ Scope boundaries respected                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Mark Task Completed                                                │   │
│   │  UPDATE tasks SET                                                  │   │
│   │    status = 'completed',                                           │   │
│   │    completed_at = datetime('now'),                                 │   │
│   │    duration_minutes = (now - started_at)                           │   │
│   │  WHERE id = task_id                                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Update PROJECT_STATUS.md                                           │   │
│   │  (via /iris:document after milestone)                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│                    ┌───────────────────────────────┐                        │
│                    │   Milestone Complete?         │                        │
│                    │   (all tasks in milestone     │                        │
│                    │    have status='completed')   │                        │
│                    └───────────────────────────────┘                        │
│                           │              │                                  │
│                      yes  │              │ no                               │
│                           ▼              ▼                                  │
│            ┌──────────────────────┐    ┌──────────────────┐                 │
│            │  Trigger Validation  │    │  Ready for       │                 │
│            │  /iris:validate      │    │  next task       │                 │
│            │  (auto in autopilot) │    │  /iris:execute   │                 │
│            └──────────────────────┘    └──────────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Execution Outputs

| Output | Description |
|--------|-------------|
| Code files | New/modified source code |
| Test files | New/modified test files |
| Task status | Updated to 'completed' in database |
| Progress % | Updated in PROJECT_STATUS.md |
| Duration | Recorded in tasks table |

---

## /iris:validate Flow

**Purpose:** Validate milestone completion and application readiness.

**Input:** Optional milestone-id (defaults to current milestone)
**Output:** Validation report with pass/fail status

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  /iris:validate [milestone-id]                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INITIALIZATION                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Determine Validation Mode                                          │   │
│   │  ├── IRIS_MANUAL_MODE=true → Manual (human review required)        │   │
│   │  └── default → Autopilot (automated validation)                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Get Milestone ID                                                   │   │
│   │  ├── Use provided argument, OR                                     │   │
│   │  └── Query first pending/in_progress milestone                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Load Project Complexity                                            │   │
│   │  ├── micro → MINIMAL validation                                    │   │
│   │  ├── small → STANDARD validation                                   │   │
│   │  ├── medium/large → COMPREHENSIVE validation                       │   │
│   │  └── enterprise → ENTERPRISE validation                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VALIDATION PHASES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 1: Application Launch Test                                   │   │
│   │  ├── Detect project type (web, cli, api, etc.)                     │   │
│   │  ├── Execute appropriate launch command:                           │   │
│   │  │   ├── Web: npm run dev / yarn dev                              │   │
│   │  │   ├── API: start server, check /health                         │   │
│   │  │   └── CLI: run --help command                                  │   │
│   │  ├── Verify: no startup errors                                     │   │
│   │  └── Output: LAUNCH_SUCCESS = true/false                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 2: Feature Validation                                        │   │
│   │  ├── Read milestone tasks from database                            │   │
│   │  ├── For each task's scope_boundaries:                             │   │
│   │  │   ├── Execute test scenarios                                   │   │
│   │  │   ├── Document pass/fail                                       │   │
│   │  │   └── Capture evidence (screenshots if UI)                     │   │
│   │  ├── Verify critical features work                                 │   │
│   │  └── Test basic user flows                                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 3: Integration Testing                                       │   │
│   │  ├── Run existing test suites                                      │   │
│   │  ├── Check database connectivity (if applicable)                   │   │
│   │  ├── Verify API endpoints respond                                  │   │
│   │  ├── Test data persistence                                         │   │
│   │  └── Validate UI ↔ backend integration                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 4: Code Quality Check                                        │   │
│   │  ├── Run linting (0 errors required)                               │   │
│   │  ├── Run type checking (if applicable)                             │   │
│   │  ├── Check test coverage vs. threshold                             │   │
│   │  ├── Scan for TODO/FIXME comments                                  │   │
│   │  └── Check for debug statements (console.log, print)              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 5: Run Autonomous Validator                                  │   │
│   │  python3 autonomous_validator.py $PROJECT_ROOT $IRIS_DIR $MILESTONE │   │
│   │  ├── Graduated validation based on complexity                      │   │
│   │  ├── Smoke tests                                                   │   │
│   │  ├── Performance baselines                                         │   │
│   │  ├── Security scanning                                             │   │
│   │  └── Accessibility checks (web apps)                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      VALIDATION PASSED?       │
                    └───────────────────────────────┘
                           │              │
                      yes  │              │ no
                           ▼              ▼
┌──────────────────────────────────┐  ┌──────────────────────────────────────┐
│         VALIDATION PASSED        │  │         VALIDATION FAILED            │
├──────────────────────────────────┤  ├──────────────────────────────────────┤
│                                  │  │                                      │
│  ┌────────────────────────────┐  │  │  ┌──────────────────────────────┐    │
│  │ Update Database            │  │  │  │ Log Failure                  │    │
│  │ UPDATE milestones          │  │  │  │ ├── Record issues            │    │
│  │ SET status = 'validated'   │  │  │  │ └── Store in metadata        │    │
│  └────────────────────────────┘  │  │  └──────────────────────────────┘    │
│             │                    │  │               │                      │
│             ▼                    │  │               ▼                      │
│  ┌────────────────────────────┐  │  │  ┌────────────────────────────────┐  │
│  │ Mode Check                 │  │  │  │ Mode Check                     │  │
│  └────────────────────────────┘  │  │  └────────────────────────────────┘  │
│        │            │            │  │         │              │             │
│   Manual│       Autopilot        │  │    Manual│        Autopilot          │
│        ▼            ▼            │  │         ▼              ▼             │
│  ┌──────────┐ ┌──────────────┐   │  │  ┌───────────┐  ┌────────────────┐   │
│  │ PAUSE    │ │ Continue     │   │  │  │ HALT      │  │ Log & attempt  │   │
│  │ Human    │ │ automatically│   │  │  │ execution │  │ recovery       │   │
│  │ review   │ │ to next      │   │  │  │           │  │                │   │
│  │ required │ │ milestone    │   │  │  └───────────┘  └────────────────┘   │
│  └──────────┘ └──────────────┘   │  │                                      │
│                                  │  │                                      │
└──────────────────────────────────┘  └──────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UPDATE STATUS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Record Validation                                                  │   │
│   │  INSERT INTO project_metadata                                      │   │
│   │    (key = 'validation_M1', value = timestamp)                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Update PROJECT_STATUS.md                                           │   │
│   │  (via /iris:document after validation)                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Validation Levels by Complexity

| Complexity | Validation Level | Checks Performed |
|------------|------------------|------------------|
| MICRO | MINIMAL | App launches, basic function |
| SMALL | STANDARD | + core features, basic tests |
| MEDIUM | COMPREHENSIVE | + integration, quality gates |
| LARGE | COMPREHENSIVE | + performance, full coverage |
| ENTERPRISE | ENTERPRISE | + security, accessibility, compliance |

---

## /iris:document Flow

**Purpose:** Generate and maintain project documentation. Can run standalone or as part of the autopilot loop.

**Input:** Optional flags: `--standalone`, `--milestone <id>`, `--final`
**Output:** README.md, PROJECT_STATUS.md, COMPLETION_REPORT.md (on final)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      /iris:document [flags]                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODE DETECTION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Check for IRIS Database                                            │   │
│   │  ├── .tasks/iris_project.db exists?                                │   │
│   │  └── --standalone flag provided?                                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                  │
│              ▼                                           ▼                  │
│   ┌──────────────────────┐                ┌──────────────────────────────┐  │
│   │   STANDALONE MODE    │                │      LOOP MODE               │  │
│   │   (No database)      │                │   (IRIS-managed project)     │  │
│   └──────────────────────┘                └──────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                     │                                      │
                     ▼                                      ▼
┌────────────────────────────────────┐   ┌────────────────────────────────────┐
│      STANDALONE ANALYSIS           │   │         LOOP UPDATES               │
├────────────────────────────────────┤   ├────────────────────────────────────┤
│                                    │   │                                    │
│  ┌──────────────────────────────┐  │   │  ┌──────────────────────────────┐  │
│  │ Scan Project Structure       │  │   │  │ Read Database State          │  │
│  │ ├── Detect package.json     │  │   │  │ ├── Get milestones          │  │
│  │ ├── Detect requirements.txt │  │   │  │ ├── Get completed tasks     │  │
│  │ ├── Detect go.mod           │  │   │  │ ├── Get technologies        │  │
│  │ └── Identify frameworks     │  │   │  │ └── Get project metadata    │  │
│  └──────────────────────────────┘  │   │  └──────────────────────────────┘  │
│             │                      │   │               │                    │
│             ▼                      │   │               ▼                    │
│  ┌──────────────────────────────┐  │   │  ┌──────────────────────────────┐  │
│  │ Generate Documentation       │  │   │  │ Generate Documentation       │  │
│  │ ├── README.md (inferred)    │  │   │  │ ├── README.md (from DB)     │  │
│  │ └── PROJECT_STATUS.md       │  │   │  │ ├── PROJECT_STATUS.md       │  │
│  └──────────────────────────────┘  │   │  │ └── Features from milestones│  │
│                                    │   │  └──────────────────────────────┘  │
└────────────────────────────────────┘   │                                    │
                                         └────────────────────────────────────┘
                                                          │
                                                          ▼
                                         ┌────────────────────────────────┐
                                         │       --final FLAG SET?        │
                                         └────────────────────────────────┘
                                                │              │
                                           yes  │              │ no
                                                ▼              ▼
                              ┌──────────────────────────┐    ┌──────────┐
                              │  COMPLETION REPORT       │    │   Done   │
                              ├──────────────────────────┤    └──────────┘
                              │                          │
                              │  Calculate KPIs:         │
                              │  ├── Total time          │
                              │  ├── Tasks completed     │
                              │  ├── Milestones done     │
                              │  ├── Avg task duration   │
                              │  ├── Validations passed  │
                              │  └── Errors recovered    │
                              │                          │
                              │  Outputs:                │
                              │  ├── Terminal summary    │
                              │  └── COMPLETION_REPORT.md│
                              │                          │
                              └──────────────────────────┘
```

### Document Outputs

| Output | When Generated | Description |
|--------|----------------|-------------|
| `README.md` | Every run | Project documentation with features, install, usage |
| `PROJECT_STATUS.md` | Every run | Current progress, milestones, tasks |
| `COMPLETION_REPORT.md` | `--final` only | Full KPI report with metrics |

### Terminal Output (Final Mode)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    IRIS PROJECT COMPLETION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PROJECT:        My Project
  STATUS:         COMPLETE
  COMPLEXITY:     MEDIUM

  EXECUTION METRICS
  ─────────────────────────────────────────────────

  Total Time          45 minutes
  Tasks Completed     12 / 12 (100%)
  Milestones          3 / 3 (100%)
  Avg Task Duration   3.8 minutes

  QUALITY METRICS
  ─────────────────────────────────────────────────

  Validations Passed  3 / 3 (100%)
  Errors Recovered    2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## /iris:audit Flow

**Purpose:** Security analysis focusing on production-ready foundations.

**Input:** Scope: dependencies | auth | owasp | zerotrust | all
**Output:** Security report with findings and recommendations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    /iris:audit [scope]                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCOPE DETECTION                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Parse Scope Argument (default: "all")                              │   │
│   │  ├── dependencies → Dependency vulnerability scan                  │   │
│   │  ├── auth → Authentication pattern analysis                        │   │
│   │  ├── owasp → OWASP Top 10 basic checks                            │   │
│   │  ├── zerotrust → Zero Trust architecture validation               │   │
│   │  └── all → Run all four phases                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
        ┌─────────────────────┐       ┌─────────────────────────────┐
        │  scope=dependencies │       │  scope=auth/owasp/zerotrust │
        │  OR scope=all       │       │  OR scope=all               │
        └─────────────────────┘       └─────────────────────────────┘
                     │                             │
                     ▼                             │
┌──────────────────────────────────────┐           │
│  PHASE 1: DEPENDENCY ANALYSIS        │           │
├──────────────────────────────────────┤           │
│                                      │           │
│  ┌────────────────────────────────┐  │           │
│  │ Detect Project Type            │  │           │
│  │ ├── package.json → npm audit   │  │           │
│  │ ├── requirements.txt → pip-aud │  │           │
│  │ ├── go.mod → govulncheck      │  │           │
│  │ └── Cargo.toml → cargo audit  │  │           │
│  └────────────────────────────────┘  │           │
│             │                        │           │
│             ▼                        │           │
│  ┌────────────────────────────────┐  │           │
│  │ Run Vulnerability Scan         │  │           │
│  │ ├── Critical vulnerabilities   │  │           │
│  │ ├── High severity issues       │  │           │
│  │ └── Outdated packages          │  │           │
│  └────────────────────────────────┘  │           │
│                                      │           │
└──────────────────────────────────────┘           │
                     │                             │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: AUTHENTICATION ANALYSIS (if scope=auth or all)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Search Authentication Patterns                                     │   │
│   │  rg -i "auth|login|session|jwt|token|password"                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Validate Session Management                                        │   │
│   │  rg -i "session|cookie|expire|timeout"                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Check Password Security                                            │   │
│   │  rg -i "password|hash|bcrypt|scrypt|argon"                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Review JWT Implementation                                          │   │
│   │  rg -i "jwt|jsonwebtoken|verify|secret"                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: OWASP TOP 10 CHECKS (if scope=owasp or all)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  A01: Broken Access Control                                         │   │
│   │  rg -i "authorize|permission|role|admin|access"                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  A02: Cryptographic Failures                                        │   │
│   │  rg -i "md5|sha1|crypto|encrypt|decrypt"                           │   │
│   │  (Flag weak algorithms: MD5, SHA1)                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  A03: Injection Vulnerabilities                                     │   │
│   │  rg -i "sql|query|exec|eval|innerHTML"                             │   │
│   │  (Flag dangerous patterns)                                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  A05: Security Misconfiguration                                     │   │
│   │  rg -i "cors|header|config|debug|error"                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  A07: Authentication Failures                                       │   │
│   │  (Covered in Phase 2)                                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: ZERO TRUST VALIDATION (if scope=zerotrust or all)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Never Trust, Always Verify                                         │   │
│   │  rg -i "middleware|guard|auth|verify"                              │   │
│   │  (Check: auth on all endpoints)                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Least Privilege Access                                             │   │
│   │  rg -i "permission|role|scope|access"                              │   │
│   │  (Check: granular permissions)                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Assume Breach - Logging                                            │   │
│   │  rg -i "log|audit|monitor|track"                                   │   │
│   │  (Check: comprehensive logging)                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Micro-segmentation                                                 │   │
│   │  rg -i "service|api|endpoint|route"                                │   │
│   │  (Check: clear service boundaries)                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Data Protection                                                    │   │
│   │  rg -i "encrypt|hash|sanitize|validate"                           │   │
│   │  (Check: data handling patterns)                                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GENERATE SECURITY REPORT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Calculate Risk Scores                                              │   │
│   │  ├── Dependencies: HIGH/MEDIUM/LOW                                 │   │
│   │  ├── Authentication: SECURE/NEEDS_REVIEW                           │   │
│   │  ├── OWASP Top 10: issues per category                            │   │
│   │  └── Zero Trust: compliance percentage                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Write Report: .tasks/security_report.md                            │   │
│   │  ├── Summary by category                                           │   │
│   │  ├── Detailed findings                                             │   │
│   │  ├── Immediate actions needed                                      │   │
│   │  └── Production readiness recommendations                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      AUDIT COMPLETE           │
                    │                               │
                    │  Report: .tasks/security_     │
                    │          report.md            │
                    └───────────────────────────────┘
```

### Audit Outputs

| Output File | Description |
|-------------|-------------|
| `.tasks/security_report.md` | Main security analysis summary |
| `.tasks/dependencies.log` | Dependency scan results |
| `.tasks/auth_analysis.log` | Authentication review |
| `.tasks/owasp_check.log` | OWASP validation |
| `.tasks/zerotrust_review.log` | ZTA pattern analysis |

---

## Database State Transitions

This diagram shows how the database state changes throughout the IRIS lifecycle.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATABASE STATE MACHINE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────┐
                    │        INITIAL STATE          │
                    │    (No database exists)       │
                    └───────────────────────────────┘
                                    │
                                    │ /iris:plan
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PLANNED STATE                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   project_metadata:                                                         │
│   ├── analysis_timestamp: set                                              │
│   ├── project_complexity: micro|small|medium|large|enterprise             │
│   └── (other config keys)                                                  │
│                                                                             │
│   milestones:                                                               │
│   ├── M1: status = 'pending'                                               │
│   ├── M2: status = 'pending'                                               │
│   └── ...                                                                  │
│                                                                             │
│   tasks:                                                                    │
│   ├── T-*: status = 'pending'                                              │
│   └── (all tasks pending)                                                  │
│                                                                             │
│   project_state:                                                            │
│   └── current_milestone_id = 'M1'                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ /iris:execute (first task)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXECUTING STATE                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   milestones:                                                               │
│   ├── M1: status = 'in_progress' (implicit)                                │
│   └── M2+: status = 'pending'                                              │
│                                                                             │
│   tasks:                                                                    │
│   ├── T-*-1: status = 'in_progress', started_at = timestamp               │
│   ├── T-*-2: status = 'pending'                                            │
│   └── ...                                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Task completion
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROGRESSING STATE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   tasks:                                                                    │
│   ├── T-*-1: status = 'completed', completed_at = timestamp               │
│   ├── T-*-2: status = 'completed', completed_at = timestamp               │
│   ├── T-*-3: status = 'in_progress'                                        │
│   └── T-*-4+: status = 'pending'                                           │
│                                                                             │
│   (Repeats until milestone complete)                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ All milestone tasks complete
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MILESTONE COMPLETE STATE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   milestones:                                                               │
│   ├── M1: status = 'completed', completed_at = timestamp                   │
│   ├── M2: status = 'pending'                                               │
│   └── ...                                                                  │
│                                                                             │
│   project_state:                                                            │
│   └── current_milestone_id = 'M2' (advanced)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ /iris:validate
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VALIDATED STATE                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   milestones:                                                               │
│   └── M1: status = 'validated'                                             │
│                                                                             │
│   project_metadata:                                                         │
│   └── validation_M1 = timestamp                                            │
│                                                                             │
│   (Continue to next milestone...)                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ All milestones validated
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETED STATE                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   project_metadata:                                                         │
│   └── autopilot_completed = timestamp                                      │
│                                                                             │
│   milestones:                                                               │
│   ├── M1: status = 'validated'                                             │
│   ├── M2: status = 'validated'                                             │
│   └── ...all validated                                                     │
│                                                                             │
│   tasks:                                                                    │
│   └── ...all status = 'completed'                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status Values Reference

| Entity | Status Values | Description |
|--------|---------------|-------------|
| **Milestone** | `pending` | Not yet started |
| | `in_progress` | Tasks being executed (implicit) |
| | `completed` | All tasks done, awaiting validation |
| | `validated` | Passed validation |
| **Task** | `pending` | Not yet started |
| | `in_progress` | Currently being implemented |
| | `completed` | Implementation finished |

---

## Quick Reference: Command Summary

| Command | Primary Purpose | Key Input | Key Output |
|---------|-----------------|-----------|------------|
| `/iris:autopilot` | End-to-end autonomous development | PRD or "resume" | Working application |
| `/iris:plan` | Create adaptive sprint plan | PRD text | Populated database |
| `/iris:execute` | Implement individual tasks | Task ID (optional) | Code + completed task |
| `/iris:validate` | Verify milestone completion | Milestone ID (optional) | Validation report |
| `/iris:document` | Generate/update documentation | Flags (optional) | README, STATUS, REPORT |
| `/iris:audit` | Security analysis | Scope (optional) | Security report |

---

*Document generated for IRIS Framework v1.1*
