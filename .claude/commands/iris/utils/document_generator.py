#!/usr/bin/env python3
"""
IRIS Document Generator

Centralized documentation generation for the IRIS framework.
Handles README.md, PROJECT_STATUS.md, and COMPLETION_REPORT.md generation.

Modes:
- Standalone: Analyzes existing project without IRIS database
- Loop: Updates documentation from IRIS database state
- Final: Generates completion report with KPIs
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Add utils to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager


@dataclass
class ProjectKPIs:
    """Key Performance Indicators for project completion"""
    total_time_minutes: float = 0.0
    tasks_completed: int = 0
    tasks_total: int = 0
    milestones_completed: int = 0
    milestones_total: int = 0
    validations_passed: int = 0
    validations_total: int = 0
    errors_recovered: int = 0
    avg_task_duration_minutes: float = 0.0
    files_modified: int = 0
    project_complexity: str = "unknown"
    project_type: str = "unknown"


@dataclass
class MilestoneInfo:
    """Information about a milestone for documentation"""
    id: str
    name: str
    description: str
    status: str
    tasks_completed: int
    tasks_total: int
    features: List[str] = field(default_factory=list)


class DocumentGenerator:
    """Generates and maintains project documentation"""

    def __init__(self, db_manager: Optional[DatabaseManager], project_root: str, iris_dir: str):
        self.db = db_manager
        self.project_root = Path(project_root)
        self.iris_dir = Path(iris_dir)
        self.has_database = db_manager is not None

    # =========================================================================
    # README.md Generation
    # =========================================================================

    def generate_readme(self, mode: str = "update") -> str:
        """Generate or update README.md content"""

        if self.has_database:
            return self._generate_readme_from_db(mode)
        else:
            return self._generate_readme_standalone()

    def _generate_readme_from_db(self, mode: str) -> str:
        """Generate README from IRIS database state"""

        with self.db.get_connection() as conn:
            # Get project metadata
            metadata = self._get_metadata_dict(conn)

            # Get milestones and their features
            milestones = self._get_milestone_info(conn)

            # Get technology stack
            technologies = conn.execute(
                "SELECT name, category, version FROM technologies"
            ).fetchall()

            # Build README content
            project_name = metadata.get('project_name', self.project_root.name)
            project_desc = metadata.get('project_description', 'An IRIS-managed project')

            # Determine which features are complete
            completed_features = []
            planned_features = []

            for milestone in milestones:
                if milestone.status in ['completed', 'validated']:
                    completed_features.extend(milestone.features)
                else:
                    planned_features.extend(milestone.features)

            # Build tech stack section
            tech_by_category = {}
            for tech in technologies:
                category = tech['category'] or 'other'
                if category not in tech_by_category:
                    tech_by_category[category] = []
                tech_by_category[category].append(f"{tech['name']} {tech['version'] or ''}".strip())

            # Generate installation instructions based on tech
            install_instructions = self._generate_install_instructions(tech_by_category)

            # Calculate progress
            total_tasks = sum(m.tasks_total for m in milestones)
            completed_tasks = sum(m.tasks_completed for m in milestones)
            progress_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Build README
            readme = f"""# {project_name}

{project_desc}

"""

            # Status badge (text-based)
            if progress_pct >= 100:
                readme += "**Status:** Complete\n\n"
            else:
                readme += f"**Status:** In Development ({progress_pct:.0f}% complete)\n\n"

            # Features section
            if completed_features or planned_features:
                readme += "## Features\n\n"

                if completed_features:
                    for feature in completed_features:
                        readme += f"- [x] {feature}\n"

                if planned_features and mode != "final":
                    for feature in planned_features:
                        readme += f"- [ ] {feature}\n"

                readme += "\n"

            # Tech Stack
            if tech_by_category:
                readme += "## Tech Stack\n\n"
                for category, techs in tech_by_category.items():
                    readme += f"**{category.title()}:** {', '.join(techs)}\n"
                readme += "\n"

            # Installation
            readme += "## Installation\n\n"
            readme += install_instructions + "\n\n"

            # Usage
            readme += "## Usage\n\n"
            readme += "```bash\n"
            readme += "# Add usage examples here\n"
            readme += "```\n\n"

            # Development
            readme += "## Development\n\n"
            readme += "This project was developed using the IRIS autonomous development framework.\n\n"

            # License placeholder
            readme += "## License\n\n"
            readme += "See LICENSE file for details.\n\n"

            # Footer
            readme += "---\n"
            readme += f"*Documentation generated by IRIS on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"

            return readme

    def _generate_readme_standalone(self) -> str:
        """Generate README by analyzing existing project structure"""

        project_name = self.project_root.name

        # Detect project type and tech stack
        tech_stack = self._detect_tech_stack()
        install_instructions = self._generate_install_instructions(tech_stack)

        readme = f"""# {project_name}

Project description goes here.

## Features

- Feature 1
- Feature 2

## Tech Stack

"""

        for category, techs in tech_stack.items():
            readme += f"**{category.title()}:** {', '.join(techs)}\n"

        readme += f"""
## Installation

{install_instructions}

## Usage

```bash
# Add usage examples here
```

## License

See LICENSE file for details.

---
*Documentation generated by IRIS on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        return readme

    def _detect_tech_stack(self) -> Dict[str, List[str]]:
        """Detect technology stack from project files"""

        tech_stack = {}

        # Node.js
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                    tech_stack['runtime'] = ['Node.js']

                    # Detect frameworks
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    if 'react' in deps:
                        tech_stack['framework'] = ['React']
                    elif 'vue' in deps:
                        tech_stack['framework'] = ['Vue.js']
                    elif 'express' in deps:
                        tech_stack['framework'] = ['Express.js']
            except:
                pass

        # Python
        if (self.project_root / "requirements.txt").exists() or \
           (self.project_root / "pyproject.toml").exists():
            tech_stack['runtime'] = tech_stack.get('runtime', []) + ['Python']

        # Go
        if (self.project_root / "go.mod").exists():
            tech_stack['runtime'] = tech_stack.get('runtime', []) + ['Go']

        # Rust
        if (self.project_root / "Cargo.toml").exists():
            tech_stack['runtime'] = tech_stack.get('runtime', []) + ['Rust']

        return tech_stack

    def _generate_install_instructions(self, tech_stack: Dict[str, List[str]]) -> str:
        """Generate installation instructions based on tech stack"""

        instructions = []

        runtimes = tech_stack.get('runtime', [])

        if 'Node.js' in runtimes:
            instructions.append("```bash\nnpm install\n```")

        if 'Python' in runtimes:
            instructions.append("```bash\npip install -r requirements.txt\n```")

        if 'Go' in runtimes:
            instructions.append("```bash\ngo mod download\n```")

        if 'Rust' in runtimes:
            instructions.append("```bash\ncargo build\n```")

        if not instructions:
            return "```bash\n# Installation instructions\n```"

        return "\n\n".join(instructions)

    def _get_metadata_dict(self, conn) -> Dict[str, str]:
        """Get project metadata as dictionary"""
        rows = conn.execute("SELECT key, value FROM project_metadata").fetchall()
        return {row['key']: row['value'] for row in rows}

    def _get_milestone_info(self, conn) -> List[MilestoneInfo]:
        """Get milestone information with features"""

        milestones_data = conn.execute("""
            SELECT
                m.id, m.name, m.description, m.status,
                COUNT(t.id) as tasks_total,
                COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as tasks_completed
            FROM milestones m
            LEFT JOIN tasks t ON m.id = t.milestone_id
            GROUP BY m.id
            ORDER BY m.order_index
        """).fetchall()

        milestones = []
        for row in milestones_data:
            # Extract features from milestone name/description
            features = []
            if row['name']:
                features.append(row['name'])

            milestones.append(MilestoneInfo(
                id=row['id'],
                name=row['name'] or '',
                description=row['description'] or '',
                status=row['status'] or 'pending',
                tasks_completed=row['tasks_completed'] or 0,
                tasks_total=row['tasks_total'] or 0,
                features=features
            ))

        return milestones

    # =========================================================================
    # PROJECT_STATUS.md Generation
    # =========================================================================

    def generate_project_status(self) -> str:
        """Generate PROJECT_STATUS.md content"""

        if not self.has_database:
            return self._generate_status_standalone()

        with self.db.get_connection() as conn:
            # Get statistics
            task_stats = conn.execute("""
                SELECT
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_tasks,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks
                FROM tasks
            """).fetchone()

            milestone_stats = conn.execute("""
                SELECT
                    COUNT(*) as total_milestones,
                    COUNT(CASE WHEN status IN ('completed', 'validated') THEN 1 END) as completed_milestones
                FROM milestones
            """).fetchone()

            # Get milestones with progress
            milestones = self._get_milestone_info(conn)

            # Get current task
            current_task = conn.execute("""
                SELECT t.id, t.title, t.started_at, m.name as milestone_name
                FROM tasks t
                JOIN milestones m ON t.milestone_id = m.id
                WHERE t.status = 'in_progress'
                LIMIT 1
            """).fetchone()

            # Get next eligible tasks
            next_tasks = conn.execute("""
                SELECT t.id, t.title, m.name as milestone_name
                FROM tasks t
                JOIN milestones m ON t.milestone_id = m.id
                WHERE t.status = 'pending'
                AND NOT EXISTS (
                    SELECT 1 FROM task_dependencies td
                    JOIN tasks dep ON td.depends_on_task_id = dep.id
                    WHERE td.task_id = t.id AND dep.status != 'completed'
                )
                ORDER BY m.order_index, t.order_index
                LIMIT 3
            """).fetchall()

            # Calculate progress
            total = task_stats['total_tasks']
            completed = task_stats['completed_tasks']
            progress_pct = (completed / total * 100) if total > 0 else 0

            # Build status markdown
            status = f"""# Project Status

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Progress

| Metric | Value |
|--------|-------|
| Total Tasks | {total} |
| Completed | {completed} |
| In Progress | {task_stats['active_tasks']} |
| Pending | {task_stats['pending_tasks']} |
| **Progress** | **{progress_pct:.1f}%** |

## Milestones

"""

            for m in milestones:
                icon = {
                    'completed': '[x]',
                    'validated': '[x]',
                    'in_progress': '[-]',
                    'pending': '[ ]'
                }.get(m.status, '[ ]')

                m_progress = (m.tasks_completed / m.tasks_total * 100) if m.tasks_total > 0 else 0
                status += f"- {icon} **{m.name}** - {m.tasks_completed}/{m.tasks_total} tasks ({m_progress:.0f}%)\n"

            status += "\n"

            # Current activity
            status += "## Current Activity\n\n"
            if current_task:
                status += f"**Working on:** {current_task['id']} - {current_task['title']}\n"
                status += f"**Milestone:** {current_task['milestone_name']}\n"
                if current_task['started_at']:
                    status += f"**Started:** {current_task['started_at']}\n"
            else:
                status += "*No active tasks*\n"

            status += "\n"

            # Next up
            if next_tasks:
                status += "## Next Up\n\n"
                for i, task in enumerate(next_tasks, 1):
                    status += f"{i}. **{task['id']}** - {task['title']} *(in {task['milestone_name']})*\n"
                status += "\n"

            # Footer
            status += "---\n"
            status += "*Updated by IRIS Document Engine*\n"

            return status

    def _generate_status_standalone(self) -> str:
        """Generate basic status for non-IRIS projects"""
        return f"""# Project Status

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This project is not managed by IRIS. Run `/iris:plan` to create a sprint plan.

---
*Generated by IRIS Document Engine*
"""

    # =========================================================================
    # COMPLETION_REPORT.md Generation & KPIs
    # =========================================================================

    def calculate_kpis(self) -> ProjectKPIs:
        """Calculate project KPIs from database"""

        if not self.has_database:
            return ProjectKPIs()

        kpis = ProjectKPIs()

        with self.db.get_connection() as conn:
            # Get metadata
            metadata = self._get_metadata_dict(conn)
            kpis.project_complexity = metadata.get('project_complexity', 'unknown')
            kpis.project_type = metadata.get('project_type', 'unknown')

            # Calculate total time
            start_time = metadata.get('analysis_timestamp')
            end_time = metadata.get('autopilot_completed', datetime.now().isoformat())

            if start_time:
                try:
                    start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    kpis.total_time_minutes = (end - start).total_seconds() / 60
                except:
                    pass

            # Task stats
            task_stats = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    AVG(CASE WHEN duration_minutes > 0 THEN duration_minutes END) as avg_duration
                FROM tasks
            """).fetchone()

            kpis.tasks_total = task_stats['total'] or 0
            kpis.tasks_completed = task_stats['completed'] or 0
            kpis.avg_task_duration_minutes = task_stats['avg_duration'] or 0.0

            # Milestone stats
            milestone_stats = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status IN ('completed', 'validated') THEN 1 END) as completed
                FROM milestones
            """).fetchone()

            kpis.milestones_total = milestone_stats['total'] or 0
            kpis.milestones_completed = milestone_stats['completed'] or 0

            # Validation stats
            validation_stats = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN validation_status = 'passed' THEN 1 END) as passed
                FROM milestone_validations
            """).fetchone()

            kpis.validations_total = validation_stats['total'] or 0
            kpis.validations_passed = validation_stats['passed'] or 0

            # Error recovery count (check task_executions for retries)
            try:
                error_stats = conn.execute("""
                    SELECT COUNT(*) as recovered
                    FROM task_executions
                    WHERE attempt_number > 1
                """).fetchone()
                kpis.errors_recovered = error_stats['recovered'] or 0
            except:
                kpis.errors_recovered = 0

        return kpis

    def generate_completion_report(self, kpis: ProjectKPIs) -> str:
        """Generate COMPLETION_REPORT.md content"""

        with self.db.get_connection() as conn:
            metadata = self._get_metadata_dict(conn)
            project_name = metadata.get('project_name', self.project_root.name)

        task_pct = (kpis.tasks_completed / kpis.tasks_total * 100) if kpis.tasks_total > 0 else 0
        milestone_pct = (kpis.milestones_completed / kpis.milestones_total * 100) if kpis.milestones_total > 0 else 0
        validation_pct = (kpis.validations_passed / kpis.validations_total * 100) if kpis.validations_total > 0 else 100

        report = f"""# IRIS Completion Report

**Project:** {project_name}
**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Complexity:** {kpis.project_complexity.upper()}
**Type:** {kpis.project_type}

---

## Execution Metrics

| Metric | Value |
|--------|-------|
| Total Execution Time | {kpis.total_time_minutes:.1f} minutes |
| Tasks Completed | {kpis.tasks_completed} / {kpis.tasks_total} ({task_pct:.0f}%) |
| Milestones Completed | {kpis.milestones_completed} / {kpis.milestones_total} ({milestone_pct:.0f}%) |
| Average Task Duration | {kpis.avg_task_duration_minutes:.1f} minutes |

## Quality Metrics

| Metric | Value |
|--------|-------|
| Validations Passed | {kpis.validations_passed} / {kpis.validations_total} ({validation_pct:.0f}%) |
| Errors Recovered | {kpis.errors_recovered} |

## Project Artifacts

- `README.md` - Project documentation
- `PROJECT_STATUS.md` - Final status snapshot
- `.tasks/iris_project.db` - Complete project history

---

*Report generated by IRIS Document Engine*
"""

        return report

    def format_terminal_report(self, kpis: ProjectKPIs) -> str:
        """Format KPIs for terminal output"""

        with self.db.get_connection() as conn:
            metadata = self._get_metadata_dict(conn)
            project_name = metadata.get('project_name', self.project_root.name)

        task_pct = (kpis.tasks_completed / kpis.tasks_total * 100) if kpis.tasks_total > 0 else 0
        milestone_pct = (kpis.milestones_completed / kpis.milestones_total * 100) if kpis.milestones_total > 0 else 0
        validation_pct = (kpis.validations_passed / kpis.validations_total * 100) if kpis.validations_total > 0 else 100

        # Format time nicely
        if kpis.total_time_minutes >= 60:
            hours = int(kpis.total_time_minutes // 60)
            mins = int(kpis.total_time_minutes % 60)
            time_str = f"{hours}h {mins}m"
        else:
            time_str = f"{kpis.total_time_minutes:.0f} minutes"

        output = f"""
  PROJECT:        {project_name}
  STATUS:         COMPLETE
  COMPLEXITY:     {kpis.project_complexity.upper()}

  EXECUTION METRICS
  ─────────────────────────────────────────────────

  Total Time          {time_str}
  Tasks Completed     {kpis.tasks_completed} / {kpis.tasks_total} ({task_pct:.0f}%)
  Milestones          {kpis.milestones_completed} / {kpis.milestones_total} ({milestone_pct:.0f}%)
  Avg Task Duration   {kpis.avg_task_duration_minutes:.1f} minutes

  QUALITY METRICS
  ─────────────────────────────────────────────────

  Validations Passed  {kpis.validations_passed} / {kpis.validations_total} ({validation_pct:.0f}%)
  Errors Recovered    {kpis.errors_recovered}

  ─────────────────────────────────────────────────

  Documentation:      README.md, PROJECT_STATUS.md
  Full Report:        COMPLETION_REPORT.md
"""

        return output

    # =========================================================================
    # File Writers
    # =========================================================================

    def update_readme(self, mode: str = "update") -> bool:
        """Write README.md to project root"""
        try:
            content = self.generate_readme(mode)
            readme_path = self.project_root / "README.md"

            with open(readme_path, 'w') as f:
                f.write(content)

            print(f"  README.md updated")
            return True
        except Exception as e:
            print(f"  Failed to update README.md: {e}")
            return False

    def update_project_status(self) -> bool:
        """Write PROJECT_STATUS.md to project root"""
        try:
            content = self.generate_project_status()
            status_path = self.project_root / "PROJECT_STATUS.md"

            with open(status_path, 'w') as f:
                f.write(content)

            print(f"  PROJECT_STATUS.md updated")
            return True
        except Exception as e:
            print(f"  Failed to update PROJECT_STATUS.md: {e}")
            return False

    def write_completion_report(self) -> bool:
        """Write COMPLETION_REPORT.md to project root"""
        try:
            kpis = self.calculate_kpis()
            content = self.generate_completion_report(kpis)
            report_path = self.project_root / "COMPLETION_REPORT.md"

            with open(report_path, 'w') as f:
                f.write(content)

            print(f"  COMPLETION_REPORT.md created")
            return True
        except Exception as e:
            print(f"  Failed to create COMPLETION_REPORT.md: {e}")
            return False

    def print_terminal_report(self) -> None:
        """Print KPI report to terminal"""
        kpis = self.calculate_kpis()
        print(self.format_terminal_report(kpis))


def main():
    """CLI interface for document generation"""

    parser = argparse.ArgumentParser(description='IRIS Document Generator')
    parser.add_argument('--project-root', required=True, help='Project root directory')
    parser.add_argument('--iris-dir', required=True, help='IRIS commands directory')
    parser.add_argument('--milestone', help='Specific milestone ID to document')
    parser.add_argument('--final', action='store_true', help='Generate final completion report')
    parser.add_argument('--output-terminal', action='store_true', help='Output KPIs to terminal')
    parser.add_argument('--standalone', action='store_true', help='Standalone mode (no database)')

    args = parser.parse_args()

    project_root = Path(args.project_root)
    iris_dir = Path(args.iris_dir)

    # Initialize database if it exists
    db_path = project_root / ".tasks" / "iris_project.db"
    db_manager = None

    if db_path.exists() and not args.standalone:
        try:
            db_manager = DatabaseManager(str(db_path))
        except Exception as e:
            print(f"Warning: Could not connect to database: {e}")

    generator = DocumentGenerator(db_manager, str(project_root), str(iris_dir))

    print("IRIS Document Generator")
    print("=" * 40)

    if args.final:
        # Final mode: update all docs and generate completion report
        generator.update_readme(mode="final")
        generator.update_project_status()
        generator.write_completion_report()

        if args.output_terminal:
            generator.print_terminal_report()
    else:
        # Regular update mode
        generator.update_readme(mode="update")
        generator.update_project_status()

    print("=" * 40)
    print("Documentation update complete")


if __name__ == "__main__":
    main()
