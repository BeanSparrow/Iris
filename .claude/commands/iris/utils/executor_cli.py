#!/usr/bin/env python3
"""
IRIS SQLite-based Executor CLI

Provides command-line interface for task execution using SQLite database
instead of JSON files. Maintains same API compatibility as original executor_cli.py.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

from database.db_manager import DatabaseManager


class ExecutorCLI:
    """SQLite-based executor maintaining original API"""
    
    def __init__(self, db_path: Optional[str] = None):
        try:
            self.db = DatabaseManager(db_path)
            
            # Verify database exists and is valid
            if not self.db.validate_schema():
                print("❌ Invalid database schema. Run database initialization.")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            sys.exit(1)
    
    def get_current_status(self) -> Dict:
        """Get current sprint execution status"""
        try:
            with self.db.get_connection() as conn:
                # Get current milestone info
                current_milestone_id = conn.execute(
                    "SELECT value FROM project_state WHERE key = 'current_milestone_id'"
                ).fetchone()
                
                current_milestone = None
                if current_milestone_id and current_milestone_id['value']:
                    current_milestone = conn.execute(
                        "SELECT * FROM milestones WHERE id = ?",
                        (current_milestone_id['value'],)
                    ).fetchone()
                
                # Get task statistics
                task_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_tasks,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks
                    FROM tasks
                """).fetchone()
                
                # Check if validation is required
                validation_required = False
                blocked_reason = None
                
                if current_milestone:
                    milestone_tasks = conn.execute(
                        "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM tasks WHERE milestone_id = ?",
                        (current_milestone['id'],)
                    ).fetchone()
                    
                    if milestone_tasks['total'] > 0 and milestone_tasks['completed'] == milestone_tasks['total']:
                        validation_required = True
                        blocked_reason = f"Milestone {current_milestone['id']} complete - validation required"
                
                return {
                    "sprint_status": "active" if task_stats['active_tasks'] > 0 else "pending",
                    "current_milestone": dict(current_milestone) if current_milestone else {},
                    "total_tasks": task_stats['total_tasks'],
                    "completed_tasks": task_stats['completed_tasks'],
                    "active_tasks": task_stats['active_tasks'],
                    "pending_tasks": task_stats['pending_tasks'],
                    "validation_required": validation_required,
                    "blocked_reason": blocked_reason
                }
                
        except Exception as e:
            print(f"❌ Failed to get current status: {e}")
            return {"error": str(e)}
    
    def get_next_task(self, task_id: Optional[str] = None) -> Dict:
        """Get next eligible task or specific task by ID"""
        try:
            with self.db.get_connection() as conn:
                if task_id:
                    # Get specific task
                    task = conn.execute(
                        "SELECT * FROM tasks WHERE id = ?", (task_id,)
                    ).fetchone()
                    
                    if not task:
                        return {"error": f"Task {task_id} not found"}
                    
                    # Check dependencies
                    dependencies_met = self._check_dependencies(conn, task_id)
                    if not dependencies_met["satisfied"]:
                        return {
                            "error": f"Task {task_id} dependencies not met",
                            "missing_dependencies": dependencies_met["missing"]
                        }
                    
                    return {"task": dict(task), "eligible": True}
                
                else:
                    # Find next eligible task in current milestone
                    current_milestone_id = conn.execute(
                        "SELECT value FROM project_state WHERE key = 'current_milestone_id'"
                    ).fetchone()
                    
                    if not current_milestone_id or not current_milestone_id['value']:
                        return {"error": "No current milestone set"}
                    
                    # Get next eligible task (no unmet dependencies)
                    next_task = conn.execute("""
                        SELECT t.* FROM tasks t
                        WHERE t.milestone_id = ?
                        AND t.status = 'pending'
                        AND NOT EXISTS (
                            SELECT 1 FROM task_dependencies td
                            JOIN tasks dep_task ON td.depends_on_task_id = dep_task.id
                            WHERE td.task_id = t.id 
                            AND dep_task.status != 'completed'
                        )
                        ORDER BY t.order_index
                        LIMIT 1
                    """, (current_milestone_id['value'],)).fetchone()
                    
                    if not next_task:
                        return {"error": "No eligible tasks found in current milestone"}
                    
                    return {"task": dict(next_task), "eligible": True}
                    
        except Exception as e:
            print(f"❌ Failed to get next task: {e}")
            return {"error": str(e)}
    
    def get_task_details(self, task_id: str) -> Dict:
        """Get comprehensive task details including scope boundaries"""
        try:
            with self.db.get_connection() as conn:
                # Get task info
                task = conn.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                
                if not task:
                    return {"error": f"Task {task_id} not found"}
                
                # Get milestone context
                milestone = conn.execute(
                    "SELECT * FROM milestones WHERE id = ?", (task['milestone_id'],)
                ).fetchone()
                
                # Get dependencies
                dependencies = self._check_dependencies(conn, task_id)
                
                # Get scope boundaries from task and guardrails
                scope_boundaries = self._get_scope_boundaries(conn, task_id)
                
                # Get tech compliance
                tech_compliance = self._check_tech_compliance(conn, dict(task))
                
                return {
                    "task": dict(task),
                    "dependencies": dependencies,
                    "milestone": dict(milestone) if milestone else None,
                    "scope_boundaries": scope_boundaries,
                    "tech_compliance": tech_compliance
                }
                
        except Exception as e:
            print(f"❌ Failed to get task details: {e}")
            return {"error": str(e)}
    
    def start_task(self, task_id: str) -> Dict:
        """Mark task as in-progress and update timestamps"""
        try:
            # Create backup and execute in transaction
            backup_path = self.db.backup_database()
            
            def start_task_operation(conn):
                # Check if task exists and is eligible
                task = conn.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                
                if not task:
                    raise Exception(f"Task {task_id} not found")
                
                # Check dependencies
                dependencies_status = self._check_dependencies(conn, task_id)
                if not dependencies_status["satisfied"]:
                    raise Exception(f"Cannot start task - dependencies not met: {dependencies_status['missing']}")
                
                # Update task status
                conn.execute("""
                    UPDATE tasks 
                    SET status = 'in_progress', started_at = datetime('now')
                    WHERE id = ?
                """, (task_id,))
                
                # Log execution attempt
                conn.execute("""
                    INSERT INTO task_executions 
                    (task_id, execution_status, autopilot_mode)
                    VALUES (?, 'started', ?)
                """, (task_id, False))  # Manual mode by default
                
                return {"success": True, "task_id": task_id, "status": "in_progress"}
            
            success, results = self.db.execute_transaction([start_task_operation])
            
            if success:
                return results[0]
            else:
                # Restore backup on failure
                self.db.restore_from_backup(backup_path)
                return {"error": "Failed to start task - transaction rolled back"}
                
        except Exception as e:
            print(f"❌ Failed to start task: {e}")
            return {"error": str(e)}
    
    def complete_task(self, task_id: str) -> Dict:
        """Mark task as complete and update milestone progress"""
        try:
            # Create backup and execute in transaction
            backup_path = self.db.backup_database()
            
            def complete_task_operation(conn):
                # Check if task exists
                task = conn.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                
                if not task:
                    raise Exception(f"Task {task_id} not found")
                
                # Update task status
                conn.execute("""
                    UPDATE tasks 
                    SET status = 'completed', 
                        completed_at = datetime('now'),
                        duration_minutes = CASE 
                            WHEN started_at IS NOT NULL 
                            THEN CAST((julianday('now') - julianday(started_at)) * 1440 AS INTEGER)
                            ELSE NULL
                        END
                    WHERE id = ?
                """, (task_id,))
                
                # Update task execution log
                conn.execute("""
                    UPDATE task_executions 
                    SET execution_status = 'completed', completed_at = datetime('now')
                    WHERE task_id = ? AND execution_status = 'started'
                """, (task_id,))
                
                # Check if milestone is complete
                milestone_id = task['milestone_id']
                milestone_tasks = conn.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks
                    FROM tasks 
                    WHERE milestone_id = ?
                """, (milestone_id,)).fetchone()
                
                milestone_complete = (milestone_tasks['completed_tasks'] == milestone_tasks['total_tasks'])
                
                result = {
                    "success": True, 
                    "task_id": task_id, 
                    "status": "completed",
                    "milestone_complete": milestone_complete
                }
                
                if milestone_complete:
                    # Mark milestone as requiring validation
                    conn.execute("""
                        UPDATE milestones 
                        SET status = 'completed', validation_required = 1, completed_at = datetime('now')
                        WHERE id = ?
                    """, (milestone_id,))
                    
                    result.update({
                        "milestone_id": milestone_id,
                        "validation_required": True
                    })
                
                return result
            
            success, results = self.db.execute_transaction([complete_task_operation])
            
            if success:
                return results[0]
            else:
                # Restore backup on failure
                self.db.restore_from_backup(backup_path)
                return {"error": "Failed to complete task - transaction rolled back"}
                
        except Exception as e:
            print(f"❌ Failed to complete task: {e}")
            return {"error": str(e)}
    
    def validate_dependencies(self, task_id: str) -> Dict:
        """Check if task dependencies are satisfied"""
        try:
            with self.db.get_connection() as conn:
                return self._check_dependencies(conn, task_id)
        except Exception as e:
            print(f"❌ Failed to validate dependencies: {e}")
            return {"error": str(e)}
    
    def check_scope_compliance(self, task_id: str) -> Dict:
        """Validate task against scope boundaries"""
        try:
            with self.db.get_connection() as conn:
                return self._get_scope_boundaries(conn, task_id)
        except Exception as e:
            print(f"❌ Failed to check scope compliance: {e}")
            return {"error": str(e)}
    
    def get_milestone_status(self, milestone_id: str) -> Dict:
        """Get milestone completion status"""
        try:
            with self.db.get_connection() as conn:
                # Get milestone info
                milestone = conn.execute(
                    "SELECT * FROM milestones WHERE id = ?", (milestone_id,)
                ).fetchone()
                
                if not milestone:
                    return {"error": f"Milestone {milestone_id} not found"}
                
                # Get task statistics for milestone
                task_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                        GROUP_CONCAT(CASE WHEN status = 'completed' THEN id END) as completed_task_ids,
                        GROUP_CONCAT(CASE WHEN status != 'completed' THEN id END) as pending_task_ids
                    FROM tasks 
                    WHERE milestone_id = ?
                """, (milestone_id,)).fetchone()
                
                total_tasks = task_stats['total_tasks']
                completed_tasks = task_stats['completed_tasks']
                completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                return {
                    "milestone_id": milestone_id,
                    "milestone_name": milestone['name'],
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "pending_tasks": task_stats['pending_tasks'],
                    "completion_percentage": round(completion_percentage, 1),
                    "is_complete": completed_tasks == total_tasks,
                    "completed_task_ids": task_stats['completed_task_ids'].split(',') if task_stats['completed_task_ids'] else [],
                    "pending_task_ids": task_stats['pending_task_ids'].split(',') if task_stats['pending_task_ids'] else []
                }
                
        except Exception as e:
            print(f"❌ Failed to get milestone status: {e}")
            return {"error": str(e)}
    
    def _check_dependencies(self, conn, task_id: str) -> Dict:
        """Check if all task dependencies are satisfied"""
        dependencies = conn.execute("""
            SELECT depends_on_task_id 
            FROM task_dependencies 
            WHERE task_id = ?
        """, (task_id,)).fetchall()
        
        missing = []
        
        for dep_row in dependencies:
            dep_id = dep_row['depends_on_task_id']
            dep_task = conn.execute(
                "SELECT status FROM tasks WHERE id = ?", (dep_id,)
            ).fetchone()
            
            if not dep_task or dep_task['status'] != 'completed':
                missing.append(dep_id)
        
        return {
            "satisfied": len(missing) == 0,
            "missing": missing,
            "total_dependencies": len(dependencies)
        }
    
    def _get_scope_boundaries(self, conn, task_id: str) -> Dict:
        """Get scope boundaries for task from task data and guardrails"""
        task = conn.execute(
            "SELECT scope_boundaries, max_file_changes FROM tasks WHERE id = ?", 
            (task_id,)
        ).fetchone()
        
        if not task:
            return {"error": "Task not found"}
        
        # Parse scope boundaries JSON if exists
        scope_boundaries = {}
        if task['scope_boundaries']:
            try:
                scope_boundaries = json.loads(task['scope_boundaries'])
            except json.JSONDecodeError:
                scope_boundaries = {}
        
        # Get forbidden patterns from guardrails
        forbidden_patterns = conn.execute("""
            SELECT rule_value 
            FROM guardrails 
            WHERE rule_type = 'forbidden_keyword' AND is_active = 1
        """).fetchall()
        
        # Get allowed technologies
        allowed_technologies = conn.execute(
            "SELECT name FROM technologies"
        ).fetchall()
        
        return {
            "must_implement": scope_boundaries.get("must_implement", []),
            "must_not_implement": scope_boundaries.get("must_not_implement", []),
            "max_files": task['max_file_changes'],
            "forbidden_patterns": [row['rule_value'] for row in forbidden_patterns],
            "allowed_technologies": [row['name'] for row in allowed_technologies]
        }
    
    def _check_tech_compliance(self, conn, task: Dict) -> Dict:
        """Check if task complies with approved tech stack"""
        # Get allowed technologies
        allowed_tech = conn.execute(
            "SELECT name FROM technologies"
        ).fetchall()
        allowed_stack = {row['name'] for row in allowed_tech}
        
        # Extract technologies from task (this would need enhancement based on task content)
        task_technologies = set()
        
        # For now, assume compliance (would need more sophisticated analysis)
        return {
            "compliant": True,
            "non_compliant_technologies": [],
            "allowed_technologies": list(allowed_stack),
            "task_technologies": list(task_technologies)
        }


def main():
    """CLI interface matching original executor_cli.py"""
    parser = argparse.ArgumentParser(description='IRIS SQLite Executor CLI')
    parser.add_argument('action', choices=[
        'get-current-status',
        'get-next-task', 
        'get-task-details',
        'start-task',
        'complete-task',
        'validate-dependencies',
        'check-scope-compliance',
        'get-milestone-status'
    ])
    parser.add_argument('task_id', nargs='?', help='Task ID for task-specific operations')
    parser.add_argument('--db-path', help='Path to database file')
    
    args = parser.parse_args()
    
    try:
        executor = ExecutorCLI(args.db_path)
        
        if args.action == 'get-current-status':
            result = executor.get_current_status()
            
        elif args.action == 'get-next-task':
            result = executor.get_next_task(args.task_id)
            
        elif args.action == 'get-task-details':
            if not args.task_id:
                print("❌ Task ID required for get-task-details")
                sys.exit(1)
            result = executor.get_task_details(args.task_id)
            
        elif args.action == 'start-task':
            if not args.task_id:
                print("❌ Task ID required for start-task")
                sys.exit(1)
            result = executor.start_task(args.task_id)
            
        elif args.action == 'complete-task':
            if not args.task_id:
                print("❌ Task ID required for complete-task")
                sys.exit(1)
            result = executor.complete_task(args.task_id)
            
        elif args.action == 'validate-dependencies':
            if not args.task_id:
                print("❌ Task ID required for validate-dependencies")
                sys.exit(1)
            result = executor.validate_dependencies(args.task_id)
            
        elif args.action == 'check-scope-compliance':
            if not args.task_id:
                print("❌ Task ID required for check-scope-compliance")
                sys.exit(1)
            result = executor.check_scope_compliance(args.task_id)
            
        elif args.action == 'get-milestone-status':
            if not args.task_id:  # Using task_id parameter for milestone_id
                print("❌ Milestone ID required for get-milestone-status")
                sys.exit(1)
            result = executor.get_milestone_status(args.task_id)
        
        print(json.dumps(result, indent=2, default=str))
        
        # Exit with error code if result contains an error
        if isinstance(result, dict) and "error" in result:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Executor CLI error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()