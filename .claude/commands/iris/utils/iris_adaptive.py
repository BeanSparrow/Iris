#!/usr/bin/env python3
"""
Iris Adaptive Framework - Dynamic complexity-based adjustments
Analyzes project requirements and scales framework complexity accordingly

Version: 2.1.0
Changes in 2.1.0:
  - Added RefineConfig for Ralph Wiggum-style iterative refinement
  - Added refine_max_iterations, refine_reviewer_count to AdaptiveConfig
  - Minimum 5 iterations for refine phase (Ralph philosophy)

Changes in 2.0.0:
  - Removed ResearchOrchestrator class (research now handled by research.md)
  - Removed research_agents_count, skip_common_research from AdaptiveConfig
  - Research opportunities are now dynamically selected based on PRD analysis
"""

import json
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class ProjectComplexity(Enum):
    """Project complexity levels that drive framework behavior"""
    MICRO = "micro"      # < 1 day, 1-3 tasks, single feature
    SMALL = "small"      # 1-3 days, 4-10 tasks, 2-3 features  
    MEDIUM = "medium"    # 1-2 weeks, 11-30 tasks, 4-7 features
    LARGE = "large"      # 2-4 weeks, 31-60 tasks, 8-15 features
    ENTERPRISE = "enterprise"  # 4+ weeks, 60+ tasks, 15+ features

class ProjectType(Enum):
    """Project types for specialized handling"""
    SCRIPT = "script"              # Simple CLI script
    API_ENDPOINT = "api_endpoint"  # Single API endpoint/function
    FEATURE_ADD = "feature_add"    # Adding feature to existing code
    CRUD_APP = "crud_app"          # Basic CRUD application
    FULL_STACK = "full_stack"      # Complete web application
    MICROSERVICE = "microservice"  # Microservice architecture
    REFACTOR = "refactor"          # Code refactoring task
    BUG_FIX = "bug_fix"           # Bug fixing task

@dataclass
class AdaptiveConfig:
    """Configuration that adapts based on project complexity"""
    complexity: ProjectComplexity
    project_type: ProjectType

    # Feature limits
    max_mvp_features: int = field(init=False)
    min_mvp_features: int = field(init=False)

    # Milestone configuration
    tasks_per_milestone: Tuple[int, int] = field(init=False)  # (min, max)
    validation_frequency: str = field(init=False)  # "every", "major", "final"
    allow_parallel_milestones: bool = field(init=False)

    # Process configuration
    enforce_tdd: bool = field(init=False)
    require_validation_pause: bool = field(init=False)
    documentation_level: str = field(init=False)  # "minimal", "standard", "comprehensive"

    # Refine configuration (Ralph Wiggum-style iterative improvement)
    # Minimum 5 iterations to honor Ralph philosophy
    refine_max_iterations: int = field(init=False)
    refine_reviewer_count: int = field(init=False)
    refine_focus_areas: List[str] = field(init=False)

    # Note: Research configuration is now handled dynamically by research.md
    # based on PRD analysis, not fixed counts per complexity level

    def __post_init__(self):
        """Set configuration based on complexity and type"""
        self._configure_by_complexity()
        self._configure_refine()
        self._adjust_for_project_type()
    
    def _configure_by_complexity(self):
        """Base configuration by complexity level"""
        # Note: Research configuration removed - now handled dynamically by research.md
        configs = {
            ProjectComplexity.MICRO: {
                "max_mvp_features": 2,
                "min_mvp_features": 1,
                "tasks_per_milestone": (1, 3),
                "validation_frequency": "final",
                "allow_parallel_milestones": False,
                "enforce_tdd": False,
                "require_validation_pause": False,
                "documentation_level": "minimal"
            },
            ProjectComplexity.SMALL: {
                "max_mvp_features": 3,
                "min_mvp_features": 1,
                "tasks_per_milestone": (2, 5),
                "validation_frequency": "major",
                "allow_parallel_milestones": False,
                "enforce_tdd": True,
                "require_validation_pause": False,
                "documentation_level": "standard"
            },
            ProjectComplexity.MEDIUM: {
                "max_mvp_features": 7,
                "min_mvp_features": 3,
                "tasks_per_milestone": (3, 5),
                "validation_frequency": "every",
                "allow_parallel_milestones": True,
                "enforce_tdd": True,
                "require_validation_pause": True,
                "documentation_level": "standard"
            },
            ProjectComplexity.LARGE: {
                "max_mvp_features": 10,
                "min_mvp_features": 5,
                "tasks_per_milestone": (4, 7),
                "validation_frequency": "every",
                "allow_parallel_milestones": True,
                "enforce_tdd": True,
                "require_validation_pause": True,
                "documentation_level": "comprehensive"
            },
            ProjectComplexity.ENTERPRISE: {
                "max_mvp_features": 15,
                "min_mvp_features": 7,
                "tasks_per_milestone": (3, 5),  # Keep manageable
                "validation_frequency": "every",
                "allow_parallel_milestones": True,
                "enforce_tdd": True,
                "require_validation_pause": True,
                "documentation_level": "comprehensive"
            }
        }

        config = configs[self.complexity]
        for key, value in config.items():
            setattr(self, key, value)

    def _configure_refine(self):
        """Configure Ralph Wiggum-style refine phase based on complexity

        Key principle: Minimum 5 iterations to honor Ralph philosophy.
        The loop must run a fixed number of times - no early termination.
        """
        refine_configs = {
            ProjectComplexity.MICRO: {
                "refine_max_iterations": 5,  # Minimum for Ralph philosophy
                "refine_reviewer_count": 2,
                "refine_focus_areas": ["gaps", "quality"]
            },
            ProjectComplexity.SMALL: {
                "refine_max_iterations": 5,  # Minimum for Ralph philosophy
                "refine_reviewer_count": 3,
                "refine_focus_areas": ["gaps", "quality", "edge_cases"]
            },
            ProjectComplexity.MEDIUM: {
                "refine_max_iterations": 6,
                "refine_reviewer_count": 4,
                "refine_focus_areas": ["gaps", "quality", "integration", "edge_cases"]
            },
            ProjectComplexity.LARGE: {
                "refine_max_iterations": 8,
                "refine_reviewer_count": 5,
                "refine_focus_areas": ["gaps", "quality", "integration", "edge_cases", "security"]
            },
            ProjectComplexity.ENTERPRISE: {
                "refine_max_iterations": 10,
                "refine_reviewer_count": 6,
                "refine_focus_areas": ["gaps", "quality", "integration", "edge_cases", "security", "performance"]
            }
        }

        config = refine_configs[self.complexity]
        for key, value in config.items():
            setattr(self, key, value)

    def _adjust_for_project_type(self):
        """Fine-tune configuration based on project type"""
        # Note: Research adjustments removed - now handled dynamically by research.md
        adjustments = {
            ProjectType.SCRIPT: {
                "enforce_tdd": False,
                "tasks_per_milestone": (1, 2)
            },
            ProjectType.BUG_FIX: {
                "validation_frequency": "final",
                "enforce_tdd": True
            },
            ProjectType.REFACTOR: {
                "enforce_tdd": True,
                "documentation_level": "comprehensive"
            },
            ProjectType.API_ENDPOINT: {
                "enforce_tdd": True
            },
            ProjectType.MICROSERVICE: {
                "enforce_tdd": True,
                "documentation_level": "comprehensive"
            }
        }

        if self.project_type in adjustments:
            for key, value in adjustments[self.project_type].items():
                setattr(self, key, value)

class ProjectAnalyzer:
    """Analyzes PRD/requirements to determine project complexity and type"""
    
    # Keywords that indicate complexity
    COMPLEXITY_INDICATORS = {
        ProjectComplexity.MICRO: [
            r'\b(simple|basic|quick|small|tiny|mini)\b',
            r'\b(script|utility|helper|tool)\b',
            r'\b(one|single|just)\s+(feature|function|endpoint)\b'
        ],
        ProjectComplexity.SMALL: [
            r'\b(few|couple|several)\s+features?\b',
            r'\b(basic\s+app|simple\s+application)\b',
            r'\b(prototype|proof.of.concept|poc)\b'
        ],
        ProjectComplexity.MEDIUM: [
            r'\b(multiple\s+features?|several\s+components?)\b',
            r'\b(full\s+application|complete\s+system)\b',
            r'\b(dashboard|admin\s+panel|management)\b'
        ],
        ProjectComplexity.LARGE: [
            r'\b(comprehensive|extensive|complex|full-featured)\b',
            r'\b(enterprise|production|scalable)\b',
            r'\b(multiple\s+services?|microservices?)\b',
            r'\b(e-commerce|platform|marketplace)\b',
            r'\b(authentication|payment|notification|reporting)\b'
        ],
        ProjectComplexity.ENTERPRISE: [
            r'\b(enterprise.ready|production.ready|large.scale)\b',
            r'\b(kubernetes|docker|distributed|cloud.native)\b',
            r'\b(high.availability|fault.tolerant|auto.scaling)\b'
        ]
    }
    
    # Keywords that indicate project type
    TYPE_INDICATORS = {
        ProjectType.SCRIPT: [
            r'\b(cli|command.line|script|automation)\b',
            r'\b(batch|process|convert|transform)\b'
        ],
        ProjectType.API_ENDPOINT: [
            r'\b(api|endpoint|route|webhook)\b',
            r'\b(rest|graphql|grpc)\b'
        ],
        ProjectType.BUG_FIX: [
            r'\b(fix|bug|issue|problem|error)\b',
            r'\b(broken|failing|not.working)\b'
        ],
        ProjectType.REFACTOR: [
            r'\b(refactor|restructure|reorganize|optimize)\b',
            r'\b(clean.?up|improve|enhance)\s+code\b'
        ],
        ProjectType.CRUD_APP: [
            r'\b(crud|database|forms?|admin)\b',
            r'\b(create|read|update|delete)\b'
        ],
        ProjectType.FULL_STACK: [
            r'\b(full.?stack|web.?app|application)\b',
            r'\b(frontend|backend|database)\b',
            r'\b(e.?commerce|platform|marketplace)\b',
            r'\b(comprehensive|complete.*(system|app))\b'
        ],
        ProjectType.MICROSERVICE: [
            r'\b(microservice|service.oriented|distributed)\b',
            r'\b(kubernetes|docker|container)\b'
        ]
    }
    
    @classmethod
    def analyze(cls, prd_content: str, features_count: int = 0) -> AdaptiveConfig:
        """
        Analyze PRD content to determine complexity and type
        
        Args:
            prd_content: The PRD text or requirements description
            features_count: Number of features identified (if already parsed)
            
        Returns:
            AdaptiveConfig with appropriate settings
        """
        prd_lower = prd_content.lower()
        
        # Determine project type
        project_type = cls._determine_project_type(prd_lower)
        
        # Determine complexity
        complexity = cls._determine_complexity(prd_lower, features_count, project_type)
        
        return AdaptiveConfig(complexity=complexity, project_type=project_type)
    
    @classmethod
    def _determine_project_type(cls, prd_lower: str) -> ProjectType:
        """Determine project type from PRD content"""
        scores = {}
        
        for ptype, patterns in cls.TYPE_INDICATORS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, prd_lower))
                score += matches
            scores[ptype] = score
        
        # Return type with highest score, default to CRUD_APP
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                return best_type[0]
        
        return ProjectType.CRUD_APP
    
    @classmethod  
    def _determine_complexity(cls, prd_lower: str, features_count: int, 
                             project_type: ProjectType) -> ProjectComplexity:
        """Determine project complexity from multiple factors"""
        
        # Start with feature count heuristic
        if features_count > 0:
            if features_count <= 1:
                complexity = ProjectComplexity.MICRO
            elif features_count <= 3:
                complexity = ProjectComplexity.SMALL
            elif features_count <= 7:
                complexity = ProjectComplexity.MEDIUM
            elif features_count <= 12:
                complexity = ProjectComplexity.LARGE
            else:
                complexity = ProjectComplexity.ENTERPRISE
        else:
            complexity = ProjectComplexity.MEDIUM  # Default
        
        # Check for explicit complexity indicators
        complexity_bumps = 0
        for comp_level, patterns in cls.COMPLEXITY_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, prd_lower):
                    # Count complexity-increasing patterns
                    if comp_level in [ProjectComplexity.LARGE, ProjectComplexity.ENTERPRISE]:
                        complexity_bumps += 1
                    
                    # Micro/Small indicators override upward
                    if comp_level in [ProjectComplexity.MICRO, ProjectComplexity.SMALL]:
                        complexity = min(complexity, comp_level, key=lambda x: list(ProjectComplexity).index(x))
                    # Large indicators override downward
                    elif comp_level in [ProjectComplexity.LARGE, ProjectComplexity.ENTERPRISE]:
                        complexity = max(complexity, comp_level, key=lambda x: list(ProjectComplexity).index(x))
        
        # If multiple large-scale patterns detected, boost complexity
        if complexity_bumps >= 3:
            complexity = ProjectComplexity.LARGE
        elif complexity_bumps >= 5:
            complexity = ProjectComplexity.ENTERPRISE
        
        # Adjust based on project type
        if project_type in [ProjectType.SCRIPT, ProjectType.BUG_FIX]:
            # These are typically smaller
            complexity = min(complexity, ProjectComplexity.SMALL, 
                           key=lambda x: list(ProjectComplexity).index(x))
        elif project_type == ProjectType.MICROSERVICE:
            # These are typically larger
            complexity = max(complexity, ProjectComplexity.LARGE,
                           key=lambda x: list(ProjectComplexity).index(x))
        
        # Check document length as final factor
        word_count = len(prd_lower.split())
        if word_count < 100:
            complexity = min(complexity, ProjectComplexity.SMALL,
                           key=lambda x: list(ProjectComplexity).index(x))
        elif word_count > 1000:
            complexity = max(complexity, ProjectComplexity.LARGE,
                           key=lambda x: list(ProjectComplexity).index(x))
        
        return complexity

# Note: ResearchOrchestrator class has been removed in v2.0.0
# Research is now handled dynamically by research.md which:
# - Analyzes PRD to select research opportunities from a catalog
# - Launches parallel general-purpose subagents for web research
# - Verifies technology choices from official sources
# - Stores results with confidence levels in the database
# See: .claude/commands/iris/research.md

class MilestoneGenerator:
    """Generates milestone structure based on project complexity"""
    
    @classmethod
    def generate_milestones(cls, tasks: List[Dict], config: AdaptiveConfig) -> List[Dict]:
        """
        Generate milestone structure adapted to project complexity
        
        Args:
            tasks: List of task dictionaries
            config: Adaptive configuration
            
        Returns:
            List of milestone dictionaries
        """
        milestones = []
        min_tasks, max_tasks = config.tasks_per_milestone
        
        # For micro projects, single milestone
        if config.complexity == ProjectComplexity.MICRO:
            milestones.append({
                "id": "M1",
                "name": "Complete Implementation",
                "tasks": [t["id"] for t in tasks],
                "validation_required": config.validation_frequency != "none",
                "launch_ready": True
            })
            return milestones
        
        # Dynamic milestone creation
        current_milestone_tasks = []
        milestone_count = 1
        
        for i, task in enumerate(tasks):
            current_milestone_tasks.append(task["id"])
            
            # Check if we should create a milestone
            should_create = (
                len(current_milestone_tasks) >= min_tasks and (
                    len(current_milestone_tasks) >= max_tasks or
                    cls._is_logical_boundary(task, tasks, i) or
                    i == len(tasks) - 1
                )
            )
            
            if should_create:
                milestone = {
                    "id": f"M{milestone_count}",
                    "name": cls._generate_milestone_name(milestone_count, config),
                    "tasks": current_milestone_tasks.copy(),
                    "validation_required": cls._should_validate(milestone_count, config),
                    "launch_ready": milestone_count > 0,  # All milestones launch-ready
                    "can_parallel": config.allow_parallel_milestones and milestone_count > 1
                }
                
                # Add validation task if needed
                if milestone["validation_required"]:
                    val_task_id = f"T-VAL-M{milestone_count}"
                    milestone["tasks"].append(val_task_id)
                    milestone["validation_task"] = val_task_id
                
                milestones.append(milestone)
                current_milestone_tasks = []
                milestone_count += 1
        
        return milestones
    
    @classmethod
    def _is_logical_boundary(cls, task: Dict, all_tasks: List[Dict], index: int) -> bool:
        """Detect if this task represents a logical boundary for milestone"""
        # Check if next task has different feature prefix
        if index < len(all_tasks) - 1:
            current_prefix = task["id"].split("-")[1]
            next_prefix = all_tasks[index + 1]["id"].split("-")[1]
            return current_prefix != next_prefix
        return False
    
    @classmethod
    def _should_validate(cls, milestone_num: int, config: AdaptiveConfig) -> bool:
        """Determine if milestone needs validation"""
        if config.validation_frequency == "every":
            return True
        elif config.validation_frequency == "major":
            # Validate every 3rd milestone and final
            return milestone_num % 3 == 0
        elif config.validation_frequency == "final":
            return False  # Will be set to True for last milestone elsewhere
        return False
    
    @classmethod
    def _generate_milestone_name(cls, num: int, config: AdaptiveConfig) -> str:
        """Generate appropriate milestone name"""
        if config.complexity == ProjectComplexity.MICRO:
            return "Complete Implementation"
        
        names_by_position = {
            1: "Foundation & Setup",
            2: "Core Features",
            3: "Enhanced Functionality", 
            4: "Integration & Polish",
            5: "Advanced Features",
            6: "Optimization & Scaling"
        }
        
        return names_by_position.get(num, f"Milestone {num}")


def main():
    """Example usage and testing"""

    # Example PRD for testing
    example_prd_micro = """
    Create a simple Python script to convert CSV files to JSON format.
    It should handle basic error cases and support command line arguments.
    """

    example_prd_large = """
    Build a comprehensive e-commerce platform with microservices architecture.
    Features include user authentication, product catalog, shopping cart,
    payment processing, order management, inventory tracking, reporting dashboard,
    email notifications, and admin panel. Must be scalable and enterprise-ready
    with multiple services handling authentication, payment, notification and
    reporting capabilities.
    """

    # Analyze micro project
    print("=" * 60)
    print("MICRO PROJECT ANALYSIS")
    print("=" * 60)
    config_micro = ProjectAnalyzer.analyze(example_prd_micro, features_count=1)
    print(f"Complexity: {config_micro.complexity.value}")
    print(f"Type: {config_micro.project_type.value}")
    print(f"Max Features: {config_micro.max_mvp_features}")
    print(f"Tasks per Milestone: {config_micro.tasks_per_milestone}")
    print(f"TDD Required: {config_micro.enforce_tdd}")
    print(f"Research: Dynamic (handled by research.md)")
    print(f"Refine Iterations: {config_micro.refine_max_iterations}")
    print(f"Refine Reviewers: {config_micro.refine_reviewer_count}")
    print(f"Refine Focus: {', '.join(config_micro.refine_focus_areas)}")

    # Analyze large project
    print("\n" + "=" * 60)
    print("LARGE PROJECT ANALYSIS")
    print("=" * 60)
    config_large = ProjectAnalyzer.analyze(example_prd_large, features_count=10)
    print(f"Complexity: {config_large.complexity.value}")
    print(f"Type: {config_large.project_type.value}")
    print(f"Max Features: {config_large.max_mvp_features}")
    print(f"Tasks per Milestone: {config_large.tasks_per_milestone}")
    print(f"TDD Required: {config_large.enforce_tdd}")
    print(f"Research: Dynamic (handled by research.md)")
    print(f"Refine Iterations: {config_large.refine_max_iterations}")
    print(f"Refine Reviewers: {config_large.refine_reviewer_count}")
    print(f"Refine Focus: {', '.join(config_large.refine_focus_areas)}")

    print("\n" + "=" * 60)
    print("RESEARCH NOTE")
    print("=" * 60)
    print("Research is now handled dynamically by research.md")
    print("- Research opportunities selected based on PRD gaps")
    print("- Parallel subagents perform actual web research")
    print("- Results stored with confidence levels")
    print("See: .claude/commands/iris/research.md")

    print("\n" + "=" * 60)
    print("REFINE NOTE (Ralph Wiggum Philosophy)")
    print("=" * 60)
    print("Refine phase implements Ralph Wiggum-style iteration:")
    print("- Minimum 5 iterations (never exit early)")
    print("- Parallel review agents with fresh context")
    print("- Single refiner agent receives PRD each iteration")
    print("- Progress persists in files/git, not context")
    print("See: .claude/commands/iris/refine.md")

if __name__ == "__main__":
    main()