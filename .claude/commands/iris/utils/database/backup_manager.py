#!/usr/bin/env python3
"""
IRIS Database Backup Manager

Provides automated backup and recovery capabilities for SQLite database.
Replaces the complex JSON backup system with simple SQLite backups.
"""

import sqlite3
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict


class BackupManager:
    """Manages database backups and recovery"""
    
    def __init__(self, db_path: str, backup_dir: Optional[str] = None):
        self.db_path = Path(db_path)
        
        if backup_dir is None:
            self.backup_dir = self.db_path.parent / "backups"
        else:
            self.backup_dir = Path(backup_dir)
        
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup with optional custom name"""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"iris_backup_{timestamp}.db"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            # Use SQLite backup API for consistency
            with sqlite3.connect(str(self.db_path)) as source:
                with sqlite3.connect(str(backup_path)) as backup_conn:
                    source.backup(backup_conn)
            
            print(f"✅ Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return ""
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore from specific backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_path}")
            return False
        
        try:
            # Create safety backup before restore
            safety_backup = self.create_backup("pre_restore_safety")
            
            # Replace current database
            shutil.copy2(backup_path, self.db_path)
            
            print(f"✅ Database restored from: {backup_name}")
            print(f"📁 Safety backup created: {Path(safety_backup).name}")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, str]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db"):
            try:
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2)
                })
            except Exception:
                continue
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_minimum: int = 5) -> int:
        """Clean up old backups while keeping minimum number"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        backups = self.list_backups()
        
        if len(backups) <= keep_minimum:
            print(f"⏭️  Keeping all {len(backups)} backups (below minimum)")
            return 0
        
        removed_count = 0
        
        # Keep at least keep_minimum backups, remove older ones
        for backup in backups[keep_minimum:]:
            created_time = datetime.fromisoformat(backup['created'])
            if created_time < cutoff_date:
                try:
                    Path(backup['path']).unlink()
                    print(f"🗑️  Removed old backup: {backup['name']}")
                    removed_count += 1
                except Exception as e:
                    print(f"⚠️  Failed to remove {backup['name']}: {e}")
        
        print(f"✅ Cleanup complete: {removed_count} backups removed")
        return removed_count
    
    def auto_backup(self, trigger_reason: str = "auto") -> str:
        """Create automatic backup with reason in filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"auto_{trigger_reason}_{timestamp}.db"
        
        return self.create_backup(backup_name)
    
    def verify_backup(self, backup_name: str) -> bool:
        """Verify backup integrity"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return False
        
        try:
            with sqlite3.connect(str(backup_path)) as conn:
                # Check database integrity
                result = conn.execute("PRAGMA integrity_check").fetchone()
                
                if result and result[0] == "ok":
                    # Check if essential tables exist
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                    
                    required_tables = {'milestones', 'tasks', 'project_state'}
                    found_tables = {row[0] for row in tables}
                    
                    if required_tables.issubset(found_tables):
                        print(f"✅ Backup verified: {backup_name}")
                        return True
            
            print(f"❌ Backup verification failed: {backup_name}")
            return False
            
        except Exception as e:
            print(f"❌ Backup verification error: {e}")
            return False
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict]:
        """Get detailed information about a specific backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return None
        
        try:
            stat = backup_path.stat()
            
            info = {
                'name': backup_name,
                'path': str(backup_path),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_valid': self.verify_backup(backup_name)
            }
            
            # Try to get database stats
            if info['is_valid']:
                try:
                    with sqlite3.connect(str(backup_path)) as conn:
                        milestone_count = conn.execute("SELECT COUNT(*) FROM milestones").fetchone()[0]
                        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
                        
                        info.update({
                            'milestone_count': milestone_count,
                            'task_count': task_count
                        })
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            print(f"❌ Failed to get backup info: {e}")
            return None


def main():
    """CLI interface for backup management"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='IRIS Database Backup Manager')
    parser.add_argument('action', choices=['create', 'restore', 'list', 'cleanup', 'verify'])
    parser.add_argument('--backup-name', help='Backup name for restore/verify operations')
    parser.add_argument('--db-path', help='Path to database file')
    parser.add_argument('--keep-days', type=int, default=30, help='Days to keep backups during cleanup')
    
    args = parser.parse_args()
    
    if not args.db_path:
        # Try to find database in standard location
        from pathlib import Path
        current = Path.cwd()
        while current != current.parent:
            db_path = current / ".tasks" / "iris_project.db"
            if db_path.exists():
                args.db_path = str(db_path)
                break
            current = current.parent
        
        if not args.db_path:
            print("❌ Database not found. Please specify --db-path")
            sys.exit(1)
    
    backup_manager = BackupManager(args.db_path)
    
    if args.action == 'create':
        backup_path = backup_manager.create_backup()
        if backup_path:
            print(f"Backup created: {Path(backup_path).name}")
    
    elif args.action == 'restore':
        if not args.backup_name:
            print("❌ --backup-name required for restore")
            sys.exit(1)
        
        success = backup_manager.restore_backup(args.backup_name)
        sys.exit(0 if success else 1)
    
    elif args.action == 'list':
        backups = backup_manager.list_backups()
        if not backups:
            print("No backups found")
        else:
            print(f"{'Name':<40} {'Created':<20} {'Size (MB)':<10}")
            print("-" * 70)
            for backup in backups:
                print(f"{backup['name']:<40} {backup['created'][:19]:<20} {backup['size_mb']:<10}")
    
    elif args.action == 'cleanup':
        removed = backup_manager.cleanup_old_backups(args.keep_days)
        print(f"Removed {removed} old backups")
    
    elif args.action == 'verify':
        if not args.backup_name:
            print("❌ --backup-name required for verify")
            sys.exit(1)
        
        is_valid = backup_manager.verify_backup(args.backup_name)
        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()