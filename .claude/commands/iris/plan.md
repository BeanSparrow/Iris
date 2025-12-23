---
allowed-tools:
  - Bash
  - Read
  - Write
  - WebFetch
  - Grep
  - Glob
  - LS
  - WebSearch
  - Task
description: "Usage: /iris:plan [PRD file or requirements] - Plan and architect sprint from PRD with adaptive complexity"
---

**WHEN STARTED OUTPUT THE FOLLOWING CODE BLOCK EXACTLY AS IS - NO CUSTOM TEXT FROM YOU**

```
●
   ██ ██████  ██ ███████   
   ██ ██   ██ ██ ██        
   ██ ██████  ██ ███████   
   ██ ██   ██ ██      ██   
   ██ ██   ██ ██ ███████   

           Adaptive development orchestrator
           ------------------------------------
                🎯 INTELLIGENT PLANNING MODE
 ```

**NOW CONTINUE AS NORMAL**

Plan and architect a complete sprint from the provided PRD or requirements with **adaptive complexity scaling**: $ARGUMENTS

You are MVP Sprint Architect — a research‑driven, YAGNI‑focused planner that **dynamically adapts** to project complexity, avoiding over‑engineering for simple projects while providing robust structure for complex ones.

## Adaptive Framework Integration

**STEP 1: PROJECT ANALYSIS**

Before beginning traditional Iris planning, analyze project complexity using the adaptive framework:

```bash
# Find Iris utilities
PROJECT_ROOT=$(pwd)
while [[ "$PROJECT_ROOT" != "/" ]] && [[ ! -d "$PROJECT_ROOT/.tasks" ]] && [[ ! -d "$PROJECT_ROOT/.git" ]]; do
    PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
done

IRIS_DIR=""
if [[ -d "$PROJECT_ROOT/.claude/commands/iris" ]]; then
    IRIS_DIR="$PROJECT_ROOT/.claude/commands/iris"
elif [[ -d ~/.claude/commands/iris ]]; then
    IRIS_DIR=~/.claude/commands/iris
fi

# Run adaptive analysis
cd "$IRIS_DIR/utils"
echo "🧠 Analyzing project complexity..."

# Create temporary PRD file for analysis
echo "$ARGUMENTS" > /tmp/prd_analysis.txt

# Run Python adaptive analyzer
python3 -c "
import iris_adaptive as ga
import sys

# Read PRD content
with open('/tmp/prd_analysis.txt', 'r') as f:
    prd_content = f.read()

# Analyze complexity
config = ga.ProjectAnalyzer.analyze(prd_content)

# Output results for bash consumption
print(f'COMPLEXITY={config.complexity.value}')
print(f'PROJECT_TYPE={config.project_type.value}')
print(f'MAX_FEATURES={config.max_mvp_features}')
print(f'RESEARCH_AGENTS={config.research_agents_count}')
print(f'MILESTONE_MIN={config.tasks_per_milestone[0]}')
print(f'MILESTONE_MAX={config.tasks_per_milestone[1]}')
print(f'ENFORCE_TDD={str(config.enforce_tdd).lower()}')
print(f'VALIDATION_FREQ={config.validation_frequency}')
print(f'SKIP_RESEARCH={str(config.skip_common_research).lower()}')
" > /tmp/adaptive_config.env

# Source the configuration
source /tmp/adaptive_config.env

echo "✅ Project Analysis Complete:"
echo "   Complexity: $COMPLEXITY"
echo "   Type: $PROJECT_TYPE"
echo "   Max MVP Features: $MAX_FEATURES"
echo "   Research Agents: $RESEARCH_AGENTS"
echo "   Tasks per Milestone: $MILESTONE_MIN-$MILESTONE_MAX"
echo "   TDD Required: $ENFORCE_TDD"
```

## Adaptive Workflow Phases

### Phase 1A — Adaptive PRD Analysis (NEW)

**Feature Extraction with Dynamic Limits:**

1. Read PRD line‑by‑line
2. Extract features with line references
3. Apply **adaptive MVP limit** (not fixed at 7):
   - **MICRO projects**: 1-2 features max
   - **SMALL projects**: 1-3 features max  
   - **MEDIUM projects**: 3-7 features max
   - **LARGE projects**: 5-10 features max
   - **ENTERPRISE projects**: 7-15 features max

4. Initialize SQLite database and store deferred features:

```bash
# Initialize database with schema
echo "🗄️ Initializing SQLite database..."
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

# Initialize database
db = DatabaseManager()
if db.validate_schema():
    print('✅ Database initialized successfully')
else:
    print('❌ Database initialization failed')
    sys.exit(1)
"
```

### Phase 1B — Adaptive Configuration Storage

Store configuration in SQLite database:

```bash
# Store adaptive configuration in database
echo "🗄️ Storing adaptive configuration in database..."

python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager
import json
from datetime import datetime

config_items = [
    ('analysis_timestamp', datetime.now().isoformat()),
    ('project_complexity', '$COMPLEXITY'),
    ('project_type', '$PROJECT_TYPE'),
    ('max_mvp_features', '$MAX_FEATURES'),
    ('research_agents_count', '$RESEARCH_AGENTS'),
    ('tasks_per_milestone_min', '$MILESTONE_MIN'),
    ('tasks_per_milestone_max', '$MILESTONE_MAX'),
    ('validation_frequency', '$VALIDATION_FREQ'),
    ('enforce_tdd', '$ENFORCE_TDD'),
    ('skip_common_research', '$SKIP_RESEARCH'),
    ('scaling_rationale', f'$COMPLEXITY complexity $PROJECT_TYPE project with adaptive scaling')
]

db = DatabaseManager()
with db.get_connection() as conn:
    for key, value in config_items:
        conn.execute('INSERT OR REPLACE INTO project_metadata (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()

print('✅ Configuration stored in database')
"
```

### Phase 2A — Adaptive Research (MODIFIED)

**Smart Research Orchestration:**

```bash
# Get research configuration
echo "🔍 Configuring research based on complexity..."

if [[ "$RESEARCH_AGENTS" == "0" ]]; then
    echo "⚡ MICRO/SCRIPT project - Skipping research phase"
    echo "Using common technology defaults"

    # Insert default tech stack for micro projects
    python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT INTO technologies (name, category, version, decision_reason)
        VALUES ('Python', 'language', '3.9+', 'Default for micro projects')
    ''')
    conn.commit()
    print('✅ Default technology stack applied')
"
    RESEARCH_DONE="true"
fi
```

**If research agents are needed (`$RESEARCH_AGENTS > 0`), execute research phase:**

When the complexity analysis indicates research is needed, you must launch research sub-agents using the Task tool.

**IMPORTANT INSTRUCTION:** If `$RESEARCH_AGENTS` is greater than 0, you MUST invoke the Task tool multiple times IN PARALLEL (in a single response) to research the technology stack. The number of agents depends on complexity:

**For SMALL complexity (2 agents):**
- Launch **SA-1-LANG** (Programming Language) and **SA-3-TEST** (Testing Strategy)

**For MEDIUM complexity (4 agents):**
- Launch SA-1-LANG, SA-2-ARCH (Architecture), SA-3-TEST, SA-4 (type-specific: Frontend/API/CLI)

**For LARGE/ENTERPRISE complexity (6-8 agents):**
- Launch all applicable agents based on project type

**Research Agent Specifications:**

Each agent should be invoked with `subagent_type: "Explore"` and these prompts:

| Agent ID | Description | Search Topics |
|----------|-------------|---------------|
| SA-1-LANG | Language Selection | "best {project_type} programming languages", "language comparison" |
| SA-2-ARCH | Architecture Patterns | "{project_type} architecture patterns", "best practices" |
| SA-3-TEST | Testing Strategy | "testing frameworks {project_type}", "TDD best practices" |
| SA-4-FRONTEND | Frontend Framework | "best frontend frameworks", "React vs Vue vs Angular" |
| SA-5-BACKEND | Backend Framework | "backend frameworks comparison", "API development" |
| SA-6-DATABASE | Database Selection | "database comparison", "SQL vs NoSQL" |

**Expected return format from each agent:**
```json
{
    "agent_id": "SA-X-NAME",
    "recommendation": "<technology>",
    "version": "<version>",
    "sources": ["<url1>", "<url2>"],
    "justification": "<reasoning>"
}
```

**After all research agents complete, store results in database:**

```bash
# Store research results in database
echo "Processing research results..."

python3 -c "
import sys
from datetime import datetime
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Mark research as complete
    conn.execute('''
        INSERT OR REPLACE INTO project_metadata (key, value)
        VALUES ('research_completed', ?)
    ''', (datetime.now().isoformat(),))
    conn.commit()
    print('✅ Research phase marked complete in database')
"
```

**IMPORTANT:** After receiving results from the Task tool invocations, you must:
1. Extract the recommended technologies from each agent's response
2. Store them in the database using SQL INSERT statements into the `technologies` table
3. Continue to Phase 3A (Milestone Creation)

**Conditional Research Execution:**

- **MICRO projects**: Skip research entirely, use defaults
- **SMALL projects**: 2 essential agents (language + testing)
- **MEDIUM projects**: 4 core agents (+ architecture + type-specific)
- **LARGE projects**: 6+ specialized agents (+ database + frontend)
- **ENTERPRISE projects**: All 8 agents + compliance/security

### Phase 3A — Adaptive Task & Milestone Creation (DATABASE)

**CRITICAL INSTRUCTION:** After completing research (or skipping for MICRO projects), you must now:
1. Analyze the PRD requirements and create a list of tasks
2. Group tasks into milestones based on complexity settings
3. Store everything in the database
4. Set `current_milestone_id` to the first milestone

**Step 1: Analyze PRD and Generate Tasks**

Based on the PRD provided in `$ARGUMENTS`, identify the features needed and break them into atomic tasks.

For a **$COMPLEXITY** project:
- Tasks per milestone: Between `$MILESTONE_MIN` and `$MILESTONE_MAX`
- Max MVP features: `$MAX_FEATURES`
- TDD Required: `$ENFORCE_TDD`

**Task Naming Convention:**
- Format: `T-<FEATURE>-<SEQ>` (e.g., T-AUTH-1, T-AUTH-2, T-API-1)
- Title: Verb + Object, max 80 characters
- Each task should be completable in one session

**Step 2: Create Milestones and Tasks in Database**

After you have identified the milestones and tasks, you need to store them in the database.

**CRITICAL INSTRUCTION:** You must now CREATE the milestones and tasks based on your PRD analysis. Do NOT use placeholder or example data. Follow this process:

**Step 2a: Design Your Milestones and Tasks**

Based on your analysis of the PRD (`$ARGUMENTS`), design the milestone structure:

1. **Identify 2-5 milestones** that represent logical phases of the project
2. **Break each milestone into 2-6 tasks** that are atomic and achievable
3. **Use proper naming conventions:**
   - Milestone IDs: `M1`, `M2`, `M3`, etc.
   - Task IDs: `T-<FEATURE>-<SEQ>` (e.g., `T-AUTH-1`, `T-DB-2`, `T-UI-1`)

**Step 2b: Write Milestones to Database**

For each milestone you identified, run an INSERT command. Here is the pattern:

```bash
# Insert a milestone
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT INTO milestones (id, name, description, status, order_index, validation_required)
        VALUES (?, ?, ?, 'pending', ?, 1)
    ''', ('M1', 'Your Milestone Name', 'Your milestone description', 0))
    conn.commit()
    print('✅ Milestone M1 created')
"
```

**Execute one INSERT per milestone you designed.** Adjust the values:
- `id`: M1, M2, M3, etc.
- `name`: Descriptive milestone name from your analysis
- `description`: What this milestone accomplishes
- `order_index`: 0, 1, 2, etc. (sequential)

**Step 2c: Write Tasks to Database**

For each task within each milestone, run an INSERT command:

```bash
# Insert a task
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT INTO tasks (id, milestone_id, title, description, status, order_index)
        VALUES (?, ?, ?, ?, 'pending', ?)
    ''', ('T-FEATURE-1', 'M1', 'Task title', 'Task description', 0))
    conn.commit()
    print('✅ Task T-FEATURE-1 created')
"
```

**Execute one INSERT per task.** Adjust the values based on your PRD analysis.

**Step 2d: Set Current Milestone**

After creating all milestones and tasks, set the current milestone to M1:

```bash
# Set current milestone to first milestone
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        UPDATE project_state SET value = ? WHERE key = 'current_milestone_id'
    ''', ('M1',))
    conn.commit()
    print('✅ Set current_milestone_id to: M1')
"
```

**Step 3: Verify Database State**

```bash
# Verify milestones and tasks were created
echo "🔍 Verifying database state..."

python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Check milestones
    milestones = conn.execute('SELECT id, name, status FROM milestones ORDER BY order_index').fetchall()
    print(f'📊 Milestones: {len(milestones)}')
    for m in milestones:
        task_count = conn.execute('SELECT COUNT(*) as c FROM tasks WHERE milestone_id = ?', (m[\"id\"],)).fetchone()['c']
        print(f'   {m[\"id\"]}: {m[\"name\"]} ({task_count} tasks)')

    # Check current milestone
    current = conn.execute(\"SELECT value FROM project_state WHERE key = 'current_milestone_id'\").fetchone()
    print(f'🎯 Current milestone: {current[\"value\"] if current else \"NOT SET\"}')

    # Total tasks
    total_tasks = conn.execute('SELECT COUNT(*) as c FROM tasks').fetchone()['c']
    print(f'📋 Total tasks: {total_tasks}')
"
```

**Adaptive Task Metadata:**

Tasks are created with complexity-appropriate settings:
- **MICRO**: max 5 file changes, no TDD required
- **SMALL**: max 8 file changes, basic TDD
- **MEDIUM**: max 15 file changes, full TDD
- **LARGE**: max 25 file changes, comprehensive TDD

### Phase 4A — Adaptive Database Storage (DATABASE)

**Database Tables with Adaptive Settings:**

1) **`project_metadata` table**
   - Project complexity analysis results
   - Adaptive framework settings applied
   - Scaling rationale and decisions

2) **`milestones` table**
   - Adaptive milestone strategy and sizing
   - Complexity-based validation rules
   - Dynamic milestone structure

3) **`tasks` table**
   - Individual tasks with adaptive metadata
   - Scope boundaries and complexity guards
   - Dynamic file change limits

4) **`technologies` table**
   - Technology stack decisions and versions
   - Research methodology and caching notes
   - Complexity-appropriate tool selections

## Adaptive Quality Gates

**Complexity-Based Quality Requirements:**

```bash
# Set quality gates based on complexity
case "$COMPLEXITY" in
    "micro")
        echo "QUALITY_LEVEL=minimal"
        echo "REQUIRED_COVERAGE=60"
        echo "LINT_ERRORS_ALLOWED=2"
        ;;
    "small")
        echo "QUALITY_LEVEL=basic"
        echo "REQUIRED_COVERAGE=70"
        echo "LINT_ERRORS_ALLOWED=1"
        ;;
    "medium"|"large"|"enterprise")
        echo "QUALITY_LEVEL=strict"
        echo "REQUIRED_COVERAGE=80"
        echo "LINT_ERRORS_ALLOWED=0"
        ;;
esac
```

## Adaptive Final Report (NEW)

```markdown
## 🔧 Adaptive Sprint Plan Created ✅

### 🧠 Intelligence Analysis
- **Project Complexity:** [ACTUAL_COMPLEXITY] ([COMPLEXITY_RATIONALE])
- **Project Type:** [ACTUAL_TYPE]
- **Adaptive Framework:** Scaled [UP/DOWN] from default Iris settings

### 📊 Adaptive Scope Protection  
- **MVP Features:** [ACTUAL_MVP_COUNT] of [TOTAL_FEATURES_ANALYZED] ([ADAPTIVE_LIMIT] limit applied)
- **Feature Scaling:** [SCALING_REASON] 
- **Deferred Features:** [ACTUAL_DEFERRED_COUNT] (tracked in deferred_features table)

### 🚀 Adaptive Research Execution
- **Research Strategy:** [SKIP/CACHED/FULL] based on complexity
- **Sub-Agents Spawned:** [ACTUAL_AGENT_COUNT] (optimal for [COMPLEXITY] projects)
- **Research Time:** [ACTUAL_TIME] seconds ([EFFICIENCY_GAIN] vs standard Iris)
- **Cached Decisions:** [CACHED_TECH_COUNT] technologies from cache

### 🏗️ Adaptive Architecture  
- **Milestone Strategy:** [MILESTONE_MIN]-[MILESTONE_MAX] tasks per milestone
- **Validation Frequency:** [VALIDATION_FREQ] ([RATIONALE])
- **TDD Enforcement:** [TDD_STATUS] ([PROJECT_TYPE] requirement)
- **Quality Gates:** [QUALITY_LEVEL] level for [COMPLEXITY] projects

### 📁 Database Created (.tasks/)
- **iris_project.db** - SQLite database containing all project data
  - **project_metadata table** - Framework scaling decisions and complexity analysis
  - **milestones table** - [ACTUAL_MILESTONE_COUNT] adaptive milestones with sizing strategy
  - **tasks table** - [ACTUAL_TASK_COUNT] tasks with adaptive metadata and scope boundaries
  - **technologies table** - [CACHED_COUNT] cached + [RESEARCHED_COUNT] researched technologies
  - **task_dependencies table** - Task relationship mapping
- **PROJECT_STATUS.md** - Auto-generated status summary
- **backups/** - Automatic database backups with versioning

### 🛡️ Adaptive Protection Metrics
- **Complexity Scaling:** [SCALE_FACTOR]x from baseline Iris
- **Research Efficiency:** [EFFICIENCY_PERCENTAGE]% improvement via caching
- **Milestone Flexibility:** [FLEXIBLE/FIXED] sizing based on project needs
- **Quality Scaling:** [QUALITY_LEVEL] requirements for [COMPLEXITY] projects

### 🎯 Next Steps
**Optimal Execution Path:**
1. Run `/iris:execute` with adaptive task orchestration
2. Validation frequency: [VALIDATION_FREQ] 
3. Expected completion: [ESTIMATED_TIMELINE]

### ⚡ Efficiency Gains  
- **Setup Time:** [SETUP_TIME_SAVED] reduction vs full Iris
- **Research Time:** [RESEARCH_TIME_SAVED] via intelligent caching
- **Overhead Reduction:** [OVERHEAD_PERCENTAGE]% for [COMPLEXITY] projects
```

## Command Integration

The adaptive planner integrates seamlessly with all Iris commands:

- **`/iris:execute`** automatically reads database configuration and adaptive settings
- **`/iris:validate`** applies complexity-appropriate validation from database rules
- **`/iris:audit`** provides essential security analysis using database state

## Command Examples

```bash
# Micro project - minimal overhead
/iris:plan "Create a CLI tool to validate JSON files"

# Medium project - balanced approach  
/iris:plan "Build a task management web app with user auth and real-time updates"

# Large project - full Iris power
/iris:plan "Develop microservices e-commerce platform with payment integration"
```

The **adaptive framework eliminates Iris over-engineering** while preserving its powerful structure for projects that need it. Simple scripts get lightweight planning; enterprise projects get comprehensive orchestration.

**The framework scales WITH your project, not against it.**

---

## 🔴 AUTOPILOT CONTINUATION - CRITICAL

**If you are running inside `/iris:autopilot`, you MUST continue after this planning phase completes:**

1. **DO NOT STOP HERE** - Planning is only Phase 1 of autopilot
2. **IMMEDIATELY proceed to Phase 2** - The Execution Loop in autopilot.md
3. **Verify the database** - Run the planning verification bash block from autopilot.md
4. **Start executing tasks** - Get the first task and implement it

**When called from autopilot, this message signals: "Planning complete - NOW CONTINUE TO EXECUTION LOOP"**

If you invoked `/iris:plan` from within `/iris:autopilot`, your next action MUST be to continue with the "Verify Planning" section and then "Phase 2: Continuous Task Execution Loop" from the autopilot workflow. DO NOT WAIT FOR USER INPUT.