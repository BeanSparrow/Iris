#!/usr/bin/env python3
"""
IRIS Database Manager

Provides atomic SQLite operations replacing JSON file management.
Includes connection pooling, transaction management, and backup capabilities.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database for IRIS project state"""

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize DatabaseManager.

        Args:
            project_root: Optional path to project root. If not provided, checks:
                         1. IRIS_PROJECT_ROOT environment variable
                         2. Auto-detection via _find_project_root()
        """
        if project_root is not None:
            # Explicit project root provided
            self.project_root = Path(project_root)
        elif os.environ.get('IRIS_PROJECT_ROOT'):
            # Use environment variable (set by autopilot)
            self.project_root = Path(os.environ['IRIS_PROJECT_ROOT'])
        else:
            # Auto-detect project root (fallback)
            self.project_root = self._find_project_root()

        self.tasks_dir = self.project_root / ".tasks"
        self.db_path = self.tasks_dir / "iris_project.db"
        
        # Ensure tasks directory exists
        self.tasks_dir.mkdir(exist_ok=True)
        
        # Schema file path
        self.schema_path = Path(__file__).parent / "schema.sql"
        
        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            self.initialize_database()
    
    def _find_project_root(self) -> Path:
        """Find project root by looking for .claude directory (IRIS installation marker)"""
        current = Path.cwd()

        # First, check if we're running from inside .claude/commands/iris/utils
        # If so, walk up to find the project root (parent of .claude)
        cwd_str = str(current)
        if ".claude/commands/iris" in cwd_str:
            # Extract the project root by finding the .claude parent
            parts = cwd_str.split(".claude/commands/iris")
            if parts[0]:
                project_root = Path(parts[0].rstrip("/\\"))
                return project_root

        # Second, look for .claude directory (IRIS installation = project root)
        check = current
        while check != check.parent:
            if (check / ".claude").exists():
                return check
            check = check.parent

        # Third, look for existing .tasks directory (but not inside .claude/commands)
        check = current
        while check != check.parent:
            if (check / ".tasks").exists() and ".claude/commands" not in str(check):
                return check
            check = check.parent

        # Fallback to current directory
        return current
    
    def initialize_database(self) -> bool:
        """Initialize database with schema"""
        try:
            with self.get_connection() as conn:
                # Read and execute schema
                with open(self.schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema in parts (SQLite doesn't like multiple statements)
                for statement in schema_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        conn.execute(statement)
                
                conn.commit()
            
            print(f"✅ Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            # Enable row factory for dict-like access
            conn.row_factory = sqlite3.Row
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        finally:
            conn.close()
    
    def execute_transaction(self, operations: List[Callable[[sqlite3.Connection], Any]]) -> Tuple[bool, List[Any]]:
        """Execute multiple operations in a single transaction"""
        results = []
        
        try:
            with self.get_connection() as conn:
                for operation in operations:
                    result = operation(conn)
                    results.append(result)
                
                conn.commit()
                return True, results
                
        except Exception as e:
            print(f"❌ Transaction failed: {e}")
            return False, []
    
    def backup_database(self) -> str:
        """Create timestamped backup of database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.tasks_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"iris_project_backup_{timestamp}.db"
        
        try:
            # Use SQLite backup API
            with self.get_connection() as source:
                with sqlite3.connect(str(backup_path)) as backup:
                    source.backup(backup)
            
            print(f"✅ Database backed up: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return ""
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                print(f"❌ Backup file not found: {backup_path}")
                return False
            
            # Remove current database
            if self.db_path.exists():
                self.db_path.unlink()
            
            # Copy backup to main location
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            print(f"✅ Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def validate_schema(self) -> bool:
        """Validate database schema integrity"""
        try:
            with self.get_connection() as conn:
                # Check if all required tables exist
                required_tables = [
                    'project_metadata', 'milestones', 'tasks', 'task_dependencies',
                    'technologies', 'technology_sources', 'guardrails',
                    'deferred_features', 'prd_features',
                    'project_metrics', 'project_state', 'task_executions',
                    'milestone_validations',
                    # Research tables (added in schema 2.0.0)
                    'research_opportunities', 'research_executions',
                    # Refine tables (added in schema 2.1.0)
                    'refine_iterations', 'refine_findings', 'refine_improvements'
                ]
                
                for table in required_tables:
                    result = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    ).fetchone()
                    
                    if not result:
                        print(f"❌ Missing table: {table}")
                        return False
                
                # Check schema version
                version_result = conn.execute(
                    "SELECT value FROM project_metadata WHERE key='schema_version'"
                ).fetchone()
                
                if not version_result:
                    print("❌ Schema version not found")
                    return False
                
                print(f"✅ Schema validation passed (version: {version_result['value']})")
                return True
                
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            return False
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get basic project statistics"""
        try:
            with self.get_connection() as conn:
                # Get milestone stats
                milestone_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_milestones,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_milestones,
                        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_milestones
                    FROM milestones
                """).fetchone()
                
                # Get task stats
                task_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_tasks,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks
                    FROM tasks
                """).fetchone()
                
                # Get current milestone
                current_milestone_id = conn.execute(
                    "SELECT value FROM project_state WHERE key='current_milestone_id'"
                ).fetchone()
                
                current_milestone = None
                if current_milestone_id and current_milestone_id['value']:
                    current_milestone = conn.execute(
                        "SELECT * FROM milestones WHERE id = ?",
                        (current_milestone_id['value'],)
                    ).fetchone()
                
                return {
                    'milestones': dict(milestone_stats),
                    'tasks': dict(task_stats),
                    'current_milestone': dict(current_milestone) if current_milestone else None,
                    'database_path': str(self.db_path),
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Failed to get project stats: {e}")
            return {}
    
    def export_to_json(self, output_dir: Optional[str] = None) -> bool:
        """Export database to JSON files for backup/debugging"""
        if output_dir is None:
            output_dir = self.tasks_dir / "json_export"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        try:
            with self.get_connection() as conn:
                # Export each major table
                tables_to_export = [
                    'milestones', 'tasks', 'task_dependencies',
                    'technologies', 'guardrails', 'project_state',
                    'prd_features'
                ]
                
                for table in tables_to_export:
                    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                    data = [dict(row) for row in rows]
                    
                    with open(output_dir / f"{table}.json", 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                
                print(f"✅ Database exported to JSON: {output_dir}")
                return True
                
        except Exception as e:
            print(f"❌ JSON export failed: {e}")
            return False
    
    def migrate_from_json(self, json_dir: Optional[str] = None) -> bool:
        """Migrate from old JSON files to SQLite"""
        if json_dir is None:
            json_dir = self.tasks_dir
        else:
            json_dir = Path(json_dir)
        
        try:
            # Create backup before migration
            backup_path = self.backup_database()
            
            with self.get_connection() as conn:
                # Migrate task_graph.json
                task_graph_file = json_dir / "task_graph.json"
                if task_graph_file.exists():
                    self._migrate_task_graph(conn, task_graph_file)
                
                # Migrate progress_tracker.json  
                progress_file = json_dir / "progress_tracker.json"
                if progress_file.exists():
                    self._migrate_progress_tracker(conn, progress_file)
                
                # Migrate techstack_research.json
                techstack_file = json_dir / "techstack_research.json"
                if techstack_file.exists():
                    self._migrate_techstack(conn, techstack_file)
                
                # Migrate other files as needed...
                
                conn.commit()
            
            print(f"✅ Migration from JSON completed (backup: {backup_path})")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def _migrate_task_graph(self, conn: sqlite3.Connection, task_graph_file: Path):
        """Migrate task_graph.json to milestones and tasks tables"""
        with open(task_graph_file, 'r') as f:
            data = json.load(f)
        
        # Migrate milestones
        for milestone in data.get('milestones', []):
            conn.execute("""
                INSERT OR REPLACE INTO milestones 
                (id, name, description, status, order_index) 
                VALUES (?, ?, ?, ?, ?)
            """, (
                milestone.get('id'),
                milestone.get('name'),
                milestone.get('description', ''),
                milestone.get('status', 'pending'),
                milestone.get('order_index', 0)
            ))
        
        # Migrate tasks
        for task in data.get('tasks', []):
            conn.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, milestone_id, title, description, status, order_index, max_file_changes) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task.get('id'),
                task.get('milestone_id'),
                task.get('title'),
                task.get('description', ''),
                task.get('status', 'pending'),
                task.get('order_index', 0),
                task.get('max_file_changes', 10)
            ))
            
            # Migrate task dependencies
            for dep in task.get('dependencies', []):
                conn.execute("""
                    INSERT OR REPLACE INTO task_dependencies 
                    (task_id, depends_on_task_id) 
                    VALUES (?, ?)
                """, (task.get('id'), dep))
    
    def _migrate_progress_tracker(self, conn: sqlite3.Connection, progress_file: Path):
        """Migrate progress_tracker.json to project_state table"""
        with open(progress_file, 'r') as f:
            data = json.load(f)
        
        # Migrate key-value pairs
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            conn.execute("""
                INSERT OR REPLACE INTO project_state (key, value) 
                VALUES (?, ?)
            """, (key, str(value)))
    
    def _migrate_techstack(self, conn: sqlite3.Connection, techstack_file: Path):
        """Migrate techstack_research.json to technologies table"""
        with open(techstack_file, 'r') as f:
            data = json.load(f)
        
        stack = data.get('stack', {})
        for tech_name, tech_data in stack.items():
            conn.execute("""
                INSERT OR REPLACE INTO technologies
                (name, category, version, is_latest_stable, official_url, decision_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tech_name,
                tech_data.get('category', 'imported'),
                tech_data.get('version'),
                tech_data.get('version_verified', {}).get('is_latest_stable', False),
                tech_data.get('documentation', {}).get('official_url'),
                tech_data.get('decision_sources', [{}])[0].get('relevance', '')
            ))