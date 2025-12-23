# Iris

An autonomous PRD-to-prototype development framework for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## What is Iris?

Iris is an experimental framework that attempts to transform a Product Requirements Document (PRD) into a working prototype autonomously. You provide the requirements, enable the necessary permissions, and Iris handles the planning, implementation, and validation phases without human intervention.

The name comes from the iris of a camera—the aperture that adapts to different lighting conditions. Similarly, this framework adapts its approach based on project complexity, scaling from simple scripts to full applications.

**Important:** This is a prototype-focused tool designed for rapid feasibility testing and proof-of-concept development. It is not intended for production application development.

## Origin & Attribution

Iris is built upon the [Gustav Framework](https://github.com/anthropics/claude-code-framework/tree/main/frameworks/gustav) created by [Dimitri Tholen](https://github.com/dimitritholen). Gustav established the foundational concepts:

- Milestone-driven development with structured sprints
- Parallel research agents for technology decisions
- Anti-hallucination guards to prevent AI drift
- Scope creep prevention with feature limits
- Human-in-the-loop validation checkpoints

Iris extends Gustav with autonomous execution capabilities and replaces the JSON-based project tracking with a SQLite database backend for improved reliability and state management.

## Key Changes from Gustav

### Autonomous Execution
Gustav requires human validation at each milestone. Iris introduces an autopilot mode that runs continuously from PRD to completion, with configurable validation frequency based on project complexity.

### SQLite Database Backend
Gustav tracks project state across multiple JSON files (`task_graph.json`, `progress_tracker.json`, `techstack_research.json`, etc.). Iris consolidates all project data into a single SQLite database (`.tasks/iris_project.db`) with:

- Atomic transactions for data integrity
- Relational structure for task dependencies
- Automatic backup and restore capabilities
- Schema versioning for future migrations

### Adaptive Complexity Scaling
Gustav applies the same enterprise-grade process to all projects. Iris analyzes the PRD and scales its approach accordingly:

| Complexity | Features | Research Agents | Tasks/Milestone | Validation |
|------------|----------|-----------------|-----------------|------------|
| MICRO | 1-2 | 0 | 1-3 | Minimal |
| SMALL | 1-3 | 2 | 2-5 | Major milestones |
| MEDIUM | 3-7 | 4 | 3-7 | Each milestone |
| LARGE | 5-10 | 8 | 5-10 | Comprehensive |
| ENTERPRISE | 7-15 | 12 | 8-15 | Full suite |

## Installation

Clone or copy the `.claude/commands/iris` directory to your project:

```bash
# Option 1: Project-local installation
mkdir -p .claude/commands
cp -r /path/to/iris .claude/commands/

# Option 2: Global installation
cp -r /path/to/iris ~/.claude/commands/
```

## Commands

| Command | Description |
|---------|-------------|
| `/iris:autopilot <PRD>` | **Primary command** - Autonomous development from PRD to completion |
| `/iris:plan <PRD>` | Generate sprint plan (used internally by autopilot) |
| `/iris:execute [task-id]` | Execute tasks (used internally by autopilot) |
| `/iris:validate [milestone]` | Validate milestone (used internally by autopilot) |
| `/iris:document [flags]` | Generate/update documentation (README, status, completion report) |
| `/iris:audit [scope]` | Security analysis |
| `/iris:help` | Display help information |

## Usage

Iris is designed for autonomous operation. Provide your requirements and let it build:

```bash
/iris:autopilot "Build a REST API for task management with user authentication"
```

This requires the permissions flag. See [Permission Setup](#permission-setup).

### Development Loop

Autopilot executes a 4-phase loop for each milestone:

```
Plan → Execute → Validate → Document
         ↑________________________↓
              (per milestone)
```

1. **Plan** - Analyze PRD, create milestones and tasks
2. **Execute** - Implement tasks with TDD methodology
3. **Validate** - Verify milestone completion, run tests
4. **Document** - Update README.md, PROJECT_STATUS.md

On final completion, Iris generates a `COMPLETION_REPORT.md` with KPIs (total time, tasks completed, validation rate, errors recovered).

### Debugging Mode

The individual commands (`/iris:plan`, `/iris:execute`, `/iris:validate`, `/iris:document`) can be run separately for debugging or step-by-step control. Set `IRIS_MANUAL_MODE=true` to enable blocking on errors:

```bash
export IRIS_MANUAL_MODE=true
/iris:plan "Build a REST API for task management"
/iris:execute
/iris:validate
/iris:document
```

## Permission Setup

Autopilot mode requires Claude Code to be launched with the `--dangerously-skip-permissions` flag:

```bash
claude --dangerously-skip-permissions
```

Without this flag, Claude will prompt you to approve every tool call (file writes, bash commands, etc.), making autonomous execution impossible.

### Quick Start

```bash
# Launch Claude Code with permissions flag
claude --dangerously-skip-permissions

# Run autopilot
/iris:autopilot "Build a REST API for task management"
```

### Optional: Environment Variable

Setting `CLAUDE_DANGEROUS_MODE=true` will suppress the startup warning:

```bash
export CLAUDE_DANGEROUS_MODE=true
claude --dangerously-skip-permissions
```

**⚠️ WARNING:** Only use autopilot in trusted development environments. If you start seeing permission prompts, you forgot the `--dangerously-skip-permissions` flag.

## Project Structure

When Iris runs, it creates the following structure:

```
your-project/
├── .tasks/
│   ├── iris_project.db      # SQLite database (all project state)
│   ├── backups/             # Automatic database backups
│   └── autopilot.log        # Execution logs
├── README.md                # Auto-generated project documentation
├── PROJECT_STATUS.md        # Human-readable progress summary
├── COMPLETION_REPORT.md     # Final KPIs (generated on completion)
└── [your application files]
```

### Database Schema

The SQLite database contains these tables:

- `milestones` - Project phases with status tracking
- `tasks` - Individual work items with dependencies
- `task_dependencies` - Relationships between tasks
- `technologies` - Technology stack decisions
- `project_metadata` - Configuration and analysis results
- `project_state` - Current execution state
- `deferred_features` - Features postponed for future work

## Interruption & Resume

Iris automatically detects and resumes interrupted projects. All progress is stored in the SQLite database, so if a session ends unexpectedly:

```bash
# Re-run autopilot - Iris detects existing project and resumes
/iris:autopilot "resume"
```

When resuming, Iris will:
- Detect existing tasks in `.tasks/iris_project.db`
- Display current progress
- Reset any interrupted (in-progress) tasks back to pending
- Skip planning and continue the execution loop

## Limitations

Iris operates within Claude Code's session constraints:

- **Context window:** ~200K tokens limits the conversation length
- **Session timeout:** Extended inactivity may end the session
- **No persistence:** Session state is lost on restart (database state persists)

For larger projects, consider:
- Breaking work into smaller PRDs
- Re-running `/iris:autopilot` to resume after interruptions
- Using debugging mode for troubleshooting specific issues

## Architecture

```
.claude/commands/iris/
├── autopilot.md              # Autonomous orchestrator
├── plan.md                   # Sprint planning
├── execute.md                # Task execution
├── validate.md               # Milestone validation
├── document.md               # Documentation generation
├── audit.md                  # Security analysis
├── help.md                   # Help documentation
└── utils/
    ├── database/
    │   ├── db_manager.py     # Database operations
    │   ├── schema.sql        # Table definitions
    │   └── backup_manager.py # Backup/restore
    ├── autopilot_init.py     # Autopilot initialization (project detection, permissions, resume)
    ├── iris_adaptive.py      # Complexity analysis
    ├── executor_cli.py       # Task management CLI
    ├── autonomous_validator.py # Validation system
    ├── document_generator.py   # README, status, and completion reports
    └── [other utilities]
```

## Status

This framework is experimental and under active development. It works for small to medium complexity prototypes but may encounter issues with:

- Very large or complex PRDs
- Projects requiring extensive external integrations
- Long-running sessions that exceed context limits

## Contributing

Contributions are welcome. Key areas:

- Complexity detection improvements (`iris_adaptive.py`)
- Additional validation checks (`autonomous_validator.py`)
- Database schema enhancements (`schema.sql`)
- Documentation and examples

## License

This project builds upon the Gustav Framework. Please respect the original licensing and attribution requirements.

## Acknowledgments

- [Dimitri Tholen](https://github.com/dimitritholen) for creating the Gustav Framework
- The Claude Code team at Anthropic

---

*Iris: Transforming requirements into prototypes, autonomously.*
