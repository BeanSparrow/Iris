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
# Find project root by looking for .claude directory
PROJECT_ROOT=$(pwd)
while [[ "$PROJECT_ROOT" != "/" ]] && [[ ! -d "$PROJECT_ROOT/.claude" ]]; do
    PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
done

# Find IRIS directory relative to .claude
IRIS_DIR=""
if [[ -d "$PROJECT_ROOT/.claude/commands/iris" ]]; then
    IRIS_DIR="$PROJECT_ROOT/.claude/commands/iris"
elif [[ -d "$HOME/.claude/commands/iris" ]]; then
    IRIS_DIR="$HOME/.claude/commands/iris"
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
print(f'MILESTONE_MIN={config.tasks_per_milestone[0]}')
print(f'MILESTONE_MAX={config.tasks_per_milestone[1]}')
print(f'ENFORCE_TDD={str(config.enforce_tdd).lower()}')
print(f'VALIDATION_FREQ={config.validation_frequency}')
" > /tmp/adaptive_config.env

# Source the configuration
source /tmp/adaptive_config.env

echo "✅ Project Analysis Complete:"
echo "   Complexity: $COMPLEXITY"
echo "   Type: $PROJECT_TYPE"
echo "   Max MVP Features: $MAX_FEATURES"
echo "   Tasks per Milestone: $MILESTONE_MIN-$MILESTONE_MAX"
echo "   TDD Required: $ENFORCE_TDD"
echo "   Research: Dynamic (based on PRD analysis)"
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

# Read PRD content from temp file (created earlier in this script)
with open('/tmp/prd_analysis.txt', 'r') as f:
    prd_content = f.read()

config_items = [
    ('analysis_timestamp', datetime.now().isoformat()),
    ('project_complexity', '$COMPLEXITY'),
    ('project_type', '$PROJECT_TYPE'),
    ('max_mvp_features', '$MAX_FEATURES'),
    ('tasks_per_milestone_min', '$MILESTONE_MIN'),
    ('tasks_per_milestone_max', '$MILESTONE_MAX'),
    ('validation_frequency', '$VALIDATION_FREQ'),
    ('enforce_tdd', '$ENFORCE_TDD'),
    ('research_mode', 'dynamic'),  # Research opportunities selected dynamically
    ('scaling_rationale', f'$COMPLEXITY complexity $PROJECT_TYPE project with adaptive scaling'),
    ('prd_content', prd_content)  # Store PRD for refine phase to access
]

db = DatabaseManager()
with db.get_connection() as conn:
    for key, value in config_items:
        conn.execute('INSERT OR REPLACE INTO project_metadata (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()

print('✅ Configuration stored in database (including PRD content)')
"
```

### Phase 2A — Technology Research

**CRITICAL INSTRUCTION:** Now perform technology research following the research protocol.

The research module uses a three-phase approach:
1. **Foundation** - Analyze PRD for explicit tech mentions, select research opportunities
2. **Parallel Research** - Launch subagents for each selected opportunity
3. **Review & Reconciliation** - Verify coherence, resolve conflicts, commit to database

**Research Execution (Prose-Orchestration):**

**CRITICAL:** Use the Read tool to read the file at `$IRIS_DIR/research.md`, then execute its instructions inline as part of this planning session. This is prose-orchestration: you (Claude) read the .md file and follow its instructions directly—there is no subprocess or separate invocation. The PRD content from `$ARGUMENTS` is already in your context.

The research process will:

1. Analyze the PRD (`$ARGUMENTS`) for explicit technology choices
2. Detect project type and constraints
3. Select applicable research opportunities from the catalog based on what's NOT specified
4. Build a research context with all known information
5. Launch parallel `general-purpose` subagents for each selected opportunity
6. Each subagent uses WebSearch and WebFetch to find current, verified information
7. Review all results for coherence and conflicts
8. Commit the approved technology stack to the database

**For MICRO/SCRIPT projects with minimal complexity:**

If complexity analysis indicates a very simple project where research would be overhead:

```bash
# For MICRO projects - minimal research
echo "⚡ Simple project - Applying minimal research..."

python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Insert minimal research opportunity
    conn.execute('''
        INSERT INTO research_opportunities (id, category, name, research_question, status)
        VALUES ('OPS_TESTING', 'ops', 'Testing Strategy', 'What testing approach for this project?', 'pending')
    ''')
    conn.commit()
    print('✅ Minimal research opportunity queued')
"
```

Even MICRO projects should verify testing approach and language version.

**For all other projects:**

Execute the full research protocol:

1. **Phase 1 (Foundation):** Analyze PRD, select opportunities, build context
2. **Phase 2 (Parallel Research):** Launch subagents with `subagent_type: "general-purpose"`
3. **Phase 3 (Review):** Check coherence, resolve issues, commit stack

**IMPORTANT:** The research module stores results directly to the database:
- `research_opportunities` - Tracks what was researched
- `research_executions` - Records subagent execution history
- `technologies` - Stores the approved technology stack
- `technology_sources` - Stores verification URLs

**After research completes, verify the technology stack:**

```bash
# Verify research results
echo "🔍 Verifying technology stack..."

python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Check research status - MUST be 'completed'
    status = conn.execute(\"SELECT value FROM project_metadata WHERE key = 'research_phase_status'\").fetchone()
    status_value = status['value'] if status else 'NOT STARTED'
    print(f'Research Status: {status_value}')

    if status_value != 'completed':
        print('❌ ERROR: Research phase not completed. Review research.md execution.')
        sys.exit(1)

    # List approved technologies
    techs = conn.execute('SELECT name, category, version, confidence FROM technologies').fetchall()
    print(f'Technologies Approved: {len(techs)}')
    for t in techs:
        print(f'   {t[\"category\"]}: {t[\"name\"]} {t[\"version\"]} ({t[\"confidence\"]})')

    # Check for any low confidence items
    low_conf = conn.execute(\"SELECT COUNT(*) as c FROM technologies WHERE confidence = 'LOW'\").fetchone()
    if low_conf['c'] > 0:
        print(f'⚠️  {low_conf[\"c\"]} technologies with LOW confidence - review recommended')

    print('✅ Research verification passed')
"
```

### Phase 2B — Research Documentation

**Generate research documentation for transparency and debugging:**

Use the Read tool to read `$IRIS_DIR/document.md` and invoke it with the `--research` flag to generate technology decision documentation.

This creates a `TECH_DECISIONS.md` file that documents:
- All research opportunities that were analyzed
- Technology recommendations with rationale
- Confidence levels and source URLs
- Compatibility notes

**Continue to Phase 3A (Milestone Creation) after research documentation completes.**

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

### 🚀 Dynamic Research Execution
- **Research Strategy:** Dynamic opportunity selection based on PRD analysis
- **Opportunities Researched:** [OPPORTUNITY_COUNT] (selected based on PRD gaps)
- **High Confidence:** [HIGH_CONF_COUNT] technologies verified from official sources
- **Parallel Execution:** [AGENT_COUNT] subagents launched simultaneously

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
  - **technologies table** - [TECH_COUNT] researched technologies with confidence levels
  - **research_opportunities table** - [OPPORTUNITY_COUNT] opportunities tracked
  - **research_executions table** - Subagent execution history for debugging
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

### ⚡ Research Quality
- **Source Verification:** Technologies verified from official documentation
- **Compatibility Checked:** Stack coherence verified in reconciliation phase
- **Confidence Tracking:** Each technology has HIGH/MEDIUM/LOW confidence rating
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