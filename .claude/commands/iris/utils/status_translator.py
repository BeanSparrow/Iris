#!/usr/bin/env python3
"""
IRIS Status Translator

Converts SQLite database state into human-readable markdown status files.
Replaces the technical writer with a focused translation system.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from database.db_manager import DatabaseManager


@dataclass
class TaskStatus:
    id: str
    title: str
    status: str
    milestone_name: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_minutes: Optional[int] = None


@dataclass 
class MilestoneProgress:
    id: str
    name: str
    status: str
    total_tasks: int
    completed_tasks: int
    progress_percentage: float
    validation_required: bool = False


class StatusTranslator:
    """Translates database state to human-readable markdown"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.output_file = "PROJECT_STATUS.md"
    
    def generate_project_status(self) -> str:
        """Generate complete project status markdown"""
        
        with self.db.get_connection() as conn:
            # Get overall project stats
            project_stats = self._get_project_statistics(conn)
            
            # Get milestone progress
            milestone_progress = self._get_milestone_progress(conn)
            
            # Get current task info
            current_task = self._get_current_task(conn)
            
            # Get next eligible tasks
            next_tasks = self._get_next_eligible_tasks(conn)
            
            # Get validation status
            validation_status = self._get_validation_status(conn)
            
            # Generate markdown
            return self._format_markdown(
                project_stats, milestone_progress, current_task, 
                next_tasks, validation_status
            )
    
    def update_status_file(self, output_path: Optional[str] = None) -> bool:
        """Update the PROJECT_STATUS.md file"""
        if output_path is None:
            # Output to project root, not .tasks/
            output_path = self.db.project_root / self.output_file
        else:
            output_path = Path(output_path)
        
        try:
            markdown_content = self.generate_project_status()
            
            with open(output_path, 'w') as f:
                f.write(markdown_content)
            
            print(f"✅ Status updated: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update status file: {e}")
            return False
    
    def _get_project_statistics(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get overall project statistics"""
        
        # Task statistics
        task_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_tasks,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                COUNT(CASE WHEN status = 'blocked' THEN 1 END) as blocked_tasks
            FROM tasks
        """).fetchone()
        
        # Milestone statistics
        milestone_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_milestones,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_milestones,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_milestones
            FROM milestones
        """).fetchone()
        
        # Calculate progress percentage
        total = task_stats['total_tasks']
        completed = task_stats['completed_tasks']
        progress_percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            'tasks': dict(task_stats),
            'milestones': dict(milestone_stats),
            'progress_percentage': round(progress_percentage, 1),
            'generated_at': datetime.now().isoformat(),
            'database_path': str(self.db.db_path)
        }
    
    def _get_milestone_progress(self, conn: sqlite3.Connection) -> List[MilestoneProgress]:
        """Get detailed milestone progress"""
        
        milestones_data = conn.execute("""
            SELECT 
                m.id,
                m.name,
                m.status,
                m.validation_required,
                COUNT(t.id) as total_tasks,
                COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
            FROM milestones m
            LEFT JOIN tasks t ON m.id = t.milestone_id
            GROUP BY m.id, m.name, m.status, m.validation_required
            ORDER BY m.order_index
        """).fetchall()
        
        milestones = []
        for row in milestones_data:
            total = row['total_tasks']
            completed = row['completed_tasks']
            progress = (completed / total * 100) if total > 0 else 0
            
            milestones.append(MilestoneProgress(
                id=row['id'],
                name=row['name'],
                status=row['status'],
                total_tasks=total,
                completed_tasks=completed,
                progress_percentage=round(progress, 1),
                validation_required=bool(row['validation_required'])
            ))
        
        return milestones
    
    def _get_current_task(self, conn: sqlite3.Connection) -> Optional[TaskStatus]:
        """Get currently active task"""
        
        current_task_data = conn.execute("""
            SELECT 
                t.id, t.title, t.status, t.started_at, t.completed_at, t.duration_minutes,
                m.name as milestone_name
            FROM tasks t
            JOIN milestones m ON t.milestone_id = m.id
            WHERE t.status = 'in_progress'
            ORDER BY t.started_at DESC
            LIMIT 1
        """).fetchone()
        
        if not current_task_data:
            return None
        
        return TaskStatus(
            id=current_task_data['id'],
            title=current_task_data['title'],
            status=current_task_data['status'],
            milestone_name=current_task_data['milestone_name'],
            started_at=current_task_data['started_at'],
            completed_at=current_task_data['completed_at'],
            duration_minutes=current_task_data['duration_minutes']
        )
    
    def _get_next_eligible_tasks(self, conn: sqlite3.Connection, limit: int = 3) -> List[TaskStatus]:
        """Get next eligible tasks (no unmet dependencies)"""
        
        next_tasks_data = conn.execute("""
            SELECT 
                t.id, t.title, t.status,
                m.name as milestone_name
            FROM tasks t
            JOIN milestones m ON t.milestone_id = m.id
            WHERE t.status = 'pending'
            AND NOT EXISTS (
                SELECT 1 FROM task_dependencies td
                JOIN tasks dep_task ON td.depends_on_task_id = dep_task.id
                WHERE td.task_id = t.id 
                AND dep_task.status != 'completed'
            )
            ORDER BY m.order_index, t.order_index
            LIMIT ?
        """, (limit,)).fetchall()
        
        return [
            TaskStatus(
                id=row['id'],
                title=row['title'],
                status=row['status'],
                milestone_name=row['milestone_name']
            )
            for row in next_tasks_data
        ]
    
    def _get_validation_status(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get milestone validation status"""
        
        # Find milestones needing validation
        pending_validation = conn.execute("""
            SELECT m.id, m.name
            FROM milestones m
            WHERE m.validation_required = 1
            AND NOT EXISTS (
                SELECT 1 FROM milestone_validations mv
                WHERE mv.milestone_id = m.id 
                AND mv.validation_status = 'passed'
            )
        """).fetchall()
        
        # Get recent validation attempts
        recent_validations = conn.execute("""
            SELECT 
                mv.milestone_id, mv.validation_status, mv.validated_at,
                m.name as milestone_name
            FROM milestone_validations mv
            JOIN milestones m ON mv.milestone_id = m.id
            ORDER BY mv.validated_at DESC
            LIMIT 5
        """).fetchall()
        
        return {
            'pending_validation': [dict(row) for row in pending_validation],
            'recent_validations': [dict(row) for row in recent_validations]
        }
    
    def _format_markdown(
        self,
        project_stats: Dict,
        milestone_progress: List[MilestoneProgress], 
        current_task: Optional[TaskStatus],
        next_tasks: List[TaskStatus],
        validation_status: Dict
    ) -> str:
        """Format all data into markdown"""
        
        # Header
        markdown = f"""# 🚀 Project Status

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Database:** {project_stats['database_path']}

## 📊 Overall Progress
- **Total Tasks:** {project_stats['tasks']['total_tasks']}
- **Completed:** {project_stats['tasks']['completed_tasks']}  
- **In Progress:** {project_stats['tasks']['active_tasks']}
- **Pending:** {project_stats['tasks']['pending_tasks']}
- **Blocked:** {project_stats['tasks']['blocked_tasks']}
- **Progress:** {project_stats['progress_percentage']}% complete

## 📈 Milestone Status

"""
        
        # Current Activity
        if current_task:
            duration_text = ""
            if current_task.started_at:
                started = datetime.fromisoformat(current_task.started_at.replace('Z', '+00:00'))
                duration = datetime.now() - started
                duration_minutes = int(duration.total_seconds() / 60)
                duration_text = f"**Duration:** {duration_minutes} minutes"
            
            markdown += f"""## 🔄 Current Activity
**Task:** {current_task.id} - {current_task.title}  
**Milestone:** {current_task.milestone_name}  
**Started:** {current_task.started_at}  
{duration_text}

"""
        else:
            markdown += """## 🔄 Current Activity
**No active tasks**

"""
        
        # Milestone Progress
        for milestone in milestone_progress:
            status_icon = {
                'completed': '✅',
                'in_progress': '🔄', 
                'pending': '⏳',
                'blocked': '❌'
            }.get(milestone.status, '❓')
            
            validation_text = ""
            if milestone.validation_required:
                validation_text = " 🔍 *Validation Required*"
            
            markdown += f"""### {status_icon} {milestone.name} ({milestone.progress_percentage}%){validation_text}
- **Tasks:** {milestone.completed_tasks}/{milestone.total_tasks} complete
- **Status:** {milestone.status}

"""
        
        # Next Eligible Tasks
        if next_tasks:
            markdown += """## ⏭️ Next Eligible Tasks

"""
            for i, task in enumerate(next_tasks, 1):
                markdown += f"{i}. **{task.id}** - {task.title} _(in {task.milestone_name})_\n"
            markdown += "\n"
        
        # Validation Status
        if validation_status['pending_validation']:
            markdown += """## ⚠️ Validation Pending

"""
            for validation in validation_status['pending_validation']:
                markdown += f"- **{validation['name']}** (ID: {validation['id']})\n"
            markdown += "\n"
        
        # Dependencies Status
        markdown += """## 🔗 Dependencies
- **Blocked Tasks:** [Query from task_dependencies where dependency not completed]
- **Available Tasks:** See 'Next Eligible Tasks' above

"""
        
        # Footer
        markdown += f"""---
*Status updated after each task completion*
*Manual update: `cd .claude/commands/iris/utils && python3 status_translator.py`*
"""
        
        return markdown
    
    def get_milestone_summary(self, milestone_id: str) -> Optional[Dict]:
        """Get detailed summary for specific milestone"""
        try:
            with self.db.get_connection() as conn:
                milestone_data = conn.execute("""
                    SELECT * FROM milestones WHERE id = ?
                """, (milestone_id,)).fetchone()
                
                if not milestone_data:
                    return None
                
                tasks_data = conn.execute("""
                    SELECT id, title, status, started_at, completed_at, duration_minutes
                    FROM tasks 
                    WHERE milestone_id = ?
                    ORDER BY order_index
                """, (milestone_id,)).fetchall()
                
                return {
                    'milestone': dict(milestone_data),
                    'tasks': [dict(task) for task in tasks_data],
                    'summary_generated': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Failed to get milestone summary: {e}")
            return None


def main():
    """CLI interface for status translation"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='IRIS Status Translator')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--milestone', '-m', help='Generate summary for specific milestone')
    parser.add_argument('--db-path', help='Path to database file')
    
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager(args.db_path)
    translator = StatusTranslator(db_manager)
    
    if args.milestone:
        # Generate milestone-specific summary
        summary = translator.get_milestone_summary(args.milestone)
        if summary:
            print(json.dumps(summary, indent=2, default=str))
        else:
            print(f"❌ Milestone not found: {args.milestone}")
            sys.exit(1)
    else:
        # Generate full project status
        success = translator.update_status_file(args.output)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()