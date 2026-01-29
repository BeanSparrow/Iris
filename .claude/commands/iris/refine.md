---
allowed-tools:
  - Bash
  - Read
  - Task
  - Edit
  - Write
  - Glob
  - Grep
description: "Usage: /iris:refine - Run Ralph-style iterative refinement loop"
---

# Iris Refine Module

**Purpose:** Implement Ralph Wiggum-style iterative refinement to improve the implementation toward better PRD alignment.

**Can be invoked:**
- **Standalone:** `/iris:refine` - Run refinement on an existing project
- **Via Autopilot:** Executed inline as part of `/iris:autopilot` workflow

---

## Initialization (Standalone or Inline)

**First, establish the environment variables if not already set:**

```bash
# Find project root if not set (standalone invocation)
if [[ -z "$PROJECT_ROOT" ]]; then
    PROJECT_ROOT=$(pwd)
    while [[ "$PROJECT_ROOT" != "/" ]] && [[ ! -d "$PROJECT_ROOT/.claude" ]]; do
        PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
    done
fi

# Find IRIS directory if not set
if [[ -z "$IRIS_DIR" ]]; then
    if [[ -d "$PROJECT_ROOT/.claude/commands/iris" ]]; then
        IRIS_DIR="$PROJECT_ROOT/.claude/commands/iris"
    elif [[ -d "$HOME/.claude/commands/iris" ]]; then
        IRIS_DIR="$HOME/.claude/commands/iris"
    fi
fi

# Set environment variable for DatabaseManager
export IRIS_PROJECT_ROOT="$PROJECT_ROOT"

echo "🔄 IRIS Refine Module"
echo "   Project Root: $PROJECT_ROOT"
echo "   IRIS Directory: $IRIS_DIR"
echo ""

# Verify project has been planned (tasks exist)
TASK_CHECK=$(python3 -c "
import sys
sys.path.insert(0, '$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

try:
    db = DatabaseManager('$PROJECT_ROOT')
    with db.get_connection() as conn:
        tasks = conn.execute('SELECT COUNT(*) as c FROM tasks').fetchone()['c']
        completed = conn.execute(\"SELECT COUNT(*) as c FROM tasks WHERE status = 'completed'\").fetchone()['c']
        print(f'{tasks}:{completed}')
except Exception as e:
    print(f'error:{e}')
")

IFS=':' read -r TOTAL_TASKS COMPLETED_TASKS <<< "$TASK_CHECK"

if [[ "$TOTAL_TASKS" == "error"* ]]; then
    echo "❌ ERROR: Cannot access project database"
    echo "   $TASK_CHECK"
    echo "   Run /iris:plan first to initialize the project."
    exit 1
fi

if [[ "$TOTAL_TASKS" -eq 0 ]]; then
    echo "❌ ERROR: No tasks found in project"
    echo "   Run /iris:plan first to create tasks."
    exit 1
fi

echo "📊 Project Status: $COMPLETED_TASKS/$TOTAL_TASKS tasks completed"
echo ""
```

---

## Prose-Orchestration Context

When invoked via autopilot (inline execution), this module:

1. **Has access to the PRD** - Stored in project_metadata, retrieve it for each refiner iteration
2. **Has access to $IRIS_DIR** - Set by autopilot.md or initialization above
3. **Has access to $PROJECT_ROOT** - Set by autopilot.md or initialization above
4. **Returns control to autopilot.md** - After completing all iterations

---

## Ralph Wiggum Philosophy

This module implements the Ralph Wiggum iterative refinement approach:

| Principle | Implementation |
|-----------|----------------|
| **Fresh Context** | Each iteration uses fresh subagents that see the codebase without accumulated baggage |
| **Progress in Files** | Improvements are committed to git; state persists in database |
| **Fixed Iterations** | Loop runs exactly `max_iterations` times — do NOT terminate early |
| **Improve, Not Just Fix** | Focus on enhancement toward PRD intent, not just bug repair |
| **PRD Anchoring** | Refiner receives the original PRD each iteration to maintain alignment |
| **Backpressure** | Validation provides feedback but doesn't terminate the loop |

**Critical:** The loop MUST run for the full `max_iterations` count. Do not exit early even if no issues are found. Each iteration provides fresh perspective for improvement.

---

## Configuration by Complexity

Retrieve refine configuration based on project complexity:

| Complexity | Max Iterations | Reviewers | Review Focus Areas |
|------------|----------------|-----------|-------------------|
| MICRO | 5 | 2 | gaps, quality |
| SMALL | 5 | 3 | gaps, quality, edge_cases |
| MEDIUM | 6 | 4 | gaps, quality, integration, edge_cases |
| LARGE | 8 | 5 | gaps, quality, integration, edge_cases, security |
| ENTERPRISE | 10 | 6 | gaps, quality, integration, edge_cases, security, performance |

---

## Phase 0: Initialization

### Step 0.1: Load Configuration

```bash
# Get refine configuration from database
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Get complexity
    result = conn.execute('''
        SELECT value FROM project_metadata WHERE key = 'project_complexity'
    ''').fetchone()
    complexity = result['value'] if result else 'MEDIUM'

    # Get max iterations (default based on complexity)
    iter_result = conn.execute('''
        SELECT value FROM project_state WHERE key = 'refine_max_iterations'
    ''').fetchone()

    # Complexity-based defaults
    defaults = {
        'MICRO': 5, 'SMALL': 5, 'MEDIUM': 6,
        'LARGE': 8, 'ENTERPRISE': 10
    }
    max_iter = int(iter_result['value']) if iter_result else defaults.get(complexity.upper(), 5)

    print(f'COMPLEXITY: {complexity}')
    print(f'MAX_ITERATIONS: {max_iter}')
"
```

Store the values:
- `$COMPLEXITY` = detected complexity level
- `$MAX_ITERATIONS` = number of iterations to run (minimum 5)

### Step 0.2: Load PRD Content

```bash
# Retrieve PRD from database
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    result = conn.execute('''
        SELECT value FROM project_metadata WHERE key = 'prd_content'
    ''').fetchone()
    if result:
        print(result['value'])
    else:
        print('ERROR: PRD not found in database')
"
```

Store as `$PRD_CONTENT` for use in refiner prompts.

### Step 0.3: Load Tech Stack

```bash
# Get approved tech stack
python3 -c "
import sys
import json
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    results = conn.execute('''
        SELECT name, category, version FROM technologies
    ''').fetchall()

    stack = {row['category']: {'name': row['name'], 'version': row['version']} for row in results}
    print(json.dumps(stack, indent=2))
"
```

Store as `$TECH_STACK` for use in refiner prompts.

### Step 0.4: Initialize Refine State

```bash
python3 -c "
import sys
from datetime import datetime
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO project_state (key, value)
        VALUES ('refine_phase_status', 'in_progress')
    ''')
    conn.execute('''
        INSERT OR REPLACE INTO project_state (key, value)
        VALUES ('refine_current_iteration', '0')
    ''')
    conn.execute('''
        INSERT OR REPLACE INTO project_metadata (key, value)
        VALUES ('refine_started_at', ?)
    ''', (datetime.now().isoformat(),))
    conn.commit()
    print('✅ Refine phase initialized')
"
```

---

## Phase 1: Iteration Loop

**CRITICAL:** Execute this loop exactly `$MAX_ITERATIONS` times. Do NOT exit early.

```
for iteration in range(1, MAX_ITERATIONS + 1):
    Phase 1A: Review (parallel subagents)
    Phase 1B: Aggregate findings
    Phase 1C: Refine (single subagent)
    Phase 1D: Validate
    Phase 1E: Record iteration
```

---

## Phase 1A: Review (Parallel Fresh Subagents)

**Purpose:** Analyze codebase with fresh context, identify improvement opportunities.

### Step 1A.1: Determine Review Focus Areas

Based on `$COMPLEXITY`, select reviewers:

| Complexity | Focus Areas |
|------------|-------------|
| MICRO | `gaps`, `quality` |
| SMALL | `gaps`, `quality`, `edge_cases` |
| MEDIUM | `gaps`, `quality`, `integration`, `edge_cases` |
| LARGE | `gaps`, `quality`, `integration`, `edge_cases`, `security` |
| ENTERPRISE | `gaps`, `quality`, `integration`, `edge_cases`, `security`, `performance` |

### Step 1A.2: Prepare Review Agent Prompts

For each focus area, prepare a prompt using this template:

```markdown
You are a code reviewer analyzing an implementation. Your focus: **[FOCUS_AREA]**

## Original Requirements (PRD)
[Insert $PRD_CONTENT]

## Your Focus Area: [FOCUS_AREA]

### Focus-Specific Instructions

**If gaps:** Compare implementation against PRD. What features are missing? What requirements are not fully met? What deviates from the spec?

**If quality:** Review code patterns and consistency. What code smells exist? What patterns are inconsistent? Where is technical debt accumulating?

**If integration:** Do components work together correctly? Are API contracts honored? Are there integration issues between modules?

**If edge_cases:** Is error handling comprehensive? Are edge cases covered? Is input validation sufficient?

**If security:** Check for OWASP issues. Is input sanitized? Are there auth gaps? SQL injection? XSS risks?

**If performance:** Are there obvious performance issues? N+1 queries? Unnecessary re-renders? Memory leaks?

## Instructions
1. Analyze the codebase thoroughly (use Glob, Grep, Read tools)
2. Compare against the PRD requirements above
3. Identify improvement opportunities in your focus area
4. **DO NOT modify any files** — read and analyze only

## Output Format
Return your findings as JSON (keep under 500 words total):

```json
{
  "focus_area": "[FOCUS_AREA]",
  "iteration": [N],
  "findings": [
    {
      "severity": "HIGH|MEDIUM|LOW",
      "file": "path/to/file",
      "line": 42,
      "description": "What you found",
      "suggestion": "How to improve it",
      "prd_reference": "Which PRD requirement this relates to"
    }
  ],
  "summary": "Brief overall assessment (1-2 sentences)"
}
```
```

### Step 1A.3: Launch Parallel Review Agents

**CRITICAL:** Launch ALL review agents in a SINGLE message with multiple Task tool calls.

For each focus area, invoke:
```
Task tool call:
- subagent_type: "general-purpose"
- description: "Review [FOCUS_AREA] iteration [N]"
- prompt: [Prepared prompt from Step 1A.2]
```

**Example for MEDIUM complexity (4 reviewers):**
```
[Task 1: gaps review]
[Task 2: quality review]
[Task 3: integration review]
[Task 4: edge_cases review]
```

All tasks launch simultaneously for parallel execution.

### Step 1A.4: Collect Review Results

As each subagent completes, collect the JSON findings.

---

## Phase 1B: Aggregate Findings

### Step 1B.1: Combine All Findings

Merge findings from all reviewers into a single list:

```
ITERATION [N] FINDINGS:
┌──────────┬─────────────────┬──────────────────────────────────────────┐
│ Severity │ Focus           │ Description                              │
├──────────┼─────────────────┼──────────────────────────────────────────┤
│ HIGH     │ gaps            │ Missing user authentication feature      │
│ HIGH     │ security        │ SQL injection risk in search endpoint    │
│ MEDIUM   │ quality         │ Inconsistent error handling pattern      │
│ LOW      │ edge_cases      │ Missing null check in helper function    │
└──────────┴─────────────────┴──────────────────────────────────────────┘
```

### Step 1B.2: Prioritize Findings

Sort findings by:
1. Severity (HIGH → MEDIUM → LOW)
2. PRD alignment (gaps > others for PRD-critical items)
3. File locality (group changes to same file)

### Step 1B.3: Store Findings

```bash
# Store each finding in database
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # First, get or create iteration record
    conn.execute('''
        INSERT INTO refine_iterations (iteration_number, status, started_at)
        VALUES (?, 'in_progress', datetime('now'))
    ''', ([ITERATION_NUMBER],))

    iteration_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Insert finding
    conn.execute('''
        INSERT INTO refine_findings
        (iteration_id, reviewer_focus, severity, category, file_path, line_number, description, suggestion, prd_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (iteration_id, '[FOCUS]', '[SEVERITY]', '[CATEGORY]', '[FILE]', [LINE], '[DESC]', '[SUGGESTION]', '[PRD_REF]'))

    conn.commit()
    print(f'✅ Finding stored for iteration {[ITERATION_NUMBER]}')
"
```

---

## Phase 1C: Refine (Single Fresh Subagent)

**Purpose:** Improve the implementation based on findings, anchored to PRD intent.

### Step 1C.1: Prepare Refiner Prompt

```markdown
You are improving an implementation toward better alignment with its requirements.

## Original Requirements (PRD)
[Insert $PRD_CONTENT — FULL PRD, not a summary]

## Approved Tech Stack
[Insert $TECH_STACK]

## Review Findings (Iteration [N])
[Insert aggregated findings JSON from Phase 1B]

## Instructions
You are IMPROVING, not just fixing. With fresh eyes:

1. Review the findings from the review agents above
2. Review the relevant parts of the codebase
3. For each improvement opportunity (prioritized by severity):
   - Implement the improvement
   - Run tests to verify (if tests exist)
   - Commit with descriptive message
4. Focus on alignment with PRD intent, not just addressing symptoms
5. Do NOT add features beyond the PRD scope
6. Do NOT refactor code unrelated to findings

## Constraints
- Only modify files related to findings
- Use only technologies from the approved stack
- Maintain existing code style and patterns
- Run tests after changes if test suite exists

## Completion
After working through improvements, provide a summary:

```json
{
  "iteration": [N],
  "improvements_made": [
    {
      "finding_addressed": "description of finding",
      "change_made": "what you did",
      "files_modified": ["list", "of", "files"],
      "tests_passing": true
    }
  ],
  "commits": ["commit-hash-1", "commit-hash-2"],
  "remaining_concerns": ["anything you couldn't address and why"]
}
```
```

### Step 1C.2: Launch Refiner Agent

**Single subagent with full tool access:**

```
Task tool call:
- subagent_type: "general-purpose"
- description: "Refine iteration [N]"
- prompt: [Prepared prompt from Step 1C.1]
```

### Step 1C.3: Collect Refiner Results

Parse the refiner's completion summary JSON.

### Step 1C.4: Store Improvements

```bash
# Store each improvement in database
python3 -c "
import sys
import json
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Get current iteration ID
    result = conn.execute('''
        SELECT id FROM refine_iterations WHERE iteration_number = ? ORDER BY id DESC LIMIT 1
    ''', ([ITERATION_NUMBER],)).fetchone()
    iteration_id = result['id']

    # Insert improvement
    conn.execute('''
        INSERT INTO refine_improvements
        (iteration_id, finding_id, description, files_modified, commit_hash, tests_passing)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (iteration_id, [FINDING_ID_OR_NULL], '[DESCRIPTION]', json.dumps([FILES]), '[COMMIT]', [TESTS_BOOL]))

    conn.commit()
    print(f'✅ Improvement stored for iteration {[ITERATION_NUMBER]}')
"
```

---

## Phase 1D: Validate

**Purpose:** Provide backpressure, but do NOT terminate the loop.

### Step 1D.1: Run Validation Checks

```bash
# Run test suite if it exists
if [ -f "package.json" ]; then
    npm test 2>&1 || echo "Tests completed with issues"
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    python -m pytest 2>&1 || echo "Tests completed with issues"
elif [ -f "Cargo.toml" ]; then
    cargo test 2>&1 || echo "Tests completed with issues"
fi
```

### Step 1D.2: Record Validation Result

```bash
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Update iteration with validation result
    conn.execute('''
        UPDATE refine_iterations
        SET validation_passed = ?,
            completed_at = datetime('now'),
            status = 'completed'
        WHERE iteration_number = ?
    ''', ([VALIDATION_PASSED], [ITERATION_NUMBER]))

    conn.commit()
    print(f'✅ Iteration {[ITERATION_NUMBER]} completed (validation: {[VALIDATION_PASSED]})')
"
```

**CRITICAL:** Validation result is recorded but does NOT affect loop continuation. Continue to next iteration regardless.

---

## Phase 1E: Record Iteration Progress

### Step 1E.1: Update Iteration Counter

```bash
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO project_state (key, value)
        VALUES ('refine_current_iteration', ?)
    ''', (str([CURRENT_ITERATION]),))
    conn.commit()
"
```

### Step 1E.2: Output Iteration Summary

```
═══════════════════════════════════════════════════════════════
           REFINE ITERATION [N] of [MAX] COMPLETE
═══════════════════════════════════════════════════════════════

Findings This Iteration:    [COUNT]
  - HIGH severity:          [COUNT]
  - MEDIUM severity:        [COUNT]
  - LOW severity:           [COUNT]

Improvements Made:          [COUNT]
Files Modified:             [COUNT]
Tests Passing:              [YES/NO]

Progress: [████████░░] [N]/[MAX] iterations

═══════════════════════════════════════════════════════════════
```

### Step 1E.3: Continue to Next Iteration

**IMPORTANT:** Return to Phase 1A for the next iteration. Do NOT exit the loop until all `$MAX_ITERATIONS` are complete.

---

## Phase 2: Completion

After ALL iterations are complete:

### Step 2.1: Final Validation

Run comprehensive validation:

```bash
# Run full test suite
npm test 2>&1 || python -m pytest 2>&1 || cargo test 2>&1

# Check for lint errors
npm run lint 2>&1 || flake8 . 2>&1 || cargo clippy 2>&1

# Check build
npm run build 2>&1 || python -m py_compile *.py 2>&1 || cargo build 2>&1
```

### Step 2.2: Generate Refine Report

Generate a detailed report showing findings and improvements for each iteration:

```bash
# Generate detailed refine report
python3 "$IRIS_DIR/utils/refine_orchestrator.py" detailed-report
```

This outputs a per-iteration breakdown including:
- Findings discovered (with severity, file location, description)
- Improvements made (with files modified and test status)
- Overall summary statistics

### Step 2.3: Update Refine State

```bash
python3 -c "
import sys
from datetime import datetime
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO project_state (key, value)
        VALUES ('refine_phase_status', 'completed')
    ''')
    conn.execute('''
        INSERT OR REPLACE INTO project_metadata (key, value)
        VALUES ('refine_completed_at', ?)
    ''', (datetime.now().isoformat(),))
    conn.commit()
    print('✅ Refine phase completed')
"
```

### Step 2.4: Output Final Summary

```
═══════════════════════════════════════════════════════════════
                    REFINE PHASE COMPLETE
═══════════════════════════════════════════════════════════════

ITERATION SUMMARY:
──────────────────────────────────────────────────────────────
Total Iterations:           [MAX_ITERATIONS]
Validation Passed:          [COUNT] / [MAX_ITERATIONS]

FINDINGS SUMMARY:
──────────────────────────────────────────────────────────────
Total Findings:             [TOTAL]
  - HIGH severity:          [COUNT]
  - MEDIUM severity:        [COUNT]
  - LOW severity:           [COUNT]
Findings Addressed:         [COUNT] ([PERCENTAGE]%)

IMPROVEMENTS SUMMARY:
──────────────────────────────────────────────────────────────
Total Improvements:         [COUNT]
With Passing Tests:         [COUNT]
Commits Made:               [COUNT]

QUALITY METRICS:
──────────────────────────────────────────────────────────────
Final Test Status:          [PASSING/FAILING]
Final Lint Status:          [CLEAN/WARNINGS/ERRORS]
Final Build Status:         [SUCCESS/FAILED]

═══════════════════════════════════════════════════════════════
         Implementation refined through [N] iterations
              aligned toward PRD requirements
═══════════════════════════════════════════════════════════════
```

---

## Error Handling

### Review Agent Failure
If a review agent fails or times out:
1. Log the failure
2. Continue with findings from other reviewers
3. Do NOT halt the iteration

### Refiner Agent Failure
If the refiner agent fails:
1. Log the failure with error details
2. Record iteration as completed with 0 improvements
3. Continue to next iteration

### Validation Failure
If validation fails:
1. Record the failure
2. **Continue to next iteration** (do NOT exit loop)
3. Validation is backpressure, not a gate

### Database Error
If database operations fail:
1. Log the error
2. Attempt to continue without database recording
3. Output findings/improvements to console for manual tracking

---

## Integration Notes

**This module is invoked by autopilot.md via prose-orchestration:**

autopilot.md instructs Claude to use the Read tool on `$IRIS_DIR/refine.md` and execute its instructions inline. The invocation looks like:

```markdown
**INSTRUCTION:** Use the Read tool to read the file at `$IRIS_DIR/refine.md`,
then execute its instructions inline to perform iterative refinement.
```

**Database tables used:**
- `project_state` - Tracks refine phase status and current iteration
- `project_metadata` - Stores PRD content, timestamps
- `refine_iterations` - Records each iteration's status
- `refine_findings` - Stores findings from review agents
- `refine_improvements` - Tracks improvements made by refiner

**Returns control to autopilot.md after:**
- All `$MAX_ITERATIONS` iterations complete
- Final summary is output
- `refine_phase_status` is set to 'completed'
