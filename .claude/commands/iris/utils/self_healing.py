#!/usr/bin/env python3
"""
IRIS Self-Healing System - Proactive system maintenance and self-repair
Monitors system health and automatically fixes common issues
"""

import os
import json
import time
import psutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum

class HealthMetric(Enum):
    """System health metrics to monitor"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_SPACE = "disk_space"
    PROCESS_COUNT = "process_count"
    FILE_HANDLES = "file_handles"
    NETWORK_CONNECTIVITY = "network_connectivity"
    APPLICATION_HEALTH = "application_health"

class HealthStatus(Enum):
    """Health status levels"""
    OPTIMAL = "optimal"     # 90-100% health
    GOOD = "good"          # 70-89% health
    DEGRADED = "degraded"  # 50-69% health
    CRITICAL = "critical"  # 0-49% health

@dataclass
class HealthCheck:
    """Individual health check configuration"""
    check_id: str
    name: str
    metric: HealthMetric
    interval_seconds: int = 60
    warning_threshold: float = 70.0
    critical_threshold: float = 90.0
    enabled: bool = True
    auto_fix: bool = True
    fix_command: Optional[str] = None

@dataclass
class HealthReading:
    """A health metric reading"""
    metric: HealthMetric
    timestamp: datetime
    value: float
    status: HealthStatus
    details: Dict[str, Any]

class SelfHealingSystem:
    """
    Proactive system health monitoring and self-repair system
    """
    
    def __init__(self, project_root: str, iris_dir: str):
        self.project_root = Path(project_root)
        self.iris_dir = Path(iris_dir)
        self.tasks_dir = self.project_root / ".tasks"
        
        # Health monitoring
        self.health_checks: List[HealthCheck] = []
        self.health_history: List[HealthReading] = []
        self.current_health: Dict[HealthMetric, HealthReading] = {}
        
        # Configuration
        self.autopilot_mode = os.getenv('IRIS_AUTOPILOT_ACTIVE', 'false').lower() == 'true'
        self.monitoring_enabled = True
        self.healing_enabled = True
        self.monitoring_interval = 30  # seconds
        
        # State
        self.monitoring_thread: Optional[threading.Thread] = None
        self.last_health_check = datetime.now()
        self.system_health_score = 100.0
        
        # Initialize health checks
        self._initialize_health_checks()
        self._load_health_configuration()
        
        # Logging
        self.logger = None
    
    def set_logger(self, logger):
        """Set the token efficient logger"""
        self.logger = logger
    
    def _initialize_health_checks(self):
        """Initialize default health checks"""
        self.health_checks = [
            HealthCheck(
                check_id="cpu_usage",
                name="CPU Usage Monitor",
                metric=HealthMetric.CPU_USAGE,
                interval_seconds=30,
                warning_threshold=70.0,
                critical_threshold=90.0,
                auto_fix=True,
                fix_command="pkill -f 'node.*dev'"  # Kill high-CPU dev processes
            ),
            
            HealthCheck(
                check_id="memory_usage",
                name="Memory Usage Monitor",
                metric=HealthMetric.MEMORY_USAGE,
                interval_seconds=60,
                warning_threshold=80.0,
                critical_threshold=95.0,
                auto_fix=True
            ),
            
            HealthCheck(
                check_id="disk_space",
                name="Disk Space Monitor",
                metric=HealthMetric.DISK_SPACE,
                interval_seconds=300,  # 5 minutes
                warning_threshold=80.0,
                critical_threshold=95.0,
                auto_fix=True
            ),
            
            HealthCheck(
                check_id="process_count",
                name="Process Count Monitor",
                metric=HealthMetric.PROCESS_COUNT,
                interval_seconds=120,
                warning_threshold=500.0,
                critical_threshold=1000.0,
                auto_fix=False  # Don't auto-kill processes
            ),
            
            HealthCheck(
                check_id="network_connectivity",
                name="Network Connectivity Check",
                metric=HealthMetric.NETWORK_CONNECTIVITY,
                interval_seconds=180,  # 3 minutes
                warning_threshold=50.0,  # 50% success rate
                critical_threshold=20.0,  # 20% success rate
                auto_fix=False
            ),
            
            HealthCheck(
                check_id="application_health",
                name="Application Health Check",
                metric=HealthMetric.APPLICATION_HEALTH,
                interval_seconds=90,
                warning_threshold=70.0,
                critical_threshold=40.0,
                auto_fix=True
            )
        ]
    
    def _load_health_configuration(self):
        """Load health monitoring configuration"""
        try:
            config_file = self.tasks_dir / "health_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.monitoring_interval = config.get('monitoring_interval', 30)
                self.healing_enabled = config.get('healing_enabled', True)
                
                # Update check configurations
                check_configs = config.get('health_checks', {})
                for check in self.health_checks:
                    if check.check_id in check_configs:
                        check_config = check_configs[check.check_id]
                        check.enabled = check_config.get('enabled', check.enabled)
                        check.warning_threshold = check_config.get('warning_threshold', check.warning_threshold)
                        check.critical_threshold = check_config.get('critical_threshold', check.critical_threshold)
                        check.auto_fix = check_config.get('auto_fix', check.auto_fix)
                
                if self.logger:
                    self.logger.debug("Health configuration loaded")
                    
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to load health config: {e}")
    
    def start_monitoring(self):
        """Start health monitoring in background"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.monitoring_enabled = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        if self.logger:
            self.logger.info("Self-healing system monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_enabled = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.logger:
            self.logger.info("Self-healing system monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_enabled:
            try:
                # Run health checks
                self._run_health_checks()
                
                # Calculate overall health score
                self._calculate_health_score()
                
                # Trigger healing if needed
                if self.healing_enabled and self.autopilot_mode:
                    self._trigger_healing_actions()
                
                # Clean up old health data
                self._cleanup_health_history()
                
                # Wait before next check
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Health monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _run_health_checks(self):
        """Run all enabled health checks"""
        current_time = datetime.now()
        
        for health_check in self.health_checks:
            if not health_check.enabled:
                continue
            
            # Check if it's time to run this check
            last_reading = self.current_health.get(health_check.metric)
            if (last_reading and 
                current_time - last_reading.timestamp < timedelta(seconds=health_check.interval_seconds)):
                continue
            
            # Run the health check
            reading = self._execute_health_check(health_check)
            if reading:
                self.current_health[health_check.metric] = reading
                self.health_history.append(reading)
        
        self.last_health_check = current_time
    
    def _execute_health_check(self, check: HealthCheck) -> Optional[HealthReading]:
        """Execute a specific health check"""
        try:
            if check.metric == HealthMetric.CPU_USAGE:
                return self._check_cpu_usage()
            elif check.metric == HealthMetric.MEMORY_USAGE:
                return self._check_memory_usage()
            elif check.metric == HealthMetric.DISK_SPACE:
                return self._check_disk_space()
            elif check.metric == HealthMetric.PROCESS_COUNT:
                return self._check_process_count()
            elif check.metric == HealthMetric.NETWORK_CONNECTIVITY:
                return self._check_network_connectivity()
            elif check.metric == HealthMetric.APPLICATION_HEALTH:
                return self._check_application_health()
            else:
                return None
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Health check {check.check_id} failed: {e}")
            return None
    
    def _check_cpu_usage(self) -> HealthReading:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        status = self._get_status_for_value(cpu_percent, 70.0, 90.0)
        
        return HealthReading(
            metric=HealthMetric.CPU_USAGE,
            timestamp=datetime.now(),
            value=cpu_percent,
            status=status,
            details={
                'cpu_count': psutil.cpu_count(),
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
            }
        )
    
    def _check_memory_usage(self) -> HealthReading:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        status = self._get_status_for_value(memory_percent, 80.0, 95.0)
        
        return HealthReading(
            metric=HealthMetric.MEMORY_USAGE,
            timestamp=datetime.now(),
            value=memory_percent,
            status=status,
            details={
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2)
            }
        )
    
    def _check_disk_space(self) -> HealthReading:
        """Check disk space usage"""
        disk_usage = psutil.disk_usage(self.project_root)
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        status = self._get_status_for_value(disk_percent, 80.0, 95.0)
        
        return HealthReading(
            metric=HealthMetric.DISK_SPACE,
            timestamp=datetime.now(),
            value=disk_percent,
            status=status,
            details={
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'path': str(self.project_root)
            }
        )
    
    def _check_process_count(self) -> HealthReading:
        """Check number of running processes"""
        process_count = len(psutil.pids())
        status = self._get_status_for_value(process_count, 500.0, 1000.0)
        
        # Get process breakdown
        process_breakdown = {}
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                process_breakdown[name] = process_breakdown.get(name, 0) + 1
            except:
                continue
        
        # Top 5 most common processes
        top_processes = sorted(process_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return HealthReading(
            metric=HealthMetric.PROCESS_COUNT,
            timestamp=datetime.now(),
            value=float(process_count),
            status=status,
            details={
                'total_processes': process_count,
                'top_processes': dict(top_processes)
            }
        )
    
    def _check_network_connectivity(self) -> HealthReading:
        """Check network connectivity"""
        test_hosts = ['8.8.8.8', 'google.com', 'github.com']
        success_count = 0
        
        for host in test_hosts:
            try:
                # Ping test
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '3', host],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    success_count += 1
            except:
                continue
        
        success_rate = (success_count / len(test_hosts)) * 100
        status = self._get_status_for_value(100 - success_rate, 50.0, 80.0)  # Invert for failure rate
        
        return HealthReading(
            metric=HealthMetric.NETWORK_CONNECTIVITY,
            timestamp=datetime.now(),
            value=success_rate,
            status=status,
            details={
                'tests_passed': success_count,
                'tests_total': len(test_hosts),
                'success_rate': success_rate
            }
        )
    
    def _check_application_health(self) -> HealthReading:
        """Check application-specific health"""
        health_score = 100.0
        details = {}
        
        try:
            # Check if key files exist
            key_files = ['package.json', 'tsconfig.json', '.gitignore']
            existing_files = sum(1 for f in key_files if (self.project_root / f).exists())
            file_score = (existing_files / len(key_files)) * 40  # 40% weight
            health_score = file_score
            details['key_files_score'] = file_score
            
            # Check if node_modules exists and is reasonable size
            node_modules = self.project_root / 'node_modules'
            if node_modules.exists():
                try:
                    size_mb = sum(f.stat().st_size for f in node_modules.rglob('*') if f.is_file()) / (1024*1024)
                    if 10 < size_mb < 1000:  # Reasonable range
                        deps_score = 30
                    elif size_mb <= 10:
                        deps_score = 10  # Too small, might be incomplete
                    else:
                        deps_score = 20  # Too large, might have issues
                except:
                    deps_score = 15
            else:
                deps_score = 0
            
            health_score += deps_score
            details['dependencies_score'] = deps_score
            
            # Check git repository health
            if (self.project_root / '.git').exists():
                git_score = 30
                try:
                    # Check if repo has commits
                    result = subprocess.run(
                        ['git', 'rev-list', '--count', 'HEAD'],
                        cwd=self.project_root,
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        commit_count = int(result.stdout.decode().strip())
                        if commit_count > 0:
                            git_score = 30
                        else:
                            git_score = 10
                except:
                    git_score = 15
            else:
                git_score = 0
            
            health_score = min(100.0, health_score + git_score)
            details['git_score'] = git_score
            
        except Exception as e:
            health_score = 50.0  # Default on error
            details['error'] = str(e)
        
        status = self._get_status_for_value(100 - health_score, 30.0, 60.0)  # Invert for degradation
        
        return HealthReading(
            metric=HealthMetric.APPLICATION_HEALTH,
            timestamp=datetime.now(),
            value=health_score,
            status=status,
            details=details
        )
    
    def _get_status_for_value(self, value: float, warning_threshold: float, critical_threshold: float) -> HealthStatus:
        """Determine health status based on value and thresholds"""
        if value >= critical_threshold:
            return HealthStatus.CRITICAL
        elif value >= warning_threshold:
            return HealthStatus.DEGRADED
        elif value >= warning_threshold * 0.7:  # 70% of warning threshold
            return HealthStatus.GOOD
        else:
            return HealthStatus.OPTIMAL
    
    def _calculate_health_score(self):
        """Calculate overall system health score"""
        if not self.current_health:
            self.system_health_score = 100.0
            return
        
        # Weight different metrics
        metric_weights = {
            HealthMetric.CPU_USAGE: 0.20,
            HealthMetric.MEMORY_USAGE: 0.25,
            HealthMetric.DISK_SPACE: 0.15,
            HealthMetric.PROCESS_COUNT: 0.10,
            HealthMetric.NETWORK_CONNECTIVITY: 0.10,
            HealthMetric.APPLICATION_HEALTH: 0.20
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, reading in self.current_health.items():
            weight = metric_weights.get(metric, 0.1)
            
            # Convert status to score
            if reading.status == HealthStatus.OPTIMAL:
                score = 100.0
            elif reading.status == HealthStatus.GOOD:
                score = 80.0
            elif reading.status == HealthStatus.DEGRADED:
                score = 60.0
            else:  # CRITICAL
                score = 30.0
            
            total_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            self.system_health_score = total_score / total_weight
        else:
            self.system_health_score = 100.0
    
    def _trigger_healing_actions(self):
        """Trigger healing actions for degraded metrics"""
        for metric, reading in self.current_health.items():
            if reading.status in [HealthStatus.CRITICAL, HealthStatus.DEGRADED]:
                self._attempt_healing(metric, reading)
    
    def _attempt_healing(self, metric: HealthMetric, reading: HealthReading):
        """Attempt to heal a specific metric"""
        if self.logger:
            self.logger.info(f"Attempting healing for {metric.value} (status: {reading.status.value})")
        
        try:
            if metric == HealthMetric.CPU_USAGE and reading.value > 90:
                self._heal_high_cpu()
            elif metric == HealthMetric.MEMORY_USAGE and reading.value > 90:
                self._heal_high_memory()
            elif metric == HealthMetric.DISK_SPACE and reading.value > 90:
                self._heal_disk_space()
            elif metric == HealthMetric.APPLICATION_HEALTH and reading.value < 50:
                self._heal_application_issues()
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Healing attempt failed for {metric.value}: {e}")
    
    def _heal_high_cpu(self):
        """Heal high CPU usage"""
        if self.logger:
            self.logger.info("Healing high CPU usage")
        
        # Kill high-CPU development processes
        try:
            subprocess.run(
                ['pkill', '-f', 'node.*dev'],
                timeout=10
            )
            time.sleep(5)  # Give processes time to die
            
            if self.logger:
                self.logger.info("Killed high-CPU development processes")
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to kill high-CPU processes: {e}")
    
    def _heal_high_memory(self):
        """Heal high memory usage"""
        if self.logger:
            self.logger.info("Healing high memory usage")
        
        # Force garbage collection in Node.js processes
        try:
            subprocess.run(
                ['pkill', '-USR2', '-f', 'node'],
                timeout=10
            )
            
            if self.logger:
                self.logger.info("Sent garbage collection signal to Node processes")
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to trigger garbage collection: {e}")
    
    def _heal_disk_space(self):
        """Heal disk space issues"""
        if self.logger:
            self.logger.info("Healing disk space issues")
        
        # Clean common temp directories
        cleanup_paths = [
            self.project_root / 'node_modules' / '.cache',
            self.project_root / '.next' / 'cache',
            self.project_root / 'dist',
            self.project_root / 'build',
            Path.home() / '.npm' / '_cacache'
        ]
        
        for path in cleanup_paths:
            if path.exists():
                try:
                    subprocess.run(
                        ['rm', '-rf', str(path)],
                        timeout=30
                    )
                    if self.logger:
                        self.logger.info(f"Cleaned up {path}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Failed to clean {path}: {e}")
    
    def _heal_application_issues(self):
        """Heal application health issues"""
        if self.logger:
            self.logger.info("Healing application issues")
        
        # Reinstall dependencies if needed
        try:
            if (self.project_root / 'package.json').exists():
                subprocess.run(
                    ['npm', 'install'],
                    cwd=self.project_root,
                    timeout=300
                )
                
                if self.logger:
                    self.logger.info("Reinstalled npm dependencies")
                    
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to reinstall dependencies: {e}")
    
    def _cleanup_health_history(self):
        """Clean up old health history data"""
        # Keep only last 1000 readings or 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.health_history = [
            reading for reading in self.health_history 
            if reading.timestamp > cutoff_time
        ]
        
        # Keep only last 1000 entries
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]
    
    def get_system_health_summary(self) -> Dict:
        """Get comprehensive system health summary"""
        current_time = datetime.now()
        
        # Recent health readings (last hour)
        recent_cutoff = current_time - timedelta(hours=1)
        recent_readings = [r for r in self.health_history if r.timestamp > recent_cutoff]
        
        # Metric summaries
        metric_summaries = {}
        for metric in HealthMetric:
            metric_readings = [r for r in recent_readings if r.metric == metric]
            if metric_readings:
                latest = max(metric_readings, key=lambda x: x.timestamp)
                avg_value = sum(r.value for r in metric_readings) / len(metric_readings)
                
                metric_summaries[metric.value] = {
                    'current_value': latest.value,
                    'current_status': latest.status.value,
                    'average_value': round(avg_value, 2),
                    'readings_count': len(metric_readings),
                    'last_updated': latest.timestamp.isoformat()
                }
        
        return {
            'overall_health_score': round(self.system_health_score, 2),
            'last_check': self.last_health_check.isoformat(),
            'monitoring_enabled': self.monitoring_enabled,
            'healing_enabled': self.healing_enabled,
            'autopilot_mode': self.autopilot_mode,
            'total_readings': len(self.health_history),
            'recent_readings': len(recent_readings),
            'metrics': metric_summaries
        }
    
    def force_health_check(self) -> Dict:
        """Force immediate health check of all metrics"""
        if self.logger:
            self.logger.info("Running forced health check")
        
        # Run all health checks immediately
        for health_check in self.health_checks:
            if health_check.enabled:
                reading = self._execute_health_check(health_check)
                if reading:
                    self.current_health[health_check.metric] = reading
                    self.health_history.append(reading)
        
        # Update health score
        self._calculate_health_score()
        
        return self.get_system_health_summary()

def create_self_healing_system(project_root: str, iris_dir: str) -> SelfHealingSystem:
    """Create a self-healing system instance"""
    return SelfHealingSystem(project_root, iris_dir)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 self_healing.py <project_root> <iris_dir>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    iris_dir = sys.argv[2]
    
    # Create self-healing system
    healing_system = create_self_healing_system(project_root, iris_dir)
    
    print(f"🩺 IRIS Self-Healing System")
    print(f"📁 Project: {project_root}")
    print("")
    
    # Start monitoring
    healing_system.start_monitoring()
    
    try:
        # Run immediate health check
        health_summary = healing_system.force_health_check()
        
        print(f"🏥 System Health Score: {health_summary['overall_health_score']}/100")
        print("")
        
        # Display metric statuses
        for metric_name, metric_data in health_summary['metrics'].items():
            status_icon = {
                'optimal': '✅',
                'good': '🟢', 
                'degraded': '🟡',
                'critical': '🔴'
            }.get(metric_data['current_status'], '❓')
            
            print(f"{status_icon} {metric_name}: {metric_data['current_value']} ({metric_data['current_status']})")
        
        print(f"\n🔧 Monitoring: {'Enabled' if health_summary['monitoring_enabled'] else 'Disabled'}")
        print(f"🩹 Healing: {'Enabled' if health_summary['healing_enabled'] else 'Disabled'}")
        
        # Keep monitoring for a bit in demo mode
        if '--demo' in sys.argv:
            print(f"\n📡 Monitoring active... (Press Ctrl+C to stop)")
            while True:
                time.sleep(30)
                current_score = healing_system.system_health_score
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Health Score: {current_score:.1f}")
        
    except KeyboardInterrupt:
        healing_system.stop_monitoring()
        print("\n✅ Self-healing system stopped")