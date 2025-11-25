#!/usr/bin/env python3
"""
IRIS Continuous Executor CLI Helper

Provides database query utilities for the autopilot execution loop.
This is NOT a subprocess spawner - it's a helper tool that Claude calls
via bash to query and update task state in the database.

The actual task execution is done by Claude directly through its tools.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager


class ExecutorCLI:
    """CLI helper for continuous execution queries"""

    def __init__(self, db_path: Optional[str] = None):
        self.db = DatabaseManager(db_path)

    def get_next_task(self, milestone_id: Optional[str] = None) -> Dict:
        """Get the next eligible task for execution"""
        try:
            with self.db.get_connection() as conn:
                # Get or set current milestone
                if not milestone_id:
                    current = conn.execute(
                        "SELECT value FROM project_state WHERE key = 'current_milestone_id'"
                    ).fetchone()

                    if not current or not current['value']:
                        # Set first pending milestone as current
                        first = conn.execute(
                            "SELECT id FROM milestones WHERE status = 'pending' ORDER BY order_index LIMIT 1"
                        ).fetchone()

                        if first:
                            conn.execute(
                                "UPDATE project_state SET value = ? WHERE key = 'current_milestone_id'",
                                (first['id'],)
                            )
                            conn.commit()
                            milestone_id = first['id']
                        else:
                            # Check if all complete
                            remaining = conn.execute(
                                "SELECT COUNT(*) as c FROM tasks WHERE status != 'completed'"
                            ).fetchone()['c']

                            if remaining == 0:
                                return {'status': 'all_complete', 'message': 'All tasks completed'}
                            return {'status': 'error', 'message': 'No pending milestones found'}
                    else:
                        milestone_id = current['value']

                # Get next pending task with satisfied dependencies
                task = conn.execute('''
                    SELECT t.id, t.title, t.description, t.milestone_id,
                           m.name as milestone_name, t.order_index
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
                    return {
                        'status': 'found',
                        'task': {
                            'id': task['id'],
                            'title': task['title'],
                            'description': task['description'],
                            'milestone_id': task['milestone_id'],
                            'milestone_name': task['milestone_name']
                        }
                    }

                # No task found - check if milestone complete
                remaining = conn.execute(
                    "SELECT COUNT(*) as c FROM tasks WHERE milestone_id = ? AND status != 'completed'",
                    (milestone_id,)
                ).fetchone()['c']

                if remaining == 0:
                    # Mark milestone complete
                    conn.execute(
                        "UPDATE milestones SET status = 'completed', completed_at = datetime('now') WHERE id = ?",
                        (milestone_id,)
                    )

                    # Get next milestone
                    next_ms = conn.execute(
                        "SELECT id FROM milestones WHERE status = 'pending' ORDER BY order_index LIMIT 1"
                    ).fetchone()

                    if next_ms:
                        conn.execute(
                            "UPDATE project_state SET value = ? WHERE key = 'current_milestone_id'",
                            (next_ms['id'],)
                        )
                        conn.commit()
                        return {
                            'status': 'milestone_complete',
                            'completed_milestone': milestone_id,
                            'next_milestone': next_ms['id']
                        }
                    else:
                        conn.commit()
                        return {'status': 'all_complete', 'message': 'All milestones completed'}

                return {'status': 'blocked', 'message': 'Tasks blocked by dependencies'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def start_task(self, task_id: str) -> Dict:
        """Mark a task as in-progress"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('''
                    UPDATE tasks
                    SET status = 'in_progress', started_at = datetime('now')
                    WHERE id = ?
                ''', (task_id,))
                conn.commit()

                return {'status': 'success', 'task_id': task_id, 'message': 'Task started'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def complete_task(self, task_id: str) -> Dict:
        """Mark a task as completed"""
        try:
            with self.db.get_connection() as conn:
                # Update task status
                conn.execute('''
                    UPDATE tasks
                    SET status = 'completed',
                        completed_at = datetime('now'),
                        duration_minutes = CAST(
                            (julianday('now') - julianday(started_at)) * 24 * 60 AS INTEGER
                        )
                    WHERE id = ?
                ''', (task_id,))

                # Get milestone info
                task = conn.execute(
                    "SELECT milestone_id FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()

                milestone_id = task['milestone_id'] if task else None

                # Check if milestone is complete
                milestone_complete = False
                if milestone_id:
                    remaining = conn.execute(
                        "SELECT COUNT(*) as c FROM tasks WHERE milestone_id = ? AND status != 'completed'",
                        (milestone_id,)
                    ).fetchone()['c']

                    if remaining == 0:
                        conn.execute(
                            "UPDATE milestones SET status = 'completed', completed_at = datetime('now') WHERE id = ?",
                            (milestone_id,)
                        )
                        milestone_complete = True

                conn.commit()

                return {
                    'status': 'success',
                    'task_id': task_id,
                    'milestone_complete': milestone_complete,
                    'milestone_id': milestone_id
                }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_progress(self) -> Dict:
        """Get overall execution progress"""
        try:
            with self.db.get_connection() as conn:
                total_tasks = conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()['c']
                completed_tasks = conn.execute(
                    "SELECT COUNT(*) as c FROM tasks WHERE status = 'completed'"
                ).fetchone()['c']
                in_progress = conn.execute(
                    "SELECT COUNT(*) as c FROM tasks WHERE status = 'in_progress'"
                ).fetchone()['c']

                total_milestones = conn.execute("SELECT COUNT(*) as c FROM milestones").fetchone()['c']
                completed_milestones = conn.execute(
                    "SELECT COUNT(*) as c FROM milestones WHERE status = 'completed'"
                ).fetchone()['c']

                progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

                return {
                    'status': 'success',
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'in_progress_tasks': in_progress,
                    'pending_tasks': total_tasks - completed_tasks - in_progress,
                    'total_milestones': total_milestones,
                    'completed_milestones': completed_milestones,
                    'progress_percentage': progress_pct
                }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_current_task(self) -> Dict:
        """Get the currently in-progress task"""
        try:
            with self.db.get_connection() as conn:
                task = conn.execute('''
                    SELECT t.id, t.title, t.description, t.milestone_id,
                           m.name as milestone_name, t.started_at
                    FROM tasks t
                    JOIN milestones m ON t.milestone_id = m.id
                    WHERE t.status = 'in_progress'
                    LIMIT 1
                ''').fetchone()

                if task:
                    return {
                        'status': 'found',
                        'task': {
                            'id': task['id'],
                            'title': task['title'],
                            'description': task['description'],
                            'milestone_id': task['milestone_id'],
                            'milestone_name': task['milestone_name'],
                            'started_at': task['started_at']
                        }
                    }

                return {'status': 'none', 'message': 'No task currently in progress'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def is_all_complete(self) -> bool:
        """Check if all tasks are completed"""
        try:
            with self.db.get_connection() as conn:
                remaining = conn.execute(
                    "SELECT COUNT(*) as c FROM tasks WHERE status != 'completed'"
                ).fetchone()['c']
                return remaining == 0
        except:
            return False


def main():
    parser = argparse.ArgumentParser(
        description='IRIS Continuous Executor CLI Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Commands:
  get-next-task          Get the next eligible task for execution
  start-task <id>        Mark a task as in-progress
  complete-task <id>     Mark a task as completed
  get-progress           Get overall execution progress
  get-current-task       Get the currently executing task
  is-complete            Check if all tasks are done (returns 0 or 1)

Examples:
  python3 continuous_executor.py get-next-task
  python3 continuous_executor.py start-task T-AUTH-1
  python3 continuous_executor.py complete-task T-AUTH-1
  python3 continuous_executor.py get-progress
'''
    )

    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('task_id', nargs='?', help='Task ID (for start-task/complete-task)')
    parser.add_argument('--db-path', help='Path to database file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = ExecutorCLI(args.db_path)

    if args.command == 'get-next-task':
        result = cli.get_next_task()
        print(json.dumps(result, indent=2))

    elif args.command == 'start-task':
        if not args.task_id:
            print(json.dumps({'status': 'error', 'message': 'Task ID required'}))
            sys.exit(1)
        result = cli.start_task(args.task_id)
        print(json.dumps(result, indent=2))

    elif args.command == 'complete-task':
        if not args.task_id:
            print(json.dumps({'status': 'error', 'message': 'Task ID required'}))
            sys.exit(1)
        result = cli.complete_task(args.task_id)
        print(json.dumps(result, indent=2))

    elif args.command == 'get-progress':
        result = cli.get_progress()
        print(json.dumps(result, indent=2))

    elif args.command == 'get-current-task':
        result = cli.get_current_task()
        print(json.dumps(result, indent=2))

    elif args.command == 'is-complete':
        if cli.is_all_complete():
            print('true')
            sys.exit(0)
        else:
            print('false')
            sys.exit(1)

    else:
        print(json.dumps({'status': 'error', 'message': f'Unknown command: {args.command}'}))
        sys.exit(1)


if __name__ == "__main__":
    main()
