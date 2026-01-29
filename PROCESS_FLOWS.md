# IRIS Process Flow Documentation

This document provides visual process flows for each IRIS command, showing expected inputs, outputs, and decision points.

**Architecture Note:** IRIS uses a "prose-orchestration" approach where workflow coordination is embedded in natural language instructions within markdown files. Each `.md` command file contains instructions that Claude reads and follows directly. Modules can invoke each other inline (e.g., plan.md reads and executes research.md).

---

## Table of Contents

1. [Command Overview & Relationships](#command-overview--relationships)
2. [/iris:autopilot Flow](#irisautopilot-flow)
3. [/iris:plan Flow](#irisplan-flow)
4. [Research Module Flow](#research-module-flow)
5. [/iris:execute Flow](#irisexecute-flow)
6. [/iris:validate Flow](#irisvalidate-flow)
7. [/iris:refine Flow](#irisrefine-flow)
8. [/iris:document Flow](#irisdocument-flow)
9. [/iris:audit Flow](#irisaudit-flow)
10. [Database State Transitions](#database-state-transitions)

---

## Command Overview & Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IRIS COMMAND ECOSYSTEM                            │
│                        (Prose-Orchestration Model)                          │
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
│   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐     │
│   │  plan   │──▶│ execute │──▶│ validate │──▶│ refine │──▶│ document │     │
│   │(Phase 1)│   │(Phase 2)│   │(Phase 3) │   │(Ph 3.5)│   │(Phase 4) │     │
│   └────┬────┘   └────┬────┘   └──────────┘   └────────┘   └────┬─────┘     │
│        │             │                                         │           │
│        │             │◀────────────────────────────────────────┘           │
│        │             │     (loop per milestone until all complete)         │
│        │             ▼                                                      │
│        │         ┌────────────────────────────┐                             │
│        │         │ Final: validate → refine → │                             │
│        │         │        document (KPIs)     │                             │
│        │         └────────────────────────────┘                             │
│        │                                                                    │
│        │   PROSE-ORCHESTRATION (inline execution)                           │
│        │   ┌─────────────────────────────────────────────┐                  │
│        └──▶│  research.md ──▶ document.md --research    │                  │
│            │  (3-phase)        (TECH_DECISIONS.md)      │                  │
│            └─────────────────────────────────────────────┘                  │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                     STANDALONE COMMANDS                           │     │
│   ├───────────────────────────────────────────────────────────────────┤     │
│   │                                                                   │     │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │     │
│   │  │  /iris:refine   │  │ /iris:document  │  │   /iris:audit   │   │     │
│   │  │  (Ralph Loop)   │  │  (Standalone)   │  │   (Security)    │   │     │
│   │  └─────────────────┘  └─────────────────┘  └─────────────────┘   │     │
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
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               PHASE 3.5: RALPH-STYLE REFINEMENT LOOP                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Execute refine.md inline (prose-orchestration)                     │   │
│   │  OR invoke /iris:refine                                             │   │
│   │  (See Refine Module Flow below)                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Fixed Iterations (5-10 based on complexity)                        │   │
│   │  ├── Parallel review subagents (fresh context, read-only)          │   │
│   │  ├── Aggregate findings by severity                                │   │
│   │  ├── Single refiner subagent (fresh context, write access)         │   │
│   │  ├── Validate (backpressure, not termination gate)                 │   │
│   │  └── Repeat for all iterations (never exit early)                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: FINAL DOCUMENTATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Gate Check: Verify refine_phase_status == 'completed'             │   │
│   │  (Warns if skipped, proceeds with empty refine metrics)            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Generate Final Documentation                                       │   │
│   │  ├── Update README.md                                              │   │
│   │  ├── Update PROJECT_STATUS.md                                      │   │
│   │  ├── Generate COMPLETION_REPORT.md with KPIs                       │   │
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
| `README.md` | Auto-generated project documentation |
| `PROJECT_STATUS.md` | Human-readable progress report |
| `COMPLETION_REPORT.md` | Final KPIs and metrics |
| `.tasks/backups/` | Automatic database backups |
| Application code | Fully implemented and refined project |

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
│   │  ├── RESEARCH_MODE: dynamic (PRD-driven opportunity selection)     │   │
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
│   │  ├── research_mode: 'dynamic'                                      │   │
│   │  ├── tasks_per_milestone_min/max                                   │   │
│   │  ├── validation_frequency                                          │   │
│   │  └── enforce_tdd                                                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      COMPLEXITY CHECK         │
                    └───────────────────────────────┘
                           │              │
                    full   │              │ MICRO
                           ▼              │
┌──────────────────────────────────────┐  │
│   PHASE 2A: DYNAMIC RESEARCH         │  │
│   (Prose-Orchestration)              │  │
├──────────────────────────────────────┤  │
│                                      │  │
│  ┌────────────────────────────────┐  │  │
│  │ Read and execute research.md   │  │  │
│  │ (inline, same Claude instance) │  │  │
│  │                                │  │  │
│  │ See: Research Module Flow      │  │  │
│  │ below for detailed phases      │  │  │
│  └────────────────────────────────┘  │  │
│             │                        │  │
│             ▼                        │  │
│  ┌────────────────────────────────┐  │  │
│  │ Verify research_phase_status   │  │  │
│  │ = 'completed'                  │  │  │
│  └────────────────────────────────┘  │  │
│             │                        │  │
│             ▼                        │  │
│  ┌────────────────────────────────┐  │  │
│  │ PHASE 2B: Research Docs        │  │  │
│  │ document.md --research         │  │  │
│  │ → TECH_DECISIONS.md            │  │  │
│  └────────────────────────────────┘  │  │
│                                      │  │
└──────────────────────────────────────┘  │
                           │              │
                           │              ▼
                           │   ┌──────────────────────────┐
                           │   │ Minimal research         │
                           │   │ (OPS_TESTING only)       │
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
| `project_metadata` | ~10 configuration keys + research context |
| `milestones` | 2-5 milestones |
| `tasks` | 5-60+ tasks (based on complexity) |
| `research_opportunities` | N opportunities (dynamic based on PRD) |
| `research_executions` | N execution records (debugging) |
| `technologies` | 1-10+ technology decisions with confidence |
| `technology_sources` | Verification URLs for each technology |
| `project_state` | current_milestone_id set |

| File Output | Description |
|-------------|-------------|
| `TECH_DECISIONS.md` | Technology research summary for transparency |

---

## Research Module Flow

**Purpose:** Dynamic technology research driven by PRD analysis. Not a standalone command—invoked inline by plan.md via prose-orchestration.

**Invoked by:** `/iris:plan` (Phase 2A)
**Output:** Populated research tables, approved technology stack, TECH_DECISIONS.md

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESEARCH MODULE (research.md)                            │
│                    Invoked inline by plan.md                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 1.1: Analyze PRD for Explicit Technologies                   │   │
│   │  ├── Language specified?                                           │   │
│   │  ├── Framework specified?                                          │   │
│   │  └── Database specified?                                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 1.2: Detect Project Type                                     │   │
│   │  ├── web_app | web_api | cli_tool | library | mobile | other       │   │
│   │  ├── Has frontend? Has backend? Has database? Has auth?            │   │
│   │  └── Deployment target?                                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 1.3: Select Research Opportunities                           │   │
│   │                                                                     │   │
│   │  OPPORTUNITY CATALOG (35+ available):                              │   │
│   │  ├── Stack: STACK_LANG, STACK_FRAMEWORK_*, STACK_DATABASE, etc.   │   │
│   │  ├── Version: VERSION_LANG, VERSION_FRAMEWORK, COMPAT_MATRIX      │   │
│   │  ├── Architecture: ARCH_PATTERN, ARCH_API_DESIGN, ARCH_STATE_MGMT │   │
│   │  ├── Ops: OPS_TESTING, OPS_CI_CD, OPS_MONITORING, OPS_SECURITY    │   │
│   │  └── Custom: CUSTOM (for PRD-specific needs)                       │   │
│   │                                                                     │   │
│   │  Selection Rules:                                                   │   │
│   │  ├── Skip if PRD explicitly specifies technology                  │   │
│   │  ├── Always include OPS_TESTING                                    │   │
│   │  └── Include VERSION_* for all selected/specified tech            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 1.4-1.5: Build Context & Store                               │   │
│   │  ├── Create research_context JSON                                  │   │
│   │  ├── INSERT INTO project_metadata                                  │   │
│   │  └── INSERT INTO research_opportunities (each selected)           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: PARALLEL RESEARCH                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 2.1: Prepare Subagent Prompts                                │   │
│   │  ├── Include research_context JSON                                 │   │
│   │  ├── Include opportunity ID and research question                  │   │
│   │  └── Specify output format (RECOMMENDATION, VERSION, SOURCE, etc.) │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 2.2: Launch Parallel Research Agents                         │   │
│   │                                                                     │   │
│   │  CRITICAL: ALL agents launched in SINGLE message                   │   │
│   │                                                                     │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│   │  │  Task    │  │  Task    │  │  Task    │  │  Task    │  ...       │   │
│   │  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │            │   │
│   │  │ STACK_*  │  │ OPS_*    │  │VERSION_* │  │ ARCH_*   │            │   │
│   │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │   │
│   │       │             │             │             │                   │   │
│   │       │  subagent_type: "general-purpose"       │                   │   │
│   │       │  Tools: WebSearch, WebFetch, Read, etc. │                   │   │
│   │       │             │             │             │                   │   │
│   │       ▼             ▼             ▼             ▼                   │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │                 PARALLEL EXECUTION                          │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 2.3-2.4: Collect & Store Results                             │   │
│   │  ├── Parse: RECOMMENDATION, VERSION, SOURCE, CONFIDENCE           │   │
│   │  ├── INSERT INTO research_executions                               │   │
│   │  └── UPDATE research_opportunities SET status = 'completed'       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: REVIEW & RECONCILIATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 3.1: Aggregate Results                                       │   │
│   │                                                                     │   │
│   │  ┌───────────────────┬──────────────┬─────────┬────────────┐        │   │
│   │  │ Opportunity       │ Recommendation│ Version │ Confidence │        │   │
│   │  ├───────────────────┼──────────────┼─────────┼────────────┤        │   │
│   │  │ STACK_FRAMEWORK   │ FastAPI      │ 0.109.0 │ HIGH       │        │   │
│   │  │ OPS_TESTING       │ pytest       │ 8.0.0   │ HIGH       │        │   │
│   │  │ ...               │ ...          │ ...     │ ...        │        │   │
│   │  └───────────────────┴──────────────┴─────────┴────────────┘        │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 3.2: Check for Issues                                        │   │
│   │  ├── Coherence: Do all technologies work together?                 │   │
│   │  ├── Conflicts: Contradictory assumptions? Version mismatches?     │   │
│   │  ├── Gaps: Missing critical decisions?                             │   │
│   │  └── Confidence: Any LOW confidence needing re-research?           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│              ┌─────────────────────┴─────────────────────┐                  │
│              │                                           │                  │
│         issues found                               no issues                │
│              │                                           │                  │
│              ▼                                           │                  │
│   ┌──────────────────────────────┐                       │                  │
│   │  Step 3.3: Resolve Issues    │                       │                  │
│   │  ├── Minor: Planner judgment │                       │                  │
│   │  ├── Gaps: Follow-up research│                       │                  │
│   │  ├── Conflicts: Best fit     │                       │                  │
│   │  └── Low conf: Re-research   │                       │                  │
│   └──────────────────────────────┘                       │                  │
│              │                                           │                  │
│              └───────────────────┬───────────────────────┘                  │
│                                  │                                          │
│                                  ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step 3.4-3.5: Commit Stack & Update Status                        │   │
│   │  ├── INSERT INTO technologies (with confidence, alternatives)      │   │
│   │  ├── INSERT INTO technology_sources (verification URLs)           │   │
│   │  └── UPDATE project_metadata SET research_phase_status='completed'│   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     RESEARCH COMPLETE         │
                    │                               │
                    │  Output: Research Summary     │
                    │  Control returns to plan.md   │
                    └───────────────────────────────┘
```

### Research Outputs

| Database Table | Records Created |
|----------------|-----------------|
| `project_metadata` | Research context keys |
| `research_opportunities` | N opportunities selected from catalog |
| `research_executions` | N execution records (for debugging) |
| `technologies` | Approved stack with confidence levels |
| `technology_sources` | Verification URLs |

| File Output | Description |
|-------------|-------------|
| `TECH_DECISIONS.md` | Human-readable research summary (via document.md --research) |

### Research Opportunity Categories

| Category | Examples | When Selected |
|----------|----------|---------------|
| **Stack** | STACK_LANG, STACK_FRAMEWORK_API, STACK_DATABASE | PRD doesn't specify |
| **Version** | VERSION_LANG, VERSION_FRAMEWORK, COMPAT_MATRIX | Always for selected tech |
| **Architecture** | ARCH_PATTERN, ARCH_API_DESIGN, ARCH_STATE_MGMT | Non-trivial projects |
| **Ops** | OPS_TESTING, OPS_CI_CD, OPS_MONITORING | OPS_TESTING always; others as needed |
| **Custom** | CUSTOM | PRD has unique needs |

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
│   │  │   ┌─────────────┐     ┌─────────────┐    ┌─────────────┐     │ │     │
│   │  │   │    RED      │───▶│   GREEN     │───▶│  REFACTOR   │     │ │     │
│   │  │   │             │     │             │    │             │     │ │     │
│   │  │   │ Write tests │     │ Write code  │    │ Clean up    │     │ │     │
│   │  │   │ (failing)   │     │ (pass tests)│    │ (tests pass)│     │ │     │
│   │  │   └─────────────┘     └─────────────┘    └─────────────┘     │ │     │
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

**Input:** Optional flags: `--standalone`, `--research`, `--milestone <id>`, `--final`
**Output:** README.md, PROJECT_STATUS.md, TECH_DECISIONS.md (research), COMPLETION_REPORT.md (final)

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
| `TECH_DECISIONS.md` | `--research` only | Technology research summary with rationale |
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

## /iris:refine Flow

**Purpose:** Ralph Wiggum-style iterative refinement to improve implementation toward PRD alignment.

**Invocation:**
- **Standalone:** `/iris:refine` - Run refinement on an existing project
- **Via Autopilot:** Executed inline as Phase 3.5 of `/iris:autopilot`

**Input:** Existing project with completed tasks in database
**Output:** Improved codebase with refine_phase_status='completed'

**Philosophy:** The Ralph Wiggum technique - fixed iterations with fresh context for progressive improvement.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REFINE MODULE FLOW                                  │
│                    (Ralph Wiggum-Style Iteration)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 0: INITIALIZATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Load Configuration from Database                                 │     │
│   │  ├── Get complexity level                                         │     │
│   │  ├── Determine max_iterations (minimum 5)                         │     │
│   │  ├── Determine reviewer count (2-6 by complexity)                 │     │
│   │  └── Get review focus areas                                       │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                   │                                         │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Load Context                                                     │     │
│   │  ├── Retrieve PRD content (for refiner anchoring)                 │     │
│   │  ├── Load tech stack constraints                                  │     │
│   │  └── Initialize refine state in database                          │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 1: ITERATION LOOP (Fixed Count - Never Exit Early)       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   for iteration in range(1, max_iterations + 1):                            │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 1A: REVIEW (Parallel Fresh Subagents)                       │   │
│   │                                                                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│   │  │   Gaps      │  │  Quality    │  │ Integration │  │Edge Cases │  │   │
│   │  │  Reviewer   │  │  Reviewer   │  │  Reviewer   │  │ Reviewer  │  │   │
│   │  │  (fresh)    │  │  (fresh)    │  │  (fresh)    │  │ (fresh)   │  │   │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘  │   │
│   │         │                │                │               │        │   │
│   │         └────────────────┴────────────────┴───────────────┘        │   │
│   │                                   │                                 │   │
│   │                                   ▼                                 │   │
│   │                        [Findings JSON]                              │   │
│   │                                                                     │   │
│   │  Note: Reviewers are READ-ONLY (prompt-constrained)                 │   │
│   │  Focus areas scale with complexity (2-6 reviewers)                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 1B: AGGREGATE                                                │   │
│   │                                                                     │   │
│   │  ├── Combine findings from all reviewers                           │   │
│   │  ├── Prioritize by: Severity → PRD alignment → File locality       │   │
│   │  └── Store findings in database                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 1C: REFINE (Single Fresh Subagent)                          │   │
│   │                                                                     │   │
│   │                  ┌─────────────────────────┐                        │   │
│   │                  │      Refiner Agent      │                        │   │
│   │                  │        (fresh)          │                        │   │
│   │                  │                         │                        │   │
│   │  Receives:       │  ┌─────────────────┐    │                        │   │
│   │  • PRD (full)    │  │  Improve code   │    │                        │   │
│   │  • Tech stack    │  │  Run tests      │    │                        │   │
│   │  • Findings      │  │  Commit changes │    │                        │   │
│   │                  │  └─────────────────┘    │                        │   │
│   │                  └─────────────────────────┘                        │   │
│   │                                                                     │   │
│   │  Key: "IMPROVE, not just fix" - enhance toward PRD intent           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 1D: VALIDATE (Backpressure)                                  │   │
│   │                                                                     │   │
│   │  ├── Run test suite                                                │   │
│   │  ├── Record pass/fail                                              │   │
│   │  └── Continue regardless (validation is backpressure, not a gate)  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PHASE 1E: RECORD & CONTINUE                                        │   │
│   │                                                                     │   │
│   │  ├── Update iteration counter in database                          │   │
│   │  ├── Output iteration summary                                      │   │
│   │  └── Continue to next iteration (NEVER exit early)                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   │                                         │
│                           (loop back to 1A)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: COMPLETION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  After ALL iterations complete:                                   │     │
│   │  ├── Run final validation (tests, lint, build)                    │     │
│   │  ├── Generate refine summary report                               │     │
│   │  ├── Update refine_phase_status = 'completed'                     │     │
│   │  └── Return control to autopilot.md                               │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Configuration by Complexity

| Complexity | Max Iterations | Reviewers | Focus Areas |
|------------|----------------|-----------|-------------|
| MICRO | 5 | 2 | gaps, quality |
| SMALL | 5 | 3 | gaps, quality, edge_cases |
| MEDIUM | 6 | 4 | gaps, quality, integration, edge_cases |
| LARGE | 8 | 5 | gaps, quality, integration, edge_cases, security |
| ENTERPRISE | 10 | 6 | gaps, quality, integration, edge_cases, security, performance |

### Key Ralph Wiggum Principles

| Principle | Implementation |
|-----------|----------------|
| Fresh Context | Each iteration uses new subagents without accumulated baggage |
| Progress in Files | Improvements committed to git; state in database |
| Fixed Iterations | Loop runs exactly max_iterations times (minimum 5) |
| Improve, Not Fix | Focus on enhancement toward PRD intent, not just bug repair |
| PRD Anchoring | Refiner receives full PRD each iteration |
| Backpressure | Validation provides feedback but doesn't terminate loop |

### Database Tables Used

| Table | Purpose |
|-------|---------|
| `refine_iterations` | Tracks each iteration's status, findings count, improvements |
| `refine_findings` | Stores findings from review agents |
| `refine_improvements` | Records improvements made by refiner |
| `project_state` | Tracks refine_phase_status, current_iteration |
| `project_metadata` | Stores PRD content, timestamps |

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
| `/iris:plan` | Create adaptive sprint plan | PRD text | Populated database + TECH_DECISIONS.md |
| `research.md` | Dynamic technology research | Invoked inline by plan.md | technologies table, research_* tables |
| `/iris:execute` | Implement individual tasks | Task ID (optional) | Code + completed task |
| `/iris:validate` | Verify milestone completion | Milestone ID (optional) | Validation report |
| `/iris:document` | Generate/update documentation | Flags (optional) | README, STATUS, TECH_DECISIONS, REPORT |
| `/iris:audit` | Security analysis | Scope (optional) | Security report |

### Document Command Flags

| Flag | Purpose |
|------|---------|
| `--standalone` | Analyze existing project without IRIS database |
| `--research` | Generate TECH_DECISIONS.md from research results |
| `--milestone <id>` | Update docs for specific milestone |
| `--final` | Generate COMPLETION_REPORT.md with KPIs |

---

*Document generated for IRIS Framework v2.0 (Prose-Orchestration Architecture)*
