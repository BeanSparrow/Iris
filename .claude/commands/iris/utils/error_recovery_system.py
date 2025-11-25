#!/usr/bin/env python3
"""
IRIS Error Recovery System - Intelligent error handling and recovery for autopilot mode
Provides multiple recovery strategies and self-healing capabilities
"""

import os
import json
import time
import subprocess
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Non-critical, can continue
    MEDIUM = "medium"     # Important but recoverable
    HIGH = "high"         # Critical but potentially recoverable
    CRITICAL = "critical" # System-level failure

class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    RETRY = "retry"                    # Simple retry
    ROLLBACK = "rollback"             # Rollback to known good state
    FIX_AND_RETRY = "fix_and_retry"   # Attempt fix then retry
    SKIP_AND_CONTINUE = "skip_and_continue"  # Skip failed task and continue
    ESCALATE = "escalate"             # Escalate to human intervention
    ABORT = "abort"                   # Stop execution

@dataclass
class ErrorEvent:
    """Represents an error that occurred during execution"""
    error_id: str
    timestamp: datetime
    component: str  # Which component reported the error
    error_type: str
    error_message: str
    severity: ErrorSeverity
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_attempts: int = 0
    resolved: bool = False
    resolution_strategy: Optional[RecoveryStrategy] = None
    resolution_message: Optional[str] = None

@dataclass
class RecoveryRule:
    """Defines how to handle specific types of errors"""
    rule_id: str
    error_pattern: str  # Regex pattern to match error messages
    component: Optional[str] = None  # Component this rule applies to
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    max_attempts: int = 3
    cooldown_seconds: int = 30
    fix_command: Optional[str] = None
    enabled: bool = True

class ErrorRecoverySystem:
    """
    Intelligent error recovery system for IRIS autopilot
    """
    
    def __init__(self, project_root: str, iris_dir: str):
        self.project_root = Path(project_root)
        self.iris_dir = Path(iris_dir)
        self.tasks_dir = self.project_root / ".tasks"
        
        # Error tracking
        self.error_history: List[ErrorEvent] = []
        self.active_errors: Dict[str, ErrorEvent] = {}
        self.recovery_rules: List[RecoveryRule] = []
        
        # Configuration
        self.autopilot_mode = os.getenv('IRIS_AUTOPILOT_ACTIVE', 'false').lower() == 'true'
        self.recovery_enabled = True
        self.max_recovery_attempts = 3
        self.escalation_threshold = 5  # Escalate after 5 failed recoveries
        
        # State
        self.system_health = "healthy"  # healthy, degraded, critical
        self.last_health_check = datetime.now()
        
        # Initialize system
        self._initialize_recovery_rules()
        self._load_error_history()
        
        # Logging
        self.logger = None
    
    def set_logger(self, logger):
        """Set the token efficient logger"""
        self.logger = logger
    
    def _initialize_recovery_rules(self):
        """Initialize default recovery rules"""
        self.recovery_rules = [
            # Task execution errors
            RecoveryRule(
                rule_id="task_timeout",
                error_pattern=r"timeout|timed out",
                component="executor",
                severity=ErrorSeverity.MEDIUM,
                strategy=RecoveryStrategy.RETRY,
                max_attempts=2,
                cooldown_seconds=60
            ),
            
            # Build and compilation errors
            RecoveryRule(
                rule_id="build_failure", 
                error_pattern=r"build failed|compilation error|npm.*failed",
                component="validator",
                severity=ErrorSeverity.HIGH,
                strategy=RecoveryStrategy.FIX_AND_RETRY,
                max_attempts=3,
                fix_command="npm install"
            ),
            
            # Dependency issues
            RecoveryRule(
                rule_id="dependency_error",
                error_pattern=r"module not found|package.*not found|dependency.*missing",
                severity=ErrorSeverity.HIGH,
                strategy=RecoveryStrategy.FIX_AND_RETRY,
                max_attempts=2,
                fix_command="npm install"
            ),
            
            # Port conflicts
            RecoveryRule(
                rule_id="port_conflict",
                error_pattern=r"port.*in use|address already in use|EADDRINUSE",
                severity=ErrorSeverity.MEDIUM,
                strategy=RecoveryStrategy.FIX_AND_RETRY,
                max_attempts=2,
                fix_command="pkill -f node"
            ),
            
            # Permission errors
            RecoveryRule(
                rule_id="permission_error",
                error_pattern=r"permission denied|EACCES|access denied",
                severity=ErrorSeverity.HIGH,
                strategy=RecoveryStrategy.ESCALATE,
                max_attempts=1
            ),
            
            # File system errors
            RecoveryRule(
                rule_id="file_not_found",
                error_pattern=r"file not found|no such file|ENOENT",
                severity=ErrorSeverity.MEDIUM,
                strategy=RecoveryStrategy.FIX_AND_RETRY,
                max_attempts=2
            ),
            
            # Network errors
            RecoveryRule(
                rule_id="network_error",
                error_pattern=r"network.*error|connection.*refused|ENETUNREACH|fetch.*failed",
                severity=ErrorSeverity.LOW,
                strategy=RecoveryStrategy.RETRY,
                max_attempts=3,
                cooldown_seconds=60
            ),
            
            # Memory issues
            RecoveryRule(
                rule_id="memory_error",
                error_pattern=r"out of memory|memory.*exhausted|heap.*overflow",
                severity=ErrorSeverity.CRITICAL,
                strategy=RecoveryStrategy.ROLLBACK,
                max_attempts=1
            ),
            
            # Git errors
            RecoveryRule(
                rule_id="git_conflict",
                error_pattern=r"merge conflict|git.*conflict|conflict.*marker",
                severity=ErrorSeverity.HIGH,
                strategy=RecoveryStrategy.ESCALATE,
                max_attempts=1
            )
        ]
        
        # Load custom rules if they exist
        self._load_custom_recovery_rules()
    
    def _load_custom_recovery_rules(self):
        """Load custom recovery rules from config"""
        try:
            rules_file = self.tasks_dir / "recovery_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    custom_rules_data = json.load(f)
                
                for rule_data in custom_rules_data.get('rules', []):
                    rule = RecoveryRule(
                        rule_id=rule_data['rule_id'],
                        error_pattern=rule_data['error_pattern'],
                        component=rule_data.get('component'),
                        severity=ErrorSeverity(rule_data.get('severity', 'medium')),
                        strategy=RecoveryStrategy(rule_data.get('strategy', 'retry')),
                        max_attempts=rule_data.get('max_attempts', 3),
                        cooldown_seconds=rule_data.get('cooldown_seconds', 30),
                        fix_command=rule_data.get('fix_command'),
                        enabled=rule_data.get('enabled', True)
                    )
                    self.recovery_rules.append(rule)
                    
                if self.logger:
                    self.logger.debug(f"Loaded {len(custom_rules_data.get('rules', []))} custom recovery rules")
                    
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to load custom recovery rules: {e}")
    
    def _load_error_history(self):
        """Load error history from previous sessions"""
        try:
            history_file = self.tasks_dir / "error_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                
                # Load only recent errors (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for error_data in history_data.get('errors', []):
                    timestamp = datetime.fromisoformat(error_data['timestamp'])
                    if timestamp > cutoff_time:
                        error = ErrorEvent(
                            error_id=error_data['error_id'],
                            timestamp=timestamp,
                            component=error_data['component'],
                            error_type=error_data['error_type'],
                            error_message=error_data['error_message'],
                            severity=ErrorSeverity(error_data['severity']),
                            context=error_data['context'],
                            recovery_attempts=error_data.get('recovery_attempts', 0),
                            resolved=error_data.get('resolved', False)
                        )
                        self.error_history.append(error)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to load error history: {e}")
    
    def report_error(self, component: str, error_type: str, error_message: str, 
                    context: Dict[str, Any] = None, stack_trace: str = None) -> str:
        """Report an error to the recovery system"""
        error_id = f"{component}_{error_type}_{int(time.time())}"
        
        # Determine severity and recovery strategy
        severity, strategy = self._analyze_error(error_message, component)
        
        error = ErrorEvent(
            error_id=error_id,
            timestamp=datetime.now(),
            component=component,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            context=context or {},
            stack_trace=stack_trace
        )
        
        self.error_history.append(error)
        self.active_errors[error_id] = error
        
        if self.logger:
            self.logger.error(f"Error reported: {error_type} in {component}: {error_message}")
        
        # Update system health
        self._update_system_health()
        
        # Trigger recovery if in autopilot mode
        if self.autopilot_mode and self.recovery_enabled:
            self._trigger_recovery(error)
        
        # Save error history
        self._save_error_history()
        
        return error_id
    
    def _analyze_error(self, error_message: str, component: str) -> Tuple[ErrorSeverity, RecoveryStrategy]:
        """Analyze error and determine severity and strategy"""
        import re
        
        for rule in self.recovery_rules:
            if not rule.enabled:
                continue
            
            # Check if rule applies to this component
            if rule.component and rule.component != component:
                continue
            
            # Check if error pattern matches
            if re.search(rule.error_pattern, error_message, re.IGNORECASE):
                return rule.severity, rule.strategy
        
        # Default classification
        return ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY
    
    def _trigger_recovery(self, error: ErrorEvent):
        """Trigger recovery process for an error"""
        if not self.recovery_enabled:
            return
        
        # Find applicable recovery rule
        recovery_rule = self._find_recovery_rule(error)
        
        if not recovery_rule:
            if self.logger:
                self.logger.warning(f"No recovery rule found for error {error.error_id}")
            return
        
        # Check if we've exceeded max attempts
        if error.recovery_attempts >= recovery_rule.max_attempts:
            if self.logger:
                self.logger.error(f"Max recovery attempts exceeded for {error.error_id}")
            self._escalate_error(error)
            return
        
        # Apply cooldown if this isn't the first attempt
        if error.recovery_attempts > 0:
            time.sleep(recovery_rule.cooldown_seconds)
        
        # Execute recovery strategy
        success = self._execute_recovery_strategy(error, recovery_rule)
        
        error.recovery_attempts += 1
        
        if success:
            error.resolved = True
            error.resolution_strategy = recovery_rule.strategy
            error.resolution_message = f"Recovered using {recovery_rule.strategy.value} strategy"
            
            if error.error_id in self.active_errors:
                del self.active_errors[error.error_id]
            
            if self.logger:
                self.logger.info(f"Error {error.error_id} resolved using {recovery_rule.strategy.value}")
        else:
            if self.logger:
                self.logger.warning(f"Recovery attempt {error.recovery_attempts} failed for {error.error_id}")
    
    def _find_recovery_rule(self, error: ErrorEvent) -> Optional[RecoveryRule]:
        """Find the best recovery rule for an error"""
        import re
        
        for rule in self.recovery_rules:
            if not rule.enabled:
                continue
            
            # Check component match
            if rule.component and rule.component != error.component:
                continue
            
            # Check pattern match
            if re.search(rule.error_pattern, error.error_message, re.IGNORECASE):
                return rule
        
        return None
    
    def _execute_recovery_strategy(self, error: ErrorEvent, rule: RecoveryRule) -> bool:
        """Execute a specific recovery strategy"""
        try:
            if rule.strategy == RecoveryStrategy.RETRY:
                return self._recovery_retry(error, rule)
            elif rule.strategy == RecoveryStrategy.ROLLBACK:
                return self._recovery_rollback(error, rule)
            elif rule.strategy == RecoveryStrategy.FIX_AND_RETRY:
                return self._recovery_fix_and_retry(error, rule)
            elif rule.strategy == RecoveryStrategy.SKIP_AND_CONTINUE:
                return self._recovery_skip_and_continue(error, rule)
            elif rule.strategy == RecoveryStrategy.ESCALATE:
                return self._escalate_error(error)
            elif rule.strategy == RecoveryStrategy.ABORT:
                return self._abort_execution(error)
            else:
                if self.logger:
                    self.logger.error(f"Unknown recovery strategy: {rule.strategy}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Recovery strategy execution failed: {e}")
            return False
    
    def _recovery_retry(self, error: ErrorEvent, rule: RecoveryRule) -> bool:
        """Simple retry recovery strategy"""
        if self.logger:
            self.logger.info(f"Retrying operation for error {error.error_id}")
        
        # For retry, we just signal that recovery was attempted
        # The actual retry will happen when the operation is re-executed
        return True
    
    def _recovery_rollback(self, error: ErrorEvent, rule: RecoveryRule) -> bool:
        """Rollback to known good state"""
        if self.logger:
            self.logger.info(f"Rolling back due to error {error.error_id}")
        
        try:
            # Try to rollback using git
            rollback_commands = [
                "git stash push -m 'Auto-stash before rollback'",
                "git reset --hard HEAD~1"
            ]
            
            for cmd in rollback_commands:
                process = subprocess.run(
                    cmd.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if process.returncode != 0:
                    if self.logger:
                        self.logger.warning(f"Rollback command failed: {cmd}")
                    return False
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Rollback failed: {e}")
            return False
    
    def _recovery_fix_and_retry(self, error: ErrorEvent, rule: RecoveryRule) -> bool:
        """Attempt to fix the issue then retry"""
        if self.logger:
            self.logger.info(f"Attempting fix for error {error.error_id}")
        
        if not rule.fix_command:
            if self.logger:
                self.logger.warning(f"No fix command defined for rule {rule.rule_id}")
            return False
        
        try:
            # Execute fix command
            process = subprocess.run(
                rule.fix_command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if process.returncode == 0:
                if self.logger:
                    self.logger.info(f"Fix command succeeded for {error.error_id}")
                return True
            else:
                if self.logger:
                    self.logger.warning(f"Fix command failed: {process.stderr}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fix command execution failed: {e}")
            return False
    
    def _recovery_skip_and_continue(self, error: ErrorEvent, rule: RecoveryRule) -> bool:
        """Skip the failed operation and continue"""
        if self.logger:
            self.logger.info(f"Skipping failed operation for error {error.error_id}")
        
        # Mark as resolved so execution can continue
        return True
    
    def _escalate_error(self, error: ErrorEvent) -> bool:
        """Escalate error for human intervention"""
        if self.logger:
            self.logger.error(f"Escalating error {error.error_id} for human intervention", recoverable=False)
        
        # Create escalation file
        escalation_file = self.tasks_dir / f"ESCALATION_{error.error_id}.md"
        
        escalation_content = f"""# Error Escalation Required

**Error ID:** {error.error_id}  
**Timestamp:** {error.timestamp.isoformat()}  
**Component:** {error.component}  
**Severity:** {error.severity.value}

## Error Details

**Type:** {error.error_type}  
**Message:** {error.error_message}

## Context

```json
{json.dumps(error.context, indent=2)}
```

## Stack Trace

```
{error.stack_trace or 'Not available'}
```

## Recovery Attempts

- Attempts made: {error.recovery_attempts}
- Strategy used: {error.resolution_strategy.value if error.resolution_strategy else 'None'}

## Next Steps

1. Review the error details above
2. Investigate the root cause
3. Apply manual fix if needed
4. Resume autopilot execution with: `/iris:autopilot --resume`

## System Health

Current system status: {self.system_health}
"""
        
        try:
            with open(escalation_file, 'w') as f:
                f.write(escalation_content)
            
            if self.logger:
                self.logger.info(f"Escalation file created: {escalation_file}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create escalation file: {e}")
        
        return False  # Escalation means recovery failed
    
    def _abort_execution(self, error: ErrorEvent) -> bool:
        """Abort autopilot execution"""
        if self.logger:
            self.logger.error(f"Aborting execution due to critical error {error.error_id}", recoverable=False)
        
        # Set environment variable to signal abort
        os.environ['IRIS_AUTOPILOT_ABORT'] = 'true'
        
        return False
    
    def _update_system_health(self):
        """Update overall system health status"""
        self.last_health_check = datetime.now()
        
        # Count recent errors by severity
        recent_cutoff = datetime.now() - timedelta(minutes=30)
        recent_errors = [e for e in self.error_history if e.timestamp > recent_cutoff]
        
        critical_errors = len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
        high_errors = len([e for e in recent_errors if e.severity == ErrorSeverity.HIGH])
        
        if critical_errors > 0:
            self.system_health = "critical"
        elif high_errors >= 3 or len(recent_errors) >= 10:
            self.system_health = "degraded"
        else:
            self.system_health = "healthy"
        
        if self.logger:
            if self.system_health != "healthy":
                self.logger.warning(f"System health: {self.system_health}")
    
    def _save_error_history(self):
        """Save error history to file"""
        try:
            history_file = self.tasks_dir / "error_history.json"
            
            # Keep only last 100 errors
            recent_errors = self.error_history[-100:] if len(self.error_history) > 100 else self.error_history
            
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'system_health': self.system_health,
                'errors': [
                    {
                        'error_id': e.error_id,
                        'timestamp': e.timestamp.isoformat(),
                        'component': e.component,
                        'error_type': e.error_type,
                        'error_message': e.error_message,
                        'severity': e.severity.value,
                        'context': e.context,
                        'recovery_attempts': e.recovery_attempts,
                        'resolved': e.resolved
                    }
                    for e in recent_errors
                ]
            }
            
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save error history: {e}")
    
    def get_system_status(self) -> Dict:
        """Get current system status and health"""
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_errors = [e for e in self.error_history if e.timestamp > recent_cutoff]
        
        return {
            'system_health': self.system_health,
            'last_health_check': self.last_health_check.isoformat(),
            'total_errors': len(self.error_history),
            'active_errors': len(self.active_errors),
            'recent_errors_1h': len(recent_errors),
            'recovery_enabled': self.recovery_enabled,
            'autopilot_mode': self.autopilot_mode,
            'error_breakdown': {
                'critical': len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]),
                'high': len([e for e in recent_errors if e.severity == ErrorSeverity.HIGH]),
                'medium': len([e for e in recent_errors if e.severity == ErrorSeverity.MEDIUM]),
                'low': len([e for e in recent_errors if e.severity == ErrorSeverity.LOW])
            }
        }
    
    def get_recovery_statistics(self) -> Dict:
        """Get recovery success statistics"""
        resolved_errors = [e for e in self.error_history if e.resolved]
        
        if not self.error_history:
            return {'total_errors': 0, 'recovery_rate': 0}
        
        strategy_stats = {}
        for strategy in RecoveryStrategy:
            strategy_errors = [e for e in resolved_errors if e.resolution_strategy == strategy]
            strategy_stats[strategy.value] = len(strategy_errors)
        
        return {
            'total_errors': len(self.error_history),
            'resolved_errors': len(resolved_errors),
            'recovery_rate': int((len(resolved_errors) / len(self.error_history)) * 100),
            'strategy_breakdown': strategy_stats,
            'average_recovery_attempts': sum(e.recovery_attempts for e in self.error_history) / len(self.error_history)
        }

def create_error_recovery_system(project_root: str, iris_dir: str) -> ErrorRecoverySystem:
    """Create an error recovery system instance"""
    return ErrorRecoverySystem(project_root, iris_dir)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 error_recovery_system.py <project_root> <iris_dir>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    iris_dir = sys.argv[2]
    
    # Create error recovery system
    recovery_system = create_error_recovery_system(project_root, iris_dir)
    
    print(f"🛡️ IRIS Error Recovery System")
    print(f"📁 Project: {project_root}")
    print("")
    
    # Display system status
    status = recovery_system.get_system_status()
    print(f"🏥 System Health: {status['system_health']}")
    print(f"📊 Total Errors: {status['total_errors']}")
    print(f"🔥 Active Errors: {status['active_errors']}")
    print(f"⏰ Recent Errors (1h): {status['recent_errors_1h']}")
    
    # Display recovery statistics
    stats = recovery_system.get_recovery_statistics()
    print(f"\n📈 Recovery Statistics:")
    print(f"Success Rate: {stats['recovery_rate']}%")
    print(f"Average Attempts: {stats['average_recovery_attempts']:.1f}")
    
    # Display error breakdown
    breakdown = status['error_breakdown']
    if any(breakdown.values()):
        print(f"\n🚨 Recent Error Breakdown:")
        for severity, count in breakdown.items():
            if count > 0:
                print(f"  {severity.upper()}: {count}")
    else:
        print("\n✅ No recent errors detected")