---
allowed-tools:
  - Read
description: "Usage: /iris:help - Display Iris framework overview and commands"
---

**OUTPUT THE FOLLOWING EXACTLY AS IS - DO NOT ADD YOUR OWN TEXT**:

```
●
   ██ ██████  ██ ███████
   ██ ██   ██ ██ ██
   ██ ██████  ██ ███████
   ██ ██   ██ ██      ██
   ██ ██   ██ ██ ███████

           Autonomous Development Engine
           ------------------------------

IRIS transforms ideas into working applications autonomously. Provide requirements, enable dangerous permissions, and watch IRIS build your project from planning to completion without human intervention.

## 🚀 PRIMARY COMMAND

/iris:autopilot <PRD>       - 🚀 AUTONOMOUS DEVELOPMENT (Start here!)

## 🛠️ Manual Commands (for debugging/control)

/iris:plan <PRD>           - Manual sprint planning
/iris:execute [task-id]    - Manual task execution
/iris:validate [milestone] - Manual milestone validation
/iris:document [flags]     - Generate/update documentation
/iris:audit [scope]        - Essential security analysis

## ⚡ Quick Start - Autopilot Mode

1. Enable dangerous permissions: export CLAUDE_DANGEROUS_MODE=true
2. Run autopilot: /iris:autopilot "Build a task management API"
3. Monitor progress: watch cat PROJECT_STATUS.md
4. Check logs: tail -f .tasks/autopilot.log

## 🔧 Manual Mode (for step-by-step control)

1. Plan: /iris:plan "Your requirements"
2. Execute: /iris:execute
3. Validate: /iris:validate
4. Document: /iris:document
5. Audit: /iris:audit

## 📚 Document Command Flags

--standalone    Analyze existing project without IRIS database
--research      Generate TECH_DECISIONS.md from research results
--milestone M1  Update docs for specific milestone
--final         Generate COMPLETION_REPORT.md with KPIs

## 🔬 How Research Works

IRIS uses dynamic, PRD-driven research with prose-orchestration:

1. Foundation   - Analyze PRD, select research opportunities
2. Parallel     - Launch subagents to research technologies
3. Reconcile    - Verify coherence, commit approved stack

Research output: TECH_DECISIONS.md (technology choices with rationale)

IRIS uses adaptive complexity scaling, prose-orchestration, and dynamic research to deliver prototypes autonomously.
```