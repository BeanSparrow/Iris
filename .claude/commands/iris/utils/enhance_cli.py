#!/usr/bin/env python3
"""
IRIS SQLite-based Enhancement CLI

Provides feature enhancement capabilities using SQLite database instead of JSON files.
Maintains same API compatibility as original enhance_cli.py.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from database.db_manager import DatabaseManager


@dataclass
class FeatureAnalysis:
    """Analysis of a feature enhancement request"""
    feature_id: str
    description: str
    complexity: str  # low, medium, high
    estimated_tasks: int
    new_technologies: List[str]
    impact_assessment: str


@dataclass
class InsertionOption:
    """Option for where to insert enhancement tasks"""
    target_milestone_id: str
    milestone_name: str
    insertion_point: str  # before, after, new_milestone
    impact_score: int
    feasibility: str  # high, medium, low


class EnhanceCLI:
    """SQLite-based enhancement system"""
    
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
    
    def analyze_feature(self, description: str) -> FeatureAnalysis:
        """Analyze feature request and determine complexity"""
        feature_id = f"FEAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Simple complexity analysis (could be enhanced with ML)
        word_count = len(description.split())
        complexity_keywords = {
            'high': ['integration', 'authentication', 'payment', 'security', 'real-time', 'distributed'],
            'medium': ['api', 'database', 'user', 'interface', 'workflow', 'process'],
            'low': ['display', 'format', 'simple', 'basic', 'show', 'list']
        }
        
        complexity = 'medium'  # default
        for level, keywords in complexity_keywords.items():
            if any(keyword in description.lower() for keyword in keywords):
                complexity = level
                break
        
        # Estimate tasks based on complexity and description length
        base_tasks = {'low': 2, 'medium': 4, 'high': 8}[complexity]
        estimated_tasks = base_tasks + (word_count // 10)  # Add tasks for detailed descriptions
        
        # Extract potential new technologies (simple keyword matching)
        tech_keywords = ['react', 'vue', 'angular', 'node', 'python', 'postgres', 'redis', 'mongodb', 'kafka']
        new_technologies = [tech for tech in tech_keywords if tech in description.lower()]
        
        return FeatureAnalysis(
            feature_id=feature_id,
            description=description,
            complexity=complexity,
            estimated_tasks=estimated_tasks,
            new_technologies=new_technologies,
            impact_assessment=complexity
        )
    
    def find_insertion_options(self, analysis: FeatureAnalysis) -> List[InsertionOption]:
        """Find suitable places to insert enhancement tasks"""
        try:
            with self.db.get_connection() as conn:
                # Get all milestones with task counts
                milestones = conn.execute("""
                    SELECT 
                        m.id, m.name, m.status, m.order_index,
                        COUNT(t.id) as task_count,
                        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_count
                    FROM milestones m
                    LEFT JOIN tasks t ON m.id = t.milestone_id
                    GROUP BY m.id, m.name, m.status, m.order_index
                    ORDER BY m.order_index
                """).fetchall()
                
                options = []
                
                for milestone in milestones:
                    # Calculate impact score based on milestone status and task count
                    impact_score = 0
                    feasibility = 'high'
                    
                    if milestone['status'] == 'completed':
                        impact_score = 10  # High impact to reopen completed milestone
                        feasibility = 'low'
                    elif milestone['status'] == 'in_progress':
                        impact_score = 5  # Medium impact
                        feasibility = 'medium'
                    else:  # pending
                        impact_score = 1  # Low impact
                        feasibility = 'high'
                    
                    # Adjust for task count (prefer milestones with fewer tasks)
                    impact_score += milestone['task_count'] // 3
                    
                    options.append(InsertionOption(
                        target_milestone_id=milestone['id'],
                        milestone_name=milestone['name'],
                        insertion_point='append',
                        impact_score=impact_score,
                        feasibility=feasibility
                    ))
                
                # Add option for new milestone
                max_order = max([m['order_index'] for m in milestones]) if milestones else 0
                options.append(InsertionOption(
                    target_milestone_id=f"MILESTONE-{analysis.feature_id}",
                    milestone_name=f"Enhancement: {analysis.description[:30]}...",
                    insertion_point='new_milestone',
                    impact_score=0,  # No impact on existing milestones
                    feasibility='high'
                ))
                
                # Sort by feasibility and impact score
                feasibility_order = {'high': 0, 'medium': 1, 'low': 2}
                options.sort(key=lambda x: (feasibility_order[x.feasibility], x.impact_score))
                
                return options
                
        except Exception as e:
            print(f"❌ Failed to find insertion options: {e}")
            return []
    
    def apply_enhancement(self, analysis: FeatureAnalysis, insertion_option: InsertionOption) -> bool:
        """Apply enhancement by creating tasks in database"""
        try:
            # Create backup before major changes
            backup_path = self.db.backup_database()
            
            def apply_enhancement_operation(conn):
                # Create or update milestone
                if insertion_option.insertion_point == 'new_milestone':
                    # Create new milestone
                    max_order = conn.execute("SELECT MAX(order_index) as max_order FROM milestones").fetchone()
                    new_order = (max_order['max_order'] or 0) + 1
                    
                    conn.execute("""
                        INSERT INTO milestones (id, name, description, status, order_index)
                        VALUES (?, ?, ?, 'pending', ?)
                    """, (
                        insertion_option.target_milestone_id,
                        insertion_option.milestone_name,
                        f"Enhancement milestone for: {analysis.description}",
                        new_order
                    ))
                    
                    milestone_id = insertion_option.target_milestone_id
                else:
                    milestone_id = insertion_option.target_milestone_id
                
                # Get current task count in milestone for ordering
                task_count = conn.execute(
                    "SELECT COUNT(*) as count FROM tasks WHERE milestone_id = ?",
                    (milestone_id,)
                ).fetchone()
                start_order = task_count['count']
                
                # Generate enhancement tasks
                tasks = self._generate_enhancement_tasks(analysis, milestone_id, start_order)
                
                # Insert tasks
                for task in tasks:
                    conn.execute("""
                        INSERT INTO tasks 
                        (id, milestone_id, title, description, status, order_index, max_file_changes, scope_boundaries)
                        VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                    """, (
                        task['id'],
                        task['milestone_id'],
                        task['title'],
                        task['description'],
                        task['order_index'],
                        task['max_file_changes'],
                        json.dumps(task['scope_boundaries'])
                    ))
                
                # Insert task dependencies if any
                for task in tasks:
                    for dep_id in task.get('dependencies', []):
                        conn.execute("""
                            INSERT INTO task_dependencies (task_id, depends_on_task_id)
                            VALUES (?, ?)
                        """, (task['id'], dep_id))
                
                # Record enhancement in database
                conn.execute("""
                    INSERT INTO enhancements 
                    (id, feature_id, description, complexity, tasks_added, milestone_target, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """, (
                    analysis.feature_id,
                    analysis.feature_id,
                    analysis.description,
                    analysis.complexity,
                    len(tasks),
                    milestone_id
                ))
                
                # Add new technologies to stack if any
                for tech in analysis.new_technologies:
                    conn.execute("""
                        INSERT OR IGNORE INTO technologies
                        (name, category, needs_verification, decision_reason)
                        VALUES (?, 'enhancement', 1, ?)
                    """, (tech, f"Required for enhancement: {analysis.feature_id}"))
                
                # Update project totals
                new_total = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()
                conn.execute("""
                    UPDATE project_state 
                    SET value = ? 
                    WHERE key = 'total_tasks'
                """, (str(new_total['count']),))
                
                return {
                    "success": True,
                    "enhancement_id": analysis.feature_id,
                    "tasks_added": len(tasks),
                    "milestone_id": milestone_id,
                    "backup_created": backup_path
                }
            
            success, results = self.db.execute_transaction([apply_enhancement_operation])
            
            if success:
                result = results[0]
                print(f"✅ Enhancement applied: {result['tasks_added']} tasks added to {result['milestone_id']}")
                return result
            else:
                # Restore backup on failure
                self.db.restore_from_backup(backup_path)
                return {"error": "Failed to apply enhancement - transaction rolled back"}
                
        except Exception as e:
            print(f"❌ Failed to apply enhancement: {e}")
            return {"error": str(e)}
    
    def _generate_enhancement_tasks(self, analysis: FeatureAnalysis, milestone_id: str, start_order: int) -> List[Dict]:
        """Generate specific tasks for the enhancement"""
        tasks = []
        
        # Generate tasks based on complexity and description
        task_templates = {
            'low': [
                'Implement basic {feature} functionality',
                'Add {feature} UI components',
                'Test {feature} implementation'
            ],
            'medium': [
                'Design {feature} architecture',
                'Implement {feature} backend logic',
                'Create {feature} API endpoints',
                'Develop {feature} frontend interface',
                'Add {feature} validation and error handling',
                'Write {feature} tests and documentation'
            ],
            'high': [
                'Research {feature} requirements and dependencies',
                'Design {feature} system architecture',
                'Set up {feature} infrastructure',
                'Implement {feature} core services',
                'Develop {feature} API layer',
                'Create {feature} user interface',
                'Add {feature} security and validation',
                'Implement {feature} monitoring and logging',
                'Write comprehensive {feature} tests',
                'Create {feature} documentation and deployment guides'
            ]
        }
        
        templates = task_templates[analysis.complexity][:analysis.estimated_tasks]
        feature_name = analysis.description.split()[0:3]  # Use first few words as feature name
        feature_short = ' '.join(feature_name).lower()
        
        for i, template in enumerate(templates):
            task_id = f"{analysis.feature_id}-T{i+1:02d}"
            title = template.format(feature=feature_short)
            
            # Create dependencies (each task depends on the previous one)
            dependencies = [f"{analysis.feature_id}-T{i:02d}"] if i > 0 else []
            
            tasks.append({
                'id': task_id,
                'milestone_id': milestone_id,
                'title': title,
                'description': f"Enhancement task for: {analysis.description}",
                'order_index': start_order + i,
                'max_file_changes': 15 if analysis.complexity == 'high' else 10,
                'scope_boundaries': {
                    'must_implement': [feature_short],
                    'must_not_implement': ['unrelated-features'],
                    'enhancement_id': analysis.feature_id
                },
                'dependencies': dependencies
            })
        
        return tasks
    
    def list_enhancements(self) -> List[Dict]:
        """List all enhancements in the database"""
        try:
            with self.db.get_connection() as conn:
                enhancements = conn.execute("""
                    SELECT 
                        e.*,
                        m.name as milestone_name,
                        COUNT(t.id) as actual_tasks,
                        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
                    FROM enhancements e
                    LEFT JOIN milestones m ON e.milestone_target = m.id
                    LEFT JOIN tasks t ON t.milestone_id = e.milestone_target 
                        AND t.description LIKE '%' || e.feature_id || '%'
                    GROUP BY e.id
                    ORDER BY e.added_date DESC
                """).fetchall()
                
                return [dict(row) for row in enhancements]
                
        except Exception as e:
            print(f"❌ Failed to list enhancements: {e}")
            return []
    
    def get_enhancement_status(self, enhancement_id: str) -> Optional[Dict]:
        """Get detailed status of specific enhancement"""
        try:
            with self.db.get_connection() as conn:
                enhancement = conn.execute(
                    "SELECT * FROM enhancements WHERE id = ?",
                    (enhancement_id,)
                ).fetchone()
                
                if not enhancement:
                    return None
                
                # Get related tasks
                tasks = conn.execute("""
                    SELECT * FROM tasks 
                    WHERE milestone_id = ? 
                    AND (description LIKE '%' || ? || '%' OR id LIKE ? || '%')
                    ORDER BY order_index
                """, (
                    enhancement['milestone_target'],
                    enhancement['feature_id'],
                    enhancement['feature_id']
                )).fetchall()
                
                return {
                    'enhancement': dict(enhancement),
                    'tasks': [dict(task) for task in tasks],
                    'summary': {
                        'total_tasks': len(tasks),
                        'completed_tasks': len([t for t in tasks if t['status'] == 'completed']),
                        'progress_percentage': (len([t for t in tasks if t['status'] == 'completed']) / len(tasks) * 100) if tasks else 0
                    }
                }
                
        except Exception as e:
            print(f"❌ Failed to get enhancement status: {e}")
            return None


def main():
    """CLI interface for enhancement system"""
    parser = argparse.ArgumentParser(description='IRIS SQLite Enhancement CLI')
    parser.add_argument('action', choices=[
        'analyze', 'add', 'list', 'status', 'options'
    ])
    parser.add_argument('description', nargs='?', help='Feature description for analyze/add actions')
    parser.add_argument('--enhancement-id', help='Enhancement ID for status action')
    parser.add_argument('--milestone-id', help='Target milestone ID for add action')
    parser.add_argument('--db-path', help='Path to database file')
    
    args = parser.parse_args()
    
    try:
        enhance_cli = EnhanceCLI(args.db_path)
        
        if args.action == 'analyze':
            if not args.description:
                print("❌ Description required for analyze action")
                sys.exit(1)
                
            analysis = enhance_cli.analyze_feature(args.description)
            print(json.dumps({
                'feature_id': analysis.feature_id,
                'description': analysis.description,
                'complexity': analysis.complexity,
                'estimated_tasks': analysis.estimated_tasks,
                'new_technologies': analysis.new_technologies,
                'impact_assessment': analysis.impact_assessment
            }, indent=2))
        
        elif args.action == 'add':
            if not args.description:
                print("❌ Description required for add action")
                sys.exit(1)
            
            # Analyze the feature
            analysis = enhance_cli.analyze_feature(args.description)
            
            # Find insertion options
            options = enhance_cli.find_insertion_options(analysis)
            if not options:
                print("❌ No suitable insertion points found")
                sys.exit(1)
            
            # Use specified milestone or best option
            if args.milestone_id:
                selected_option = next((opt for opt in options if opt.target_milestone_id == args.milestone_id), None)
                if not selected_option:
                    print(f"❌ Milestone {args.milestone_id} not found in options")
                    sys.exit(1)
            else:
                selected_option = options[0]  # Best option
            
            # Apply enhancement
            result = enhance_cli.apply_enhancement(analysis, selected_option)
            print(json.dumps(result, indent=2, default=str))
        
        elif args.action == 'list':
            enhancements = enhance_cli.list_enhancements()
            print(json.dumps(enhancements, indent=2, default=str))
        
        elif args.action == 'status':
            if not args.enhancement_id:
                print("❌ Enhancement ID required for status action")
                sys.exit(1)
            
            status = enhance_cli.get_enhancement_status(args.enhancement_id)
            if status:
                print(json.dumps(status, indent=2, default=str))
            else:
                print(f"❌ Enhancement {args.enhancement_id} not found")
                sys.exit(1)
        
        elif args.action == 'options':
            if not args.description:
                print("❌ Description required for options action")
                sys.exit(1)
            
            analysis = enhance_cli.analyze_feature(args.description)
            options = enhance_cli.find_insertion_options(analysis)
            
            print(json.dumps([{
                'target_milestone_id': opt.target_milestone_id,
                'milestone_name': opt.milestone_name,
                'insertion_point': opt.insertion_point,
                'impact_score': opt.impact_score,
                'feasibility': opt.feasibility
            } for opt in options], indent=2))
        
    except Exception as e:
        print(f"❌ Enhancement CLI error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()