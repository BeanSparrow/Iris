#!/usr/bin/env python3
"""
IRIS Token Efficient Logger - Optimized logging for autopilot mode
Minimizes terminal output to reduce token usage while maintaining full file-based logging
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

class LogLevel(Enum):
    """Log levels for filtering output"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    MILESTONE = 5  # Special level for milestone updates

class OutputMode(Enum):
    """Terminal output modes"""
    SILENT = "silent"          # Minimal terminal output (autopilot)
    VERBOSE = "verbose"        # Full terminal output (debug/learning)
    EMERGENCY = "emergency"    # Only critical errors

class TokenEfficientLogger:
    """
    Logger optimized for long-running autopilot sessions
    """
    
    def __init__(self, mode: OutputMode = OutputMode.SILENT, project_root: str = None):
        self.mode = mode
        self.project_root = Path(project_root or os.getcwd())
        self.tasks_dir = self.project_root / ".tasks"
        self.tasks_dir.mkdir(exist_ok=True)
        
        # File paths
        self.log_file = self.tasks_dir / "autopilot.log"
        self.status_file = self.project_root / "PROJECT_STATUS.md"
        self.metrics_file = self.tasks_dir / "autopilot_metrics.json"
        
        # State tracking
        self.session_start = datetime.now()
        self.last_console_update = datetime.now()
        self.console_update_interval = timedelta(minutes=5)  # 5 min between console updates
        self.milestone_history = []
        self.error_count = 0
        self.warning_count = 0
        
        # Terminal output buffer (for batching)
        self.console_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Initialize files
        self._initialize_log_files()
        
        # Start background status updater
        if mode == OutputMode.SILENT:
            self._start_status_updater()
    
    def _initialize_log_files(self):
        """Initialize log files with headers"""
        # Clear/create log file
        with open(self.log_file, 'w') as f:
            f.write(f"# IRIS Autopilot Log\n")
            f.write(f"# Started: {self.session_start.isoformat()}\n")
            f.write(f"# Mode: {self.mode.value}\n")
            f.write(f"# Project: {self.project_root}\n")
            f.write(f"{'='*60}\n\n")
        
        # Initialize metrics
        self._update_metrics({
            "session_start": self.session_start.isoformat(),
            "mode": self.mode.value,
            "total_logs": 0,
            "console_updates": 0,
            "milestones_completed": 0,
            "errors": 0,
            "warnings": 0
        })
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, 
            context: Dict = None, force_console: bool = False):
        """
        Log a message with token-efficient output
        
        Args:
            message: Log message
            level: Log level
            context: Additional context data
            force_console: Force console output regardless of mode
        """
        timestamp = datetime.now()
        formatted_message = self._format_log_entry(timestamp, level, message, context)
        
        # Always log to file
        self._write_to_file(formatted_message)
        
        # Console output based on mode and level
        should_show_console = self._should_show_on_console(level, force_console, timestamp)
        
        if should_show_console:
            self._write_to_console(level, message, context)
        
        # Update metrics
        self._increment_metrics(level)
        
        # Special handling for milestones
        if level == LogLevel.MILESTONE:
            self._handle_milestone_update(message, context)
    
    def milestone_update(self, milestone_id: str, status: str, 
                        tasks_complete: int, total_tasks: int, 
                        duration_minutes: int = None):
        """
        Log milestone progress with special formatting
        """
        context = {
            "milestone_id": milestone_id,
            "status": status,
            "tasks_complete": tasks_complete,
            "total_tasks": total_tasks,
            "duration_minutes": duration_minutes
        }
        
        if status == "completed":
            message = f"M{milestone_id} ✅ Complete ({duration_minutes}m) → Next milestone"
        elif status == "in_progress":
            progress_pct = int((tasks_complete / total_tasks) * 100)
            message = f"M{milestone_id} ⚡ In Progress ({tasks_complete}/{total_tasks} tasks, {progress_pct}%)"
        else:
            message = f"M{milestone_id} {status}"
        
        self.log(message, LogLevel.MILESTONE, context, force_console=True)
    
    def task_update(self, task_id: str, status: str, duration_minutes: int = None):
        """Log task progress"""
        context = {
            "task_id": task_id,
            "status": status,
            "duration_minutes": duration_minutes
        }
        
        if status == "completed":
            message = f"Task {task_id} ✅ Complete"
        elif status == "in_progress": 
            message = f"Task {task_id} ⚡ In Progress"
        elif status == "failed":
            message = f"Task {task_id} ❌ Failed"
        else:
            message = f"Task {task_id} {status}"
        
        # Tasks are INFO level, will be batched in silent mode
        self.log(message, LogLevel.INFO, context)
    
    def error(self, message: str, context: Dict = None, recoverable: bool = True):
        """Log an error with appropriate console visibility"""
        level = LogLevel.ERROR if recoverable else LogLevel.CRITICAL
        self.log(f"❌ {message}", level, context, force_console=not recoverable)
        
        if not recoverable:
            self._emergency_stop(message, context)
    
    def warning(self, message: str, context: Dict = None):
        """Log a warning"""
        self.log(f"⚠️  {message}", LogLevel.WARNING, context)
    
    def info(self, message: str, context: Dict = None):
        """Log info message"""
        self.log(message, LogLevel.INFO, context)
    
    def debug(self, message: str, context: Dict = None):
        """Log debug message (file only in silent mode)"""
        self.log(f"🔧 {message}", LogLevel.DEBUG, context)
    
    def _format_log_entry(self, timestamp: datetime, level: LogLevel, 
                          message: str, context: Dict = None) -> str:
        """Format log entry for file output"""
        time_str = timestamp.strftime("%H:%M:%S")
        level_str = level.name.ljust(9)
        
        entry = f"[{time_str}] {level_str} {message}"
        
        if context:
            context_str = json.dumps(context, separators=(',', ':'))
            entry += f" | {context_str}"
        
        return entry + "\n"
    
    def _should_show_on_console(self, level: LogLevel, force_console: bool, 
                               timestamp: datetime) -> bool:
        """Determine if message should appear on console"""
        if force_console:
            return True
        
        if self.mode == OutputMode.VERBOSE:
            return True
        elif self.mode == OutputMode.EMERGENCY:
            return level == LogLevel.CRITICAL
        elif self.mode == OutputMode.SILENT:
            # Only milestones and critical errors
            if level in [LogLevel.CRITICAL, LogLevel.MILESTONE]:
                return True
            
            # Time-based batching for other messages
            time_since_last = timestamp - self.last_console_update
            if time_since_last >= self.console_update_interval:
                return level in [LogLevel.ERROR, LogLevel.WARNING]
        
        return False
    
    def _write_to_file(self, formatted_message: str):
        """Write to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(formatted_message)
    
    def _write_to_console(self, level: LogLevel, message: str, context: Dict = None):
        """Write to console with appropriate formatting"""
        timestamp = datetime.now().strftime("%H:%M")
        
        if level == LogLevel.MILESTONE:
            # Special milestone formatting
            print(f"[{timestamp}] {message}")
        elif level == LogLevel.CRITICAL:
            print(f"🚨 CRITICAL: {message}")
        elif level == LogLevel.ERROR:
            print(f"❌ ERROR: {message}")
        elif level == LogLevel.WARNING:
            print(f"⚠️  WARNING: {message}")
        else:
            print(f"[{timestamp}] {message}")
        
        self.last_console_update = datetime.now()
    
    def _handle_milestone_update(self, message: str, context: Dict = None):
        """Special handling for milestone updates"""
        if context:
            self.milestone_history.append({
                "timestamp": datetime.now().isoformat(),
                "message": message,
                **context
            })
    
    def _increment_metrics(self, level: LogLevel):
        """Update metrics counters"""
        if level == LogLevel.ERROR:
            self.error_count += 1
        elif level == LogLevel.WARNING:
            self.warning_count += 1
        elif level == LogLevel.MILESTONE:
            # Will be updated by milestone_update method
            pass
    
    def _update_metrics(self, metrics: Dict):
        """Update metrics file"""
        current_metrics = {
            "last_updated": datetime.now().isoformat(),
            "session_duration_minutes": self._get_session_duration_minutes(),
            "errors": self.error_count,
            "warnings": self.warning_count,
            "milestones_completed": len([m for m in self.milestone_history if "completed" in m.get("status", "")]),
            **metrics
        }
        
        with open(self.metrics_file, 'w') as f:
            json.dump(current_metrics, f, indent=2)
    
    def _get_session_duration_minutes(self) -> int:
        """Get session duration in minutes"""
        duration = datetime.now() - self.session_start
        return int(duration.total_seconds() / 60)
    
    def _start_status_updater(self):
        """Start background thread to update status file"""
        def update_loop():
            while True:
                try:
                    # Update status file every 30 seconds
                    time.sleep(30)
                    # Status file will be updated by Technical Writer
                    # This just ensures metrics are fresh
                    self._update_metrics({})
                except:
                    break
        
        status_thread = threading.Thread(target=update_loop, daemon=True)
        status_thread.start()
    
    def _emergency_stop(self, message: str, context: Dict = None):
        """Handle emergency stop scenario"""
        emergency_msg = f"""
🚨 IRIS AUTOPILOT EMERGENCY STOP 🚨
{message}

Session Details:
- Started: {self.session_start.isoformat()}
- Duration: {self._get_session_duration_minutes()} minutes
- Errors: {self.error_count}
- Warnings: {self.warning_count}

Check {self.log_file} for full details.
"""
        print(emergency_msg)
        
        # Write emergency details to file
        with open(self.tasks_dir / "EMERGENCY_STOP.md", 'w') as f:
            f.write(emergency_msg)
            if context:
                f.write(f"\nContext:\n```json\n{json.dumps(context, indent=2)}\n```")
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        return {
            "session_start": self.session_start.isoformat(),
            "duration_minutes": self._get_session_duration_minutes(),
            "mode": self.mode.value,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "milestones_completed": len(self.milestone_history),
            "log_file": str(self.log_file),
            "status_file": str(self.status_file)
        }

# Convenience functions for easy import
def create_silent_logger(project_root: str = None) -> TokenEfficientLogger:
    """Create logger optimized for autopilot mode"""
    return TokenEfficientLogger(OutputMode.SILENT, project_root)

def create_verbose_logger(project_root: str = None) -> TokenEfficientLogger:
    """Create logger for debugging/learning mode"""
    return TokenEfficientLogger(OutputMode.VERBOSE, project_root)

def create_emergency_logger(project_root: str = None) -> TokenEfficientLogger:
    """Create logger that only shows critical errors"""
    return TokenEfficientLogger(OutputMode.EMERGENCY, project_root)

def main():
    """CLI entry point for token_efficient_logger"""
    import argparse

    parser = argparse.ArgumentParser(
        description='IRIS Token Efficient Logger CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Commands:
  milestone_update <id> <status> <complete> <total> [duration]
      Log a milestone status update

  task_update <id> <status> [duration]
      Log a task status update

  info <message>
      Log an info message

  warning <message>
      Log a warning message

  error <message> [--recoverable]
      Log an error message

  summary
      Print session summary

Options:
  -c <code>           Execute Python code with logger in scope
  --verbose           Use verbose output mode
  --project-root DIR  Set project root directory

Examples:
  python3 token_efficient_logger.py milestone_update M1 completed 5 5 15
  python3 token_efficient_logger.py task_update T-AUTH-1 completed 3
  python3 token_efficient_logger.py info "Task started"
  python3 token_efficient_logger.py error "Something failed" --recoverable
  python3 token_efficient_logger.py -c "logger.info('Custom log')"
'''
    )

    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('-c', '--code', help='Execute Python code with logger in scope')
    parser.add_argument('--verbose', action='store_true', help='Use verbose output mode')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--recoverable', action='store_true', help='Mark error as recoverable')

    args = parser.parse_args()

    # Determine output mode
    mode = OutputMode.VERBOSE if args.verbose else OutputMode.SILENT

    # Create logger
    logger = TokenEfficientLogger(mode, args.project_root)

    # Handle -c option for arbitrary code execution
    if args.code:
        # Execute code with logger in scope
        exec(args.code, {'logger': logger, 'LogLevel': LogLevel})
        return

    # Handle commands
    if not args.command:
        parser.print_help()
        return

    command = args.command.lower()
    cmd_args = args.args

    if command == 'milestone_update':
        if len(cmd_args) < 4:
            print("Error: milestone_update requires: <id> <status> <tasks_complete> <total_tasks> [duration]")
            sys.exit(1)

        milestone_id = cmd_args[0]
        status = cmd_args[1]
        tasks_complete = int(cmd_args[2])
        total_tasks = int(cmd_args[3])
        duration = int(cmd_args[4]) if len(cmd_args) > 4 else None

        logger.milestone_update(milestone_id, status, tasks_complete, total_tasks, duration)
        print(f"Logged milestone update: {milestone_id} -> {status}")

    elif command == 'task_update':
        if len(cmd_args) < 2:
            print("Error: task_update requires: <id> <status> [duration]")
            sys.exit(1)

        task_id = cmd_args[0]
        status = cmd_args[1]
        duration = int(cmd_args[2]) if len(cmd_args) > 2 else None

        logger.task_update(task_id, status, duration)
        print(f"Logged task update: {task_id} -> {status}")

    elif command == 'info':
        message = ' '.join(cmd_args) if cmd_args else 'Info message'
        logger.info(message)
        print(f"Logged info: {message}")

    elif command == 'warning':
        message = ' '.join(cmd_args) if cmd_args else 'Warning message'
        logger.warning(message)
        print(f"Logged warning: {message}")

    elif command == 'error':
        message = ' '.join(cmd_args) if cmd_args else 'Error message'
        logger.error(message, recoverable=args.recoverable)
        print(f"Logged error: {message}")

    elif command == 'debug':
        message = ' '.join(cmd_args) if cmd_args else 'Debug message'
        logger.debug(message)
        print(f"Logged debug: {message}")

    elif command == 'summary':
        summary = logger.get_session_summary()
        print(json.dumps(summary, indent=2))

    elif command == 'test':
        # Run test sequence
        print(f"Testing IRIS Logger in {mode.value} mode...")

        logger.info("Starting test sequence")
        logger.debug("This is a debug message")
        logger.warning("This is a warning")
        logger.milestone_update("1", "in_progress", 2, 5)
        logger.task_update("T1-001", "completed", 3)
        logger.milestone_update("1", "completed", 5, 5, 15)
        logger.info("Test sequence complete")

        print(f"Session summary: {logger.get_session_summary()}")
        print(f"Log file: {logger.log_file}")
        print(f"Status file: {logger.status_file}")

    else:
        print(f"Unknown command: {command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()