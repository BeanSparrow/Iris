#!/usr/bin/env python3
"""
IRIS Autopilot Initialization
Handles all startup logic: project detection, permissions, resume state
Outputs JSON for consumption by autopilot.md
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def find_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Walk up from start_path to find project root.
    Looks for .git or .iris as definitive markers.
    Falls back to .tasks if not inside .claude/commands.
    """
    current = start_path or Path.cwd()

    # First pass: look for .git or .iris (definitive project markers)
    check = current
    while check != check.parent:
        if (check / ".git").exists() or (check / ".iris").exists():
            return check
        check = check.parent

    # Second pass: look for .tasks but not inside framework directory
    check = current
    while check != check.parent:
        if (check / ".tasks").exists() and ".claude/commands" not in str(check):
            return check
        check = check.parent

    # Fallback to start path
    return start_path or Path.cwd()


def find_iris_directory(project_root: Path) -> Optional[Path]:
    """
    Find the IRIS commands directory.
    Checks project-local first, then global installation.
    """
    # Project-local installation
    local_iris = project_root / ".claude" / "commands" / "iris"
    if local_iris.exists() and (local_iris / "utils").exists():
        return local_iris

    # Global installation
    global_iris = Path.home() / ".claude" / "commands" / "iris"
    if global_iris.exists() and (global_iris / "utils").exists():
        return global_iris

    return None


def check_permissions() -> Dict[str, Any]:
    """
    Check if user has acknowledged autopilot requirements.
    Always proceeds but returns different status based on env var.
    """
    env_vars = ["CLAUDE_DANGEROUS_MODE", "IRIS_AUTOPILOT_ENABLED"]

    for var in env_vars:
        value = os.getenv(var)
        if value and value.lower() in ["true", "1", "yes", "enabled"]:
            return {
                "acknowledged": True,
                "env_var": var,
                "message": "ready"
            }

    return {
        "acknowledged": False,
        "env_var": None,
        "message": "warning"
    }


def check_resume_state(project_root: Path, iris_dir: Path) -> Dict[str, Any]:
    """
    Check if this is a new project or resuming existing work.
    """
    # Add utils to path for database access
    utils_path = iris_dir / "utils"
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))

    try:
        from database.db_manager import DatabaseManager

        db = DatabaseManager(project_root)
        with db.get_connection() as conn:
            # Check for existing tasks
            tasks = conn.execute('SELECT COUNT(*) as total FROM tasks').fetchone()
            completed = conn.execute(
                "SELECT COUNT(*) as done FROM tasks WHERE status = 'completed'"
            ).fetchone()
            in_progress = conn.execute(
                "SELECT COUNT(*) as active FROM tasks WHERE status = 'in_progress'"
            ).fetchone()

            total = tasks['total']
            done = completed['done']
            active = in_progress['active']

            if total > 0:
                pct = int((done / total) * 100) if total > 0 else 0
                return {
                    "is_resume": True,
                    "total_tasks": total,
                    "completed_tasks": done,
                    "in_progress_tasks": active,
                    "progress_percent": pct
                }
            else:
                return {
                    "is_resume": False,
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "progress_percent": 0
                }

    except Exception as e:
        # Database doesn't exist or error - treat as new project
        return {
            "is_resume": False,
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "progress_percent": 0,
            "error": str(e)
        }


def reset_interrupted_tasks(project_root: Path, iris_dir: Path) -> int:
    """
    Reset any in_progress tasks back to pending (they were interrupted).
    Returns count of reset tasks.
    """
    utils_path = iris_dir / "utils"
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))

    try:
        from database.db_manager import DatabaseManager

        db = DatabaseManager(project_root)
        with db.get_connection() as conn:
            stuck = conn.execute(
                "SELECT COUNT(*) as c FROM tasks WHERE status = 'in_progress'"
            ).fetchone()['c']

            if stuck > 0:
                conn.execute(
                    "UPDATE tasks SET status = 'pending', started_at = NULL "
                    "WHERE status = 'in_progress'"
                )
                conn.commit()

            return stuck

    except Exception:
        return 0


def print_banner():
    """Print the IRIS ASCII banner."""
    print("")
    print("●")
    print("   ██ ██████  ██ ███████   ")
    print("   ██ ██   ██ ██ ██        ")
    print("   ██ ██████  ██ ███████   ")
    print("   ██ ██   ██ ██      ██   ")
    print("   ██ ██   ██ ██ ███████   ")
    print("")


def print_permissions_message(permissions: Dict[str, Any]):
    """Print appropriate permissions message."""
    if permissions["acknowledged"]:
        print("════════════════════════════════════════════════════════════════")
        print("  ✅ IRIS AUTOPILOT - Ready to proceed")
        print("════════════════════════════════════════════════════════════════")
        print("")
        print("⚠️  IMPORTANT REMINDER:")
        print("    Autopilot requires Claude Code to be launched with:")
        print("")
        print("    claude --dangerously-skip-permissions")
        print("")
        print("    If you did NOT use this flag, you will be prompted to approve")
        print("    EVERY tool call, making autonomous execution impossible.")
        print("")
        print("    If you start seeing permission prompts, press Ctrl+C and")
        print("    restart Claude Code with the flag above.")
        print("")
        print("════════════════════════════════════════════════════════════════")
    else:
        print("════════════════════════════════════════════════════════════════")
        print("  ⚠️  IRIS AUTOPILOT - IMPORTANT")
        print("════════════════════════════════════════════════════════════════")
        print("")
        print("  Autopilot requires Claude Code to be launched with:")
        print("")
        print("      claude --dangerously-skip-permissions")
        print("")
        print("  If you did NOT use this flag, you will be prompted to approve")
        print("  EVERY tool call, making autonomous execution impossible.")
        print("")
        print("  If you start seeing permission prompts:")
        print("    1. Press Ctrl+C to stop")
        print("    2. Exit Claude Code")
        print("    3. Restart with: claude --dangerously-skip-permissions")
        print("")
        print("════════════════════════════════════════════════════════════════")
        print("  Proceeding with autopilot...")
        print("════════════════════════════════════════════════════════════════")
    print("")


def print_resume_status(resume_state: Dict[str, Any], project_root: Path):
    """Print resume or new project status."""
    if resume_state["is_resume"]:
        print("────────────────────────────────────────────────────────")
        print("📂 EXISTING PROJECT DETECTED - RESUMING")
        print("────────────────────────────────────────────────────────")
        print(f"📊 Progress: {resume_state['completed_tasks']}/{resume_state['total_tasks']} "
              f"tasks completed ({resume_state['progress_percent']}%)")
        print(f"🔄 Active tasks: {resume_state['in_progress_tasks']}")
        print(f"⏰ Resuming: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("────────────────────────────────────────────────────────")
        print("")
        print("⏭️ Skipping planning phase - jumping to execution loop...")
        print("")
    else:
        print("────────────────────────────────────────────────────────")
        print("📁 NEW PROJECT - Starting fresh")
        print("────────────────────────────────────────────────────────")
        print(f"📁 Project: {project_root}")
        print(f"📊 Status: PROJECT_STATUS.md")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("────────────────────────────────────────────────────────")
        print("")


def main():
    """
    Main initialization routine.
    Can be called with --json flag for machine-readable output,
    or without for human-readable output with side effects.
    """
    json_mode = "--json" in sys.argv

    # Find project root and IRIS directory
    project_root = find_project_root()
    iris_dir = find_iris_directory(project_root)

    if iris_dir is None:
        if json_mode:
            print(json.dumps({
                "success": False,
                "error": "IRIS directory not found",
                "project_root": str(project_root)
            }))
        else:
            print("❌ ERROR: IRIS directory not found")
            print(f"   Project root: {project_root}")
            print("   Check .claude/commands/iris installation")
        sys.exit(1)

    # Check permissions
    permissions = check_permissions()

    # Check resume state
    resume_state = check_resume_state(project_root, iris_dir)

    # Reset interrupted tasks if resuming
    reset_count = 0
    if resume_state["is_resume"] and resume_state["in_progress_tasks"] > 0:
        reset_count = reset_interrupted_tasks(project_root, iris_dir)

    # Build result
    result = {
        "success": True,
        "project_root": str(project_root),
        "iris_dir": str(iris_dir),
        "permissions": permissions,
        "resume_state": resume_state,
        "reset_tasks": reset_count,
        "skip_planning": resume_state["is_resume"]
    }

    if json_mode:
        # Machine-readable output
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output with visual formatting
        print_banner()
        print("           🚀 IRIS AUTOPILOT MODE ACTIVATED")
        print("           =====================================")
        print("")

        print_permissions_message(permissions)
        print_resume_status(resume_state, project_root)

        if reset_count > 0:
            print(f"🔧 Reset {reset_count} interrupted task(s) to pending")
            print("")

        # Also output key variables for bash to capture if needed
        print(f"PROJECT_ROOT={project_root}")
        print(f"IRIS_DIR={iris_dir}")
        print(f"SKIP_PLANNING={'true' if resume_state['is_resume'] else 'false'}")

    sys.exit(0)


if __name__ == "__main__":
    main()
