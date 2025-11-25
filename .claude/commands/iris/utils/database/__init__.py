"""
IRIS Database Infrastructure

Provides SQLite-based project state management replacing the JSON file system.
Includes atomic transactions, referential integrity, and automatic backup capabilities.
"""

from .db_manager import DatabaseManager
from .backup_manager import BackupManager

__all__ = ['DatabaseManager', 'BackupManager']