# Iris Quick Start Guide

## Autonomous Development in 3 Steps

### Step 1: Launch Claude Code with Permissions

Iris Autopilot requires Claude Code to be launched with the permissions flag:

```bash
claude --dangerously-skip-permissions
```

This allows Claude to execute tools (file writes, bash commands, etc.) without prompting you for each one.

**⚠️ Without this flag, you'll be prompted for every action, making autopilot useless!**

**Optional:** Set `CLAUDE_DANGEROUS_MODE=true` to suppress the startup warning:
```bash
export CLAUDE_DANGEROUS_MODE=true
claude --dangerously-skip-permissions
```

### Step 2: Run Autopilot

```bash
# Simple script (MICRO complexity)
/iris:autopilot "Create a Python script to convert CSV to JSON"

# Web application (MEDIUM complexity)
/iris:autopilot "Build a task management app with user auth"

# Larger system (LARGE complexity)
/iris:autopilot "Develop an e-commerce API with payment integration"
```

### Step 3: Monitor Progress

```bash
# Watch real-time status (updates every 30 seconds)
watch cat PROJECT_STATUS.md

# View detailed execution logs
tail -f .tasks/autopilot.log

# Check metrics
cat .tasks/autopilot_metrics.json
```

## Interruption & Resume

Iris automatically detects existing project state. If autopilot is interrupted:

```bash
# Simply re-run autopilot with any argument
/iris:autopilot "resume"
```

Iris will:
1. Detect the existing project in `.tasks/iris_project.db`
2. Show current progress (e.g., "5/12 tasks completed")
3. Reset any interrupted tasks back to pending
4. Skip planning and resume the execution loop

```bash
# Emergency stop
Ctrl+C
```

## What Happens During Autopilot

1. **Planning Phase**
   - Analyzes project complexity (MICRO → ENTERPRISE)
   - Generates adaptive development plan
   - Creates milestones and tasks in SQLite database

2. **Execution Phase**
   - Continuous task execution with dependency resolution
   - Real-time progress tracking
   - Adaptive validation based on project scale
   - Live documentation via Status Translator

3. **Completion Phase**
   - Final validation checks
   - Generate completion report
   - Application ready for review

## Troubleshooting

### Getting Permission Prompts?
You didn't launch Claude with the required flag. Exit and restart:
```bash
claude --dangerously-skip-permissions
```

### Want to Suppress the Startup Warning?
Set the environment variable before launching:
```bash
export CLAUDE_DANGEROUS_MODE=true
claude --dangerously-skip-permissions
```

### View Setup Instructions
```bash
cd .claude/commands/iris/utils
python3 permissions_checker.py --instructions
```

### Check Database State
```bash
# View current progress
cd .claude/commands/iris/utils
python3 -c "
from database.db_manager import DatabaseManager
db = DatabaseManager()
with db.get_connection() as conn:
    tasks = conn.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status=\"completed\" THEN 1 ELSE 0 END) as done FROM tasks').fetchone()
    print(f'Progress: {tasks[\"done\"]}/{tasks[\"total\"]} tasks')
"
```

### Debugging Mode
```bash
# For troubleshooting, run commands individually with manual mode enabled
export IRIS_MANUAL_MODE=true
/iris:plan "Your requirements"     # Plan step
/iris:execute                      # Execute tasks (stops on errors)
/iris:validate                     # Validate milestone
```

## Tips

- **Start Small**: Test with simple scripts before complex projects
- **Monitor Progress**: Watch PROJECT_STATUS.md during execution
- **Use Descriptive PRDs**: Better requirements produce better results
- **Check the Database**: All state is in `.tasks/iris_project.db`

## Success Indicators

- PROJECT_STATUS.md updates regularly
- Progress percentage increases steadily
- Tasks transition: pending → in_progress → completed
- Application launches successfully after completion

---

**Ready to build? Run `/iris:autopilot "Your project idea"` and let Iris handle the rest.**
