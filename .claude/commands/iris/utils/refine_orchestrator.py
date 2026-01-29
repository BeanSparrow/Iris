#!/usr/bin/env python3
"""
Iris Refine Orchestrator

Manages Ralph Wiggum-style iterative refinement loop.
Handles database operations, configuration, and reporting for the refine phase.

Version: 1.0.0
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from database.db_manager import DatabaseManager


@dataclass
class RefineConfig:
    """Configuration for refine phase based on complexity"""
    complexity: str
    max_iterations: int
    reviewer_count: int
    review_focus_areas: List[str]

    @classmethod
    def from_complexity(cls, complexity: str) -> 'RefineConfig':
        """Create config based on project complexity"""
        configs = {
            'MICRO': {
                'max_iterations': 5,
                'reviewer_count': 2,
                'review_focus_areas': ['gaps', 'quality']
            },
            'SMALL': {
                'max_iterations': 5,
                'reviewer_count': 3,
                'review_focus_areas': ['gaps', 'quality', 'edge_cases']
            },
            'MEDIUM': {
                'max_iterations': 6,
                'reviewer_count': 4,
                'review_focus_areas': ['gaps', 'quality', 'integration', 'edge_cases']
            },
            'LARGE': {
                'max_iterations': 8,
                'reviewer_count': 5,
                'review_focus_areas': ['gaps', 'quality', 'integration', 'edge_cases', 'security']
            },
            'ENTERPRISE': {
                'max_iterations': 10,
                'reviewer_count': 6,
                'review_focus_areas': ['gaps', 'quality', 'integration', 'edge_cases', 'security', 'performance']
            }
        }

        config = configs.get(complexity.upper(), configs['MEDIUM'])
        return cls(
            complexity=complexity.upper(),
            max_iterations=config['max_iterations'],
            reviewer_count=config['reviewer_count'],
            review_focus_areas=config['review_focus_areas']
        )


class RefineOrchestrator:
    """Orchestrates the Ralph Wiggum-style refinement loop"""

    def __init__(self, db_path: Optional[str] = None):
        self.db = DatabaseManager(db_path)

    def get_config(self) -> RefineConfig:
        """Get refine configuration from database"""
        with self.db.get_connection() as conn:
            # Get complexity
            result = conn.execute(
                "SELECT value FROM project_metadata WHERE key = 'project_complexity'"
            ).fetchone()
            complexity = result['value'] if result else 'MEDIUM'

            # Check for custom max_iterations override
            iter_result = conn.execute(
                "SELECT value FROM project_state WHERE key = 'refine_max_iterations'"
            ).fetchone()

            config = RefineConfig.from_complexity(complexity)

            # Apply override if set
            if iter_result and iter_result['value']:
                config.max_iterations = max(5, int(iter_result['value']))  # Minimum 5

            return config

    def initialize_refine_phase(self) -> Dict[str, Any]:
        """Initialize the refine phase"""
        config = self.get_config()

        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO project_state (key, value) VALUES (?, ?)",
                ('refine_phase_status', 'in_progress')
            )
            conn.execute(
                "INSERT OR REPLACE INTO project_state (key, value) VALUES (?, ?)",
                ('refine_current_iteration', '0')
            )
            conn.execute(
                "INSERT OR REPLACE INTO project_state (key, value) VALUES (?, ?)",
                ('refine_max_iterations', str(config.max_iterations))
            )
            conn.execute(
                "INSERT OR REPLACE INTO project_metadata (key, value) VALUES (?, ?)",
                ('refine_started_at', datetime.now().isoformat())
            )
            conn.commit()

        return {
            'status': 'initialized',
            'complexity': config.complexity,
            'max_iterations': config.max_iterations,
            'reviewer_count': config.reviewer_count,
            'review_focus_areas': config.review_focus_areas
        }

    def start_iteration(self, iteration_number: int) -> int:
        """Start a new iteration and return its ID"""
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO refine_iterations (iteration_number, status, started_at)
                   VALUES (?, 'in_progress', datetime('now'))""",
                (iteration_number,)
            )
            conn.execute(
                "INSERT OR REPLACE INTO project_state (key, value) VALUES (?, ?)",
                ('refine_current_iteration', str(iteration_number))
            )
            conn.commit()

            result = conn.execute("SELECT last_insert_rowid()").fetchone()
            return result[0]

    def store_finding(self, iteration_id: int, finding: Dict[str, Any]) -> int:
        """Store a finding from a review agent"""
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO refine_findings
                   (iteration_id, reviewer_focus, severity, category, file_path,
                    line_number, description, suggestion, prd_reference)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    iteration_id,
                    finding.get('focus_area', 'unknown'),
                    finding.get('severity', 'MEDIUM'),
                    finding.get('category', finding.get('focus_area', 'unknown')),
                    finding.get('file'),
                    finding.get('line'),
                    finding.get('description', ''),
                    finding.get('suggestion', ''),
                    finding.get('prd_reference', '')
                )
            )
            conn.commit()

            result = conn.execute("SELECT last_insert_rowid()").fetchone()
            return result[0]

    def store_improvement(self, iteration_id: int, improvement: Dict[str, Any],
                         finding_id: Optional[int] = None) -> int:
        """Store an improvement from the refiner agent"""
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO refine_improvements
                   (iteration_id, finding_id, description, files_modified, commit_hash, tests_passing)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    iteration_id,
                    finding_id,
                    improvement.get('change_made', improvement.get('description', '')),
                    json.dumps(improvement.get('files_modified', [])),
                    improvement.get('commit_hash', ''),
                    improvement.get('tests_passing', False)
                )
            )
            conn.commit()

            result = conn.execute("SELECT last_insert_rowid()").fetchone()
            return result[0]

    def complete_iteration(self, iteration_number: int, validation_passed: bool,
                          findings_count: int = 0, improvements_count: int = 0,
                          summary: str = '') -> None:
        """Mark an iteration as complete"""
        with self.db.get_connection() as conn:
            conn.execute(
                """UPDATE refine_iterations
                   SET status = 'completed',
                       completed_at = datetime('now'),
                       validation_passed = ?,
                       findings_count = ?,
                       improvements_count = ?,
                       summary = ?
                   WHERE iteration_number = ?
                   ORDER BY id DESC LIMIT 1""",
                (validation_passed, findings_count, improvements_count, summary, iteration_number)
            )
            conn.commit()

    def get_iteration_status(self) -> Dict[str, Any]:
        """Get current iteration status"""
        with self.db.get_connection() as conn:
            current = conn.execute(
                "SELECT value FROM project_state WHERE key = 'refine_current_iteration'"
            ).fetchone()
            max_iter = conn.execute(
                "SELECT value FROM project_state WHERE key = 'refine_max_iterations'"
            ).fetchone()
            status = conn.execute(
                "SELECT value FROM project_state WHERE key = 'refine_phase_status'"
            ).fetchone()

            iterations = conn.execute(
                """SELECT iteration_number, status, validation_passed, findings_count, improvements_count
                   FROM refine_iterations ORDER BY iteration_number"""
            ).fetchall()

            return {
                'current_iteration': int(current['value']) if current else 0,
                'max_iterations': int(max_iter['value']) if max_iter else 5,
                'phase_status': status['value'] if status else 'pending',
                'iterations': [dict(i) for i in iterations]
            }

    def complete_refine_phase(self) -> Dict[str, Any]:
        """Complete the refine phase and generate summary"""
        with self.db.get_connection() as conn:
            # Update status
            conn.execute(
                "INSERT OR REPLACE INTO project_state (key, value) VALUES (?, ?)",
                ('refine_phase_status', 'completed')
            )
            conn.execute(
                "INSERT OR REPLACE INTO project_metadata (key, value) VALUES (?, ?)",
                ('refine_completed_at', datetime.now().isoformat())
            )
            conn.commit()

            # Get summary stats
            iterations = conn.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN validation_passed THEN 1 ELSE 0 END) as passed
                   FROM refine_iterations"""
            ).fetchone()

            findings = conn.execute(
                """SELECT severity, COUNT(*) as count
                   FROM refine_findings GROUP BY severity"""
            ).fetchall()

            findings_addressed = conn.execute(
                "SELECT COUNT(*) as count FROM refine_findings WHERE addressed = 1"
            ).fetchone()

            improvements = conn.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN tests_passing THEN 1 ELSE 0 END) as with_tests
                   FROM refine_improvements"""
            ).fetchone()

            return {
                'status': 'completed',
                'iterations': {
                    'total': iterations['total'],
                    'validation_passed': iterations['passed']
                },
                'findings': {
                    'by_severity': {f['severity']: f['count'] for f in findings},
                    'total': sum(f['count'] for f in findings),
                    'addressed': findings_addressed['count']
                },
                'improvements': {
                    'total': improvements['total'],
                    'with_passing_tests': improvements['with_tests']
                }
            }

    def get_prd_content(self) -> str:
        """Get PRD content from database"""
        with self.db.get_connection() as conn:
            result = conn.execute(
                "SELECT value FROM project_metadata WHERE key = 'prd_content'"
            ).fetchone()
            return result['value'] if result else ''

    def get_tech_stack(self) -> Dict[str, Any]:
        """Get approved tech stack from database"""
        with self.db.get_connection() as conn:
            results = conn.execute(
                "SELECT name, category, version FROM technologies"
            ).fetchall()

            stack = {}
            for row in results:
                stack[row['category']] = {
                    'name': row['name'],
                    'version': row['version']
                }
            return stack

    def generate_report(self) -> str:
        """Generate human-readable refine report"""
        status = self.get_iteration_status()

        if status['phase_status'] != 'completed':
            return f"Refine phase in progress: iteration {status['current_iteration']}/{status['max_iterations']}"

        summary = self.complete_refine_phase()

        lines = [
            "═" * 65,
            "                    REFINE PHASE COMPLETE",
            "═" * 65,
            "",
            "ITERATION SUMMARY:",
            "─" * 65,
            f"Total Iterations:           {summary['iterations']['total']}",
            f"Validation Passed:          {summary['iterations']['validation_passed']} / {summary['iterations']['total']}",
            "",
            "FINDINGS SUMMARY:",
            "─" * 65,
            f"Total Findings:             {summary['findings']['total']}",
        ]

        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            count = summary['findings']['by_severity'].get(severity, 0)
            lines.append(f"  - {severity} severity:          {count}")

        addressed_pct = 0
        if summary['findings']['total'] > 0:
            addressed_pct = (summary['findings']['addressed'] / summary['findings']['total']) * 100

        lines.extend([
            f"Findings Addressed:         {summary['findings']['addressed']} ({addressed_pct:.0f}%)",
            "",
            "IMPROVEMENTS SUMMARY:",
            "─" * 65,
            f"Total Improvements:         {summary['improvements']['total']}",
            f"With Passing Tests:         {summary['improvements']['with_passing_tests']}",
            "",
            "═" * 65,
            f"         Implementation refined through {summary['iterations']['total']} iterations",
            "              aligned toward PRD requirements",
            "═" * 65,
        ])

        return "\n".join(lines)

    def generate_detailed_report(self) -> str:
        """Generate detailed report with per-iteration findings and improvements"""
        lines = [
            "═" * 70,
            "                 DETAILED REFINE PHASE REPORT",
            "═" * 70,
            "",
        ]

        with self.db.get_connection() as conn:
            # Get all iterations
            iterations = conn.execute(
                """SELECT id, iteration_number, started_at, completed_at,
                          findings_count, improvements_count, validation_passed, summary
                   FROM refine_iterations ORDER BY iteration_number"""
            ).fetchall()

            if not iterations:
                lines.extend([
                    "  No refine iterations have been recorded yet.",
                    "",
                    "  Run /iris:refine to start the refinement process.",
                    "",
                    "═" * 70,
                ])
                return "\n".join(lines)

            for iteration in iterations:
                iter_num = iteration['iteration_number']
                lines.extend([
                    f"┌{'─' * 68}┐",
                    f"│ ITERATION {iter_num}{'':>{56}}│",
                    f"├{'─' * 68}┤",
                ])

                # Validation status (handle NULL)
                val_passed = iteration['validation_passed']
                if val_passed is None:
                    val_status = "⏳ NOT RUN"
                elif val_passed:
                    val_status = "✅ PASSED"
                else:
                    val_status = "❌ FAILED"
                lines.append(f"│ Validation: {val_status:<55}│")

                # Get findings for this iteration
                findings = conn.execute(
                    """SELECT severity, category, file_path, line_number, description, suggestion
                       FROM refine_findings WHERE iteration_id = ?
                       ORDER BY CASE severity WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END""",
                    (iteration['id'],)
                ).fetchall()

                if findings:
                    lines.append(f"│{'':68}│")
                    lines.append(f"│ FINDINGS ({len(findings)}):{'':<52}│")
                    lines.append(f"│{'─' * 68}│")

                    for finding in findings:
                        sev_icon = "🔴" if finding['severity'] == 'HIGH' else "🟡" if finding['severity'] == 'MEDIUM' else "🟢"
                        # Truncate description if too long
                        desc = finding['description'][:50] + "..." if len(finding['description']) > 50 else finding['description']
                        # Build location string (handle NULL file_path and line_number)
                        if finding['file_path']:
                            if finding['line_number']:
                                location = f"{finding['file_path']}:{finding['line_number']}"
                            else:
                                location = finding['file_path']
                        else:
                            location = "general"
                        location = location[:30] + "..." if len(location) > 30 else location

                        lines.append(f"│  {sev_icon} [{finding['severity']:<6}] {desc:<47}│")
                        lines.append(f"│     └─ {location:<58}│")

                # Get improvements for this iteration
                improvements = conn.execute(
                    """SELECT description, files_modified, tests_passing
                       FROM refine_improvements WHERE iteration_id = ?""",
                    (iteration['id'],)
                ).fetchall()

                if improvements:
                    lines.append(f"│{'':68}│")
                    lines.append(f"│ IMPROVEMENTS ({len(improvements)}):{'':<49}│")
                    lines.append(f"│{'─' * 68}│")

                    for imp in improvements:
                        # Handle NULL tests_passing
                        if imp['tests_passing'] is None:
                            test_icon = "❓"
                        elif imp['tests_passing']:
                            test_icon = "✅"
                        else:
                            test_icon = "⚠️"
                        desc = imp['description'][:55] + "..." if len(imp['description']) > 55 else imp['description']
                        lines.append(f"│  {test_icon} {desc:<64}│")

                        # Show modified files
                        if imp['files_modified']:
                            try:
                                files = json.loads(imp['files_modified'])
                                for file_path in files[:3]:  # Show max 3 files
                                    file_short = file_path[:55] + "..." if len(file_path) > 55 else file_path
                                    lines.append(f"│     └─ {file_short:<58}│")
                                if len(files) > 3:
                                    lines.append(f"│     └─ ... and {len(files) - 3} more files{'':<43}│")
                            except json.JSONDecodeError:
                                pass

                lines.append(f"└{'─' * 68}┘")
                lines.append("")

            # Summary at the end
            total_findings = conn.execute("SELECT COUNT(*) as c FROM refine_findings").fetchone()['c']
            total_improvements = conn.execute("SELECT COUNT(*) as c FROM refine_improvements").fetchone()['c']
            addressed = conn.execute("SELECT COUNT(*) as c FROM refine_findings WHERE addressed = 1").fetchone()['c']

            lines.extend([
                "═" * 70,
                "                           SUMMARY",
                "═" * 70,
                f"  Total Iterations:    {len(iterations)}",
                f"  Total Findings:      {total_findings}",
                f"  Findings Addressed:  {addressed}",
                f"  Total Improvements:  {total_improvements}",
                "═" * 70,
            ])

        return "\n".join(lines)


def main():
    """CLI interface for refine orchestrator"""
    parser = argparse.ArgumentParser(description='Iris Refine Orchestrator')
    parser.add_argument('command', choices=[
        'init', 'config', 'start-iteration', 'complete-iteration',
        'status', 'complete', 'report', 'detailed-report', 'prd', 'stack'
    ], help='Command to execute')
    parser.add_argument('--iteration', type=int, help='Iteration number')
    parser.add_argument('--validation-passed', type=bool, default=False)
    parser.add_argument('--findings-count', type=int, default=0)
    parser.add_argument('--improvements-count', type=int, default=0)
    parser.add_argument('--summary', type=str, default='')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()
    orchestrator = RefineOrchestrator()

    try:
        if args.command == 'init':
            result = orchestrator.initialize_refine_phase()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"✅ Refine phase initialized")
                print(f"   Complexity: {result['complexity']}")
                print(f"   Max iterations: {result['max_iterations']}")
                print(f"   Reviewers: {result['reviewer_count']}")
                print(f"   Focus areas: {', '.join(result['review_focus_areas'])}")

        elif args.command == 'config':
            config = orchestrator.get_config()
            result = {
                'complexity': config.complexity,
                'max_iterations': config.max_iterations,
                'reviewer_count': config.reviewer_count,
                'review_focus_areas': config.review_focus_areas
            }
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"COMPLEXITY: {config.complexity}")
                print(f"MAX_ITERATIONS: {config.max_iterations}")
                print(f"REVIEWER_COUNT: {config.reviewer_count}")
                print(f"FOCUS_AREAS: {','.join(config.review_focus_areas)}")

        elif args.command == 'start-iteration':
            if not args.iteration:
                print("Error: --iteration required", file=sys.stderr)
                sys.exit(1)
            iteration_id = orchestrator.start_iteration(args.iteration)
            if args.json:
                print(json.dumps({'iteration_id': iteration_id, 'iteration_number': args.iteration}))
            else:
                print(f"✅ Started iteration {args.iteration} (ID: {iteration_id})")

        elif args.command == 'complete-iteration':
            if not args.iteration:
                print("Error: --iteration required", file=sys.stderr)
                sys.exit(1)
            orchestrator.complete_iteration(
                args.iteration,
                args.validation_passed,
                args.findings_count,
                args.improvements_count,
                args.summary
            )
            if args.json:
                print(json.dumps({'status': 'completed', 'iteration': args.iteration}))
            else:
                print(f"✅ Completed iteration {args.iteration}")

        elif args.command == 'status':
            result = orchestrator.get_iteration_status()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Phase: {result['phase_status']}")
                print(f"Progress: {result['current_iteration']}/{result['max_iterations']}")
                for it in result['iterations']:
                    status_char = '✅' if it['validation_passed'] else '⚠️' if it['status'] == 'completed' else '🔄'
                    print(f"  {status_char} Iteration {it['iteration_number']}: {it['findings_count']} findings, {it['improvements_count']} improvements")

        elif args.command == 'complete':
            result = orchestrator.complete_refine_phase()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("✅ Refine phase completed")

        elif args.command == 'report':
            report = orchestrator.generate_report()
            print(report)

        elif args.command == 'detailed-report':
            report = orchestrator.generate_detailed_report()
            print(report)

        elif args.command == 'prd':
            prd = orchestrator.get_prd_content()
            print(prd)

        elif args.command == 'stack':
            stack = orchestrator.get_tech_stack()
            if args.json:
                print(json.dumps(stack, indent=2))
            else:
                for category, tech in stack.items():
                    print(f"{category}: {tech['name']} {tech['version']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
