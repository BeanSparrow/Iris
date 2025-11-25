#!/usr/bin/env python3
"""
IRIS Permissions Checker - Informational check for autopilot requirements
Displays requirements and warnings for autonomous operation
"""

import os
import json
from pathlib import Path
from typing import Tuple, Dict, Optional

class PermissionsChecker:
    """
    Checks for user acknowledgment of autopilot requirements and displays
    informational warnings about Claude Code launch requirements.

    NOTE: This checker cannot verify if Claude Code was actually launched with
    --dangerously-skip-permissions. It only checks for user acknowledgment
    via environment variable and displays appropriate warnings.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or self._find_project_root()

    def _find_project_root(self) -> Path:
        """Walk up from cwd to find project root (contains .git or .iris)"""
        current = Path.cwd()

        # First pass: look for definitive project markers (.git or .iris)
        while current != current.parent:
            if (current / ".git").exists() or (current / ".iris").exists():
                return current
            current = current.parent

        # Second pass: look for .tasks but NOT inside .claude/commands (framework internals)
        current = Path.cwd()
        while current != current.parent:
            if (current / ".tasks").exists() and ".claude/commands" not in str(current):
                return current
            current = current.parent

        # Fallback to cwd if no markers found
        return Path.cwd()

    def check_autopilot_ready(self) -> Tuple[bool, str, Dict]:
        """
        Check autopilot readiness and display appropriate warnings.

        Always returns True (proceeds) but shows different messages based on
        whether the user has set the acknowledgment environment variable.

        Returns:
            (ready, message, details) - Always True, with appropriate warning message
        """
        details = {
            "env_var_set": False,
            "warnings": []
        }

        # Check for environment variable acknowledgment
        env_vars = ["CLAUDE_DANGEROUS_MODE", "IRIS_AUTOPILOT_ENABLED"]

        for var in env_vars:
            value = os.getenv(var)
            if value and value.lower() in ["true", "1", "yes", "enabled"]:
                details["env_var_set"] = True
                details["env_var"] = var
                return True, self._get_ready_message(), details

        # No env var set - still proceed but with stronger warning
        return True, self._get_warning_message(), details

    def _get_ready_message(self) -> str:
        """Message when user has acknowledged requirements"""
        return """
════════════════════════════════════════════════════════════════
  ✅ IRIS AUTOPILOT - Ready to proceed
════════════════════════════════════════════════════════════════

⚠️  IMPORTANT REMINDER:
    Autopilot requires Claude Code to be launched with:

    claude --dangerously-skip-permissions

    If you did NOT use this flag, you will be prompted to approve
    EVERY tool call, making autonomous execution impossible.

    If you start seeing permission prompts, press Ctrl+C and
    restart Claude Code with the flag above.

════════════════════════════════════════════════════════════════
"""

    def _get_warning_message(self) -> str:
        """Warning message when proceeding without env var acknowledgment"""
        return """
════════════════════════════════════════════════════════════════
  ⚠️  IRIS AUTOPILOT - IMPORTANT
════════════════════════════════════════════════════════════════

  Autopilot requires Claude Code to be launched with:

      claude --dangerously-skip-permissions

  If you did NOT use this flag, you will be prompted to approve
  EVERY tool call, making autonomous execution impossible.

  If you start seeing permission prompts:
    1. Press Ctrl+C to stop
    2. Exit Claude Code
    3. Restart with: claude --dangerously-skip-permissions

════════════════════════════════════════════════════════════════
  Proceeding with autopilot...
════════════════════════════════════════════════════════════════
"""

    def get_permission_instructions(self) -> str:
        """Get detailed instructions for enabling permissions"""
        return """
# IRIS Autopilot Setup Guide

## Requirements

IRIS Autopilot requires TWO things to function properly:

### 1. Claude Code Launch Flag
Claude Code must be started with the --dangerously-skip-permissions flag:

    claude --dangerously-skip-permissions

This flag allows Claude to execute tools (file writes, bash commands, etc.)
without prompting you for approval each time. Without it, autopilot cannot
run autonomously.

### 2. Environment Variable (Acknowledgment)
Set this environment variable before starting Claude:

    export CLAUDE_DANGEROUS_MODE=true

This serves as your acknowledgment that you understand:
- Autopilot will modify files without asking
- Autopilot will run shell commands without asking
- Autopilot will install packages without asking
- You should only run this in trusted environments

## Complete Setup

    # Set the acknowledgment variable
    export CLAUDE_DANGEROUS_MODE=true

    # Launch Claude Code with permissions flag
    claude --dangerously-skip-permissions

    # Now run autopilot
    /iris:autopilot "Build a REST API for task management"

## What Happens During Autopilot

1. **Planning Phase**: Analyzes your requirements, determines complexity,
   researches technologies, creates milestones and tasks

2. **Execution Phase**: Implements each task using TDD methodology,
   writes code, runs tests, validates results

3. **Validation Phase**: Verifies the application works, runs quality
   checks, generates completion report

## Safety Features

- All progress saved to SQLite database (survives interruptions)
- Automatic backups before major operations
- Press Ctrl+C anytime to stop execution
- Resume with /iris:autopilot "resume"

## Monitoring

Watch progress in real-time:

    # In another terminal
    watch cat PROJECT_STATUS.md

    # Or check the database
    sqlite3 .tasks/iris_project.db "SELECT * FROM tasks"

## Troubleshooting

**Getting permission prompts?**
You didn't launch Claude with --dangerously-skip-permissions.
Press Ctrl+C, exit Claude, and restart with the flag.

**Autopilot won't start?**
Set the environment variable: export CLAUDE_DANGEROUS_MODE=true

**Want to stop?**
Press Ctrl+C. Progress is saved. Resume anytime with /iris:autopilot "resume"
"""


def check_permissions() -> Tuple[bool, str, Dict]:
    """
    Convenience function to check autopilot readiness

    Returns:
        (ready, message, details)
    """
    checker = PermissionsChecker()
    return checker.check_autopilot_ready()


def require_permissions() -> bool:
    """
    Check permissions and show requirements if not ready

    Returns:
        True if ready to proceed
    """
    ready, message, details = check_permissions()
    print(message)
    return ready


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--instructions":
        checker = PermissionsChecker()
        print(checker.get_permission_instructions())
        sys.exit(0)

    ready, message, details = check_permissions()
    print(message)

    # Always exit 0 - we proceed with warning
    sys.exit(0)