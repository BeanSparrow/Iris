---
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - LS
  - WebSearch
  - WebFetch
  - Task
  - MultiEdit
description: "Usage: /iris:autopilot <PRD> - Autonomous development from PRD to completion"
---

Execute autonomous development from PRD to completion: $ARGUMENTS

You are **IRIS Autopilot** — the autonomous development orchestrator that runs continuously from project requirements to working application without human intervention.

## 🚀 Autopilot Initialization

**Run the initialization script to set up the environment:**

```bash
# Find and run the autopilot initialization script
# This handles: project detection, permissions check, resume detection

# First, find the IRIS directory by checking common locations
if [ -d ".claude/commands/iris/utils" ]; then
    IRIS_DIR=".claude/commands/iris"
elif [ -d "$HOME/.claude/commands/iris/utils" ]; then
    IRIS_DIR="$HOME/.claude/commands/iris"
else
    echo "❌ ERROR: IRIS directory not found"
    echo "Check .claude/commands/iris installation"
    exit 1
fi

# Run the Python initialization script
python3 "$IRIS_DIR/utils/autopilot_init.py"
```

**After running the init script, capture the key variables from its output:**

```bash
# The init script outputs these variables at the end - extract them
INIT_OUTPUT=$(python3 "$IRIS_DIR/utils/autopilot_init.py" 2>&1)
echo "$INIT_OUTPUT"

# Extract variables from output
PROJECT_ROOT=$(echo "$INIT_OUTPUT" | grep "^PROJECT_ROOT=" | cut -d'=' -f2)
IRIS_DIR=$(echo "$INIT_OUTPUT" | grep "^IRIS_DIR=" | cut -d'=' -f2)
SKIP_PLANNING=$(echo "$INIT_OUTPUT" | grep "^SKIP_PLANNING=" | cut -d'=' -f2)

# Set environment flags
export IRIS_AUTOPILOT_ACTIVE=true
export IRIS_PROJECT_ROOT="$PROJECT_ROOT"

echo ""
echo "📁 Project Root: $PROJECT_ROOT"
echo "🔧 IRIS Directory: $IRIS_DIR"
echo "⏭️ Skip Planning: $SKIP_PLANNING"
echo ""
```

## 📋 Phase 1: Adaptive Planning

**Run adaptive planning to create sprint plan (skipped if resuming):**

```bash
if [ "$SKIP_PLANNING" = "true" ]; then
    echo "⏭️ Planning phase skipped - using existing project plan"
    echo ""
fi
```

### Planning Instructions

**If `SKIP_PLANNING` is `false` (new project):**
1. Invoke `/iris:plan` with the PRD content from `$ARGUMENTS`
2. **CRITICAL: After `/iris:plan` completes, YOU MUST CONTINUE to Phase 2 below**
3. Do NOT stop after planning - autopilot runs continuously until ALL tasks are done

**If `SKIP_PLANNING` is `true` (resuming):**
1. Skip directly to Phase 2 (Continuous Task Execution Loop)

---

⚠️ **AUTOPILOT CONTINUATION REQUIREMENT** ⚠️

When `/iris:plan` finishes and says "Planning complete", you MUST:
1. **NOT STOP** - autopilot continues automatically
2. **Proceed immediately** to "Verify Planning" below
3. **Then continue** to Phase 2: Execution Loop
4. **Keep executing** until ALL tasks are completed

This is AUTOPILOT mode - you run from start to finish without stopping!

---

**After planning completes (or if resuming), verify the database state:**

```bash
# Verify planning succeeded
PLANNING_CHECK=$(cd "$IRIS_DIR/utils" && python3 -c "
import sys
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

try:
    db = DatabaseManager()
    with db.get_connection() as conn:
        milestones = conn.execute('SELECT COUNT(*) as count FROM milestones').fetchone()
        tasks = conn.execute('SELECT COUNT(*) as count FROM tasks').fetchone()
        if milestones['count'] > 0 and tasks['count'] > 0:
            print(f'success:{milestones[\"count\"]}:{tasks[\"count\"]}')
        else:
            print('failed:0:0')
except Exception as e:
    print(f'error:{e}')
")

IFS=':' read -r STATUS MILESTONE_COUNT TASK_COUNT <<< "$PLANNING_CHECK"

if [[ "$STATUS" != "success" ]]; then
    echo "❌ CRITICAL: Planning phase failed - $PLANNING_CHECK"
    echo "Cannot proceed with autopilot execution."
    exit 1
fi

echo "✅ Planning complete: $MILESTONE_COUNT milestones, $TASK_COUNT tasks created"
echo ""
```

## ⚡ Phase 2: Continuous Task Execution Loop

**Execute all tasks continuously until completion.**

This is the core autopilot loop. You will repeatedly:
1. Get the next eligible task from the database
2. Execute the task using TDD methodology
3. Mark task complete and check for milestone completion
4. Update PROJECT_STATUS.md with current progress
5. Repeat until all tasks are done

### Main Execution Loop

**CRITICAL INSTRUCTION:** Execute this loop by repeatedly running the task execution workflow below until all tasks are complete.

```bash
# Get execution statistics
echo "⚡ Starting continuous task execution..."

STATS=$(cd "$IRIS_DIR/utils" && python3 -c "
import sys
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    total = conn.execute('SELECT COUNT(*) as c FROM tasks').fetchone()['c']
    completed = conn.execute(\"SELECT COUNT(*) as c FROM tasks WHERE status = 'completed'\").fetchone()['c']
    milestones = conn.execute('SELECT COUNT(*) as c FROM milestones').fetchone()['c']
    print(f'{total}:{completed}:{milestones}')
")

IFS=':' read -r TOTAL_TASKS COMPLETED_TASKS TOTAL_MILESTONES <<< "$STATS"
echo "🎯 Executing $TOTAL_TASKS tasks across $TOTAL_MILESTONES milestones"
echo "📊 Currently completed: $COMPLETED_TASKS/$TOTAL_TASKS"
echo ""
```

### Task Execution Workflow (Repeat Until Done)

**For each iteration of this loop:**

#### Step 1: Get Next Eligible Task

```bash
# Query for next eligible task
NEXT_TASK=$(cd "$IRIS_DIR/utils" && python3 -c "
import sys
import json
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # First ensure we have a current milestone set
    current = conn.execute(\"SELECT value FROM project_state WHERE key = 'current_milestone_id'\").fetchone()

    if not current or not current['value']:
        # Set first pending milestone as current
        first_milestone = conn.execute(\"SELECT id FROM milestones WHERE status = 'pending' ORDER BY order_index LIMIT 1\").fetchone()
        if first_milestone:
            conn.execute(\"UPDATE project_state SET value = ? WHERE key = 'current_milestone_id'\", (first_milestone['id'],))
            conn.commit()
            milestone_id = first_milestone['id']
        else:
            # Check if all done
            remaining = conn.execute(\"SELECT COUNT(*) as c FROM tasks WHERE status != 'completed'\").fetchone()['c']
            if remaining == 0:
                print(json.dumps({'status': 'all_complete'}))
            else:
                print(json.dumps({'status': 'error', 'message': 'No milestone found'}))
            sys.exit(0)
    else:
        milestone_id = current['value']

    # Get next pending task with satisfied dependencies
    task = conn.execute('''
        SELECT t.id, t.title, t.description, t.milestone_id, m.name as milestone_name
        FROM tasks t
        JOIN milestones m ON t.milestone_id = m.id
        WHERE t.milestone_id = ?
        AND t.status = 'pending'
        AND NOT EXISTS (
            SELECT 1 FROM task_dependencies td
            JOIN tasks dep ON td.depends_on_task_id = dep.id
            WHERE td.task_id = t.id AND dep.status != 'completed'
        )
        ORDER BY t.order_index
        LIMIT 1
    ''', (milestone_id,)).fetchone()

    if task:
        print(json.dumps({
            'status': 'found',
            'task_id': task['id'],
            'title': task['title'],
            'description': task['description'],
            'milestone_id': task['milestone_id'],
            'milestone_name': task['milestone_name']
        }))
    else:
        # Check if milestone is complete
        remaining_in_milestone = conn.execute('''
            SELECT COUNT(*) as c FROM tasks
            WHERE milestone_id = ? AND status != 'completed'
        ''', (milestone_id,)).fetchone()['c']

        if remaining_in_milestone == 0:
            # Mark milestone complete and move to next
            conn.execute(\"UPDATE milestones SET status = 'completed', completed_at = datetime('now') WHERE id = ?\", (milestone_id,))
            next_milestone = conn.execute(\"SELECT id FROM milestones WHERE status = 'pending' ORDER BY order_index LIMIT 1\").fetchone()
            if next_milestone:
                conn.execute(\"UPDATE project_state SET value = ? WHERE key = 'current_milestone_id'\", (next_milestone['id'],))
                conn.commit()
                print(json.dumps({'status': 'milestone_complete', 'completed_milestone': milestone_id, 'next_milestone': next_milestone['id']}))
            else:
                conn.commit()
                print(json.dumps({'status': 'all_complete'}))
        else:
            print(json.dumps({'status': 'blocked', 'message': 'Tasks blocked by dependencies'}))
")

# Parse the result
TASK_STATUS=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','error'))")

if [[ "$TASK_STATUS" == "all_complete" ]]; then
    echo "✅ All tasks completed! Moving to final validation..."
    # Break out of loop - proceed to Phase 3
fi

if [[ "$TASK_STATUS" == "milestone_complete" ]]; then
    COMPLETED_MS=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('completed_milestone',''))")
    NEXT_MS=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('next_milestone',''))")
    echo "🎉 Milestone $COMPLETED_MS completed!"
    echo "➡️ Moving to milestone $NEXT_MS"
    # Continue loop - get next task
fi

if [[ "$TASK_STATUS" == "found" ]]; then
    TASK_ID=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('task_id',''))")
    TASK_TITLE=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title',''))")
    TASK_DESC=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('description',''))")
    MILESTONE_NAME=$(echo "$NEXT_TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('milestone_name',''))")

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 EXECUTING TASK: $TASK_ID"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Title: $TASK_TITLE"
    echo "📁 Milestone: $MILESTONE_NAME"
    echo "📝 Description: $TASK_DESC"
    echo ""
fi
```

#### Step 2: Mark Task In-Progress and Execute

```bash
# Mark task as in-progress
cd "$IRIS_DIR/utils" && python3 -c "
import sys
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute(\"UPDATE tasks SET status = 'in_progress', started_at = datetime('now') WHERE id = ?\", ('$TASK_ID',))
    conn.commit()
print('Task marked in-progress')
"

echo "🔧 Task $TASK_ID marked as in-progress"
echo ""
```

**CRITICAL:** Now you must ACTUALLY IMPLEMENT the task described above.

Using your available tools (Read, Write, Edit, Bash, Glob, Grep), implement the task requirements:
- Read relevant files to understand context
- Write or edit code to implement the feature
- Run tests if applicable
- Ensure the implementation is complete

**Do the actual implementation work here before proceeding to mark the task complete.**

#### Step 3: Mark Task Complete

After implementing the task:

```bash
# Mark task as completed
cd "$IRIS_DIR/utils" && python3 -c "
import sys
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        UPDATE tasks
        SET status = 'completed',
            completed_at = datetime('now'),
            duration_minutes = CAST((julianday('now') - julianday(started_at)) * 24 * 60 AS INTEGER)
        WHERE id = ?
    ''', ('$TASK_ID',))
    conn.commit()
print('Task marked completed')
"

echo "✅ Task $TASK_ID completed!"
echo ""
```

#### Step 4: Update Progress and Status File

```bash
# Get updated progress
PROGRESS=$(cd "$IRIS_DIR/utils" && python3 -c "
import sys
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    total = conn.execute('SELECT COUNT(*) as c FROM tasks').fetchone()['c']
    completed = conn.execute(\"SELECT COUNT(*) as c FROM tasks WHERE status = 'completed'\").fetchone()['c']
    pct = int((completed / total) * 100) if total > 0 else 0
    print(f'{completed}/{total} ({pct}%)')
")

echo "📊 Progress: $PROGRESS"

# Update PROJECT_STATUS.md with current state
cd "$IRIS_DIR/utils" && python3 -c "
import sys
sys.path.insert(0, '.')
from status_translator import StatusTranslator
from database.db_manager import DatabaseManager

db = DatabaseManager()
translator = StatusTranslator(db)
translator.update_status_file()
"
echo ""
```

**LOOP INSTRUCTION:** After completing a task, return to "Step 1: Get Next Eligible Task" and repeat this process until `TASK_STATUS` equals `all_complete`.

## 🎯 Phase 3: Final Validation & Completion

**Once all tasks are complete, run final validation:**

```bash
echo "────────────────────────────────────────────────"
echo "🎯 Phase 3: Final Validation"
echo "────────────────────────────────────────────────"
```

Now invoke `/iris:validate` to run the final validation checks.

After validation completes:

```bash
echo "────────────────────────────────────────────────"
echo "✅ IRIS AUTOPILOT COMPLETE!"
echo "────────────────────────────────────────────────"

# Generate completion summary
cd "$IRIS_DIR/utils" && python3 -c "
import sys
from datetime import datetime
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    total_tasks = conn.execute('SELECT COUNT(*) as c FROM tasks').fetchone()['c']
    completed_tasks = conn.execute(\"SELECT COUNT(*) as c FROM tasks WHERE status = 'completed'\").fetchone()['c']
    total_milestones = conn.execute('SELECT COUNT(*) as c FROM milestones').fetchone()['c']
    completed_milestones = conn.execute(\"SELECT COUNT(*) as c FROM milestones WHERE status = 'completed'\").fetchone()['c']

    # Get start time
    start = conn.execute(\"SELECT value FROM project_metadata WHERE key = 'analysis_timestamp'\").fetchone()
    if start:
        start_time = datetime.fromisoformat(start['value'])
        duration = (datetime.now() - start_time).total_seconds() / 60
        print(f'⏰ Total time: {duration:.1f} minutes')

    print('📊 Session summary:')
    print(f'   Tasks completed: {completed_tasks}/{total_tasks}')
    print(f'   Milestones completed: {completed_milestones}/{total_milestones}')
    print('📁 Application ready!')
    print('📝 Full report: PROJECT_STATUS.md')

    # Update completion status
    conn.execute(\"INSERT OR REPLACE INTO project_metadata (key, value) VALUES ('autopilot_completed', ?)\", (datetime.now().isoformat(),))
    conn.commit()
"

echo ""
echo "🎉 Autonomous development complete!"
echo "────────────────────────────────────────────────"
```

## ⚠️ Safety Features

### Emergency Stop
- **Ctrl+C**: Graceful shutdown with state preservation
- **Critical errors**: Automatic stop with diagnostic info

### Rollback Protection
- **Milestone checkpoints**: Automatic rollback points in database
- **State preservation**: All progress saved atomically

### Monitoring
- **PROJECT_STATUS.md**: Real-time progress updated by Status Translator
- **SQLite database**: All state stored with atomic transactions

## 🔧 Execution Summary

The autopilot follows this flow:
1. **Permission Check** → Verify dangerous mode enabled
2. **Planning** → Invoke `/iris:plan` to create sprint plan
3. **Execution Loop** → Repeatedly get next task, implement it, mark complete
4. **Validation** → Invoke `/iris:validate` for final checks
5. **Completion** → Generate summary report

**KEY DIFFERENCE FROM MANUAL MODE:** In autopilot, YOU (Claude) directly implement each task using your tools. There is no subprocess spawning - you are the executor.

## 📋 Prerequisites

Before running autopilot:
1. **Dangerous permissions enabled** (checked automatically)
2. **Clear PRD or requirements** provided
3. **Writable project directory**
4. **Network access** for research/dependencies

---

## 🔴 CRITICAL REMINDERS

1. **NEVER STOP AFTER PLANNING** - When `/iris:plan` says "Planning complete", immediately continue to Phase 2
2. **NEVER STOP AFTER A SINGLE TASK** - Keep looping until ALL tasks show `all_complete`
3. **YOU ARE THE EXECUTOR** - Directly implement each task using your tools (Read, Write, Edit, Bash)
4. **CONTINUOUS OPERATION** - Autopilot means no stopping until the project is fully built

**IRIS Autopilot transforms your idea into working code autonomously. You ARE the autonomous agent - execute tasks directly using your tools!** ✨
