# Documentation Upgrade Plan

**Branch:** TBD (future work)
**Status:** Planned
**Last Updated:** 2024-12-30

---

## Table of Contents

1. [Objective](#objective)
2. [Current State](#current-state)
3. [Documentation Goals](#documentation-goals)
4. [Proposed Structure](#proposed-structure)
5. [Document Specifications](#document-specifications)
6. [Implementation Order](#implementation-order)
7. [Open Questions](#open-questions)

---

## Objective

Establish comprehensive documentation for the Iris framework that serves:
- **Your understanding** - How does this all fit together? What are the design decisions?
- **Other users' understanding** - How do I use this? How does it work?
- **Change management** - What exists? How do I safely modify it?
- **AI collaboration** - What context does Claude need to pick up and contribute?

---

## Current State

### Existing Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `README.md` | User-facing overview | Exists |
| `QUICKSTART.md` | Getting started guide | Exists |
| `PROCESS_FLOWS.md` | Visual flow diagrams | Exists, needs update |
| `SQLITE_ARCHITECTURE.md` | Database design | Exists |
| Command `.md` files | Executable instructions | Exists |

### Gaps Identified

1. **No architecture overview** - How components relate to each other
2. **No design principles doc** - Why decisions were made
3. **No change tracking** - No changelog, no decision records
4. **No AI context file** - Claude has to rediscover context each session
5. **No component-level docs** - Commands are executable but not explained
6. **No examples** - Sample PRDs and expected outcomes

---

## Documentation Goals

### Goal 1: Self-Understanding
Enable the maintainer (you) to:
- Quickly recall how the system works after time away
- Understand the rationale behind design decisions
- Identify safe modification points

### Goal 2: User Adoption
Enable new users to:
- Understand what Iris does and why they'd use it
- Get started quickly with clear examples
- Troubleshoot common issues

### Goal 3: Change Management
Enable safe evolution by:
- Tracking what changed and when
- Recording why decisions were made
- Documenting the current state before changes

### Goal 4: AI Collaboration
Enable Claude to:
- Quickly orient to the project
- Understand conventions and patterns
- Make consistent contributions
- Pick up where previous sessions left off

---

## Proposed Structure

### Tier 1: User-Facing (External)
*For users who want to USE Iris*

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| `README.md` | What is Iris, quick start, basic usage | New users | Exists, may need update |
| `QUICKSTART.md` | Step-by-step first project | New users | Exists |
| `COMMANDS.md` | Reference for all `/iris:*` commands | All users | **NEW** |
| `EXAMPLES.md` | Sample PRDs and expected outcomes | All users | **NEW** |
| `FAQ.md` | Common questions and troubleshooting | All users | **NEW** |

### Tier 2: Architecture (Internal)
*For contributors and future self*

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| `ARCHITECTURE.md` | High-level system design, component relationships, data flow | Contributors, AI | **NEW** |
| `DESIGN_PRINCIPLES.md` | Philosophy, why prose-orchestration, decision rationale | Contributors, AI | **NEW** |
| `SQLITE_ARCHITECTURE.md` | Database schema and patterns | Contributors | Exists, needs update |
| `SCHEMA_REFERENCE.md` | Complete schema reference with all tables, columns, relationships | Contributors, AI | **NEW** |
| `PROCESS_FLOWS.md` | Visual flow diagrams | Contributors, AI | Exists, needs update |

### Tier 3: Component Documentation
*Detailed docs for each major component*

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| `docs/commands/plan.md` | How plan.md works, what it does, how to modify | Contributors | **NEW** |
| `docs/commands/execute.md` | How execute.md works | Contributors | **NEW** |
| `docs/commands/validate.md` | How validate.md works | Contributors | **NEW** |
| `docs/commands/document.md` | How document.md works | Contributors | **NEW** |
| `docs/commands/research.md` | How research.md works | Contributors | **NEW** |
| `docs/commands/autopilot.md` | How autopilot.md works | Contributors | **NEW** |
| `docs/commands/audit.md` | How audit.md works | Contributors | **NEW** |
| `docs/utilities/README.md` | Overview of Python utilities | Contributors | **NEW** |
| `docs/utilities/*.md` | Documentation for each utility | Contributors | **NEW** |

### Tier 4: Change Management
*For tracking decisions and changes*

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| `CHANGELOG.md` | What changed in each version | All | **NEW** |
| `docs/decisions/README.md` | Index of Architecture Decision Records | Contributors, AI | **NEW** |
| `docs/decisions/NNN-*.md` | Individual ADRs | Contributors, AI | **NEW** |
| `docs/upgrades/*.md` | Upgrade plans (like RESEARCH_UPGRADE_PLAN.md) | Contributors | Exists (ad-hoc) |

### Tier 5: AI Collaboration
*Specifically for Claude context*

| Document | Purpose | Audience | Status |
|----------|---------|----------|--------|
| `CLAUDE.md` | Context file for Claude Code sessions | AI | **NEW** |
| `.claude/settings.json` | Claude Code configuration | AI | May exist |

---

## Document Specifications

### ARCHITECTURE.md

High-level "how it all fits together":

```markdown
# Iris Architecture

## System Overview
[Diagram showing autopilot → plan → research → execute → validate → document]

## Component Relationships
- How commands invoke each other
- Database as shared state
- Python utilities as helpers

## Data Flow
- PRD → Analysis → Tasks → Execution → Validation

## Key Abstractions
- Commands (prose instructions)
- Subagents (parallel execution)
- Database (state persistence)

## File Structure
[What lives where and why]
```

### DESIGN_PRINCIPLES.md

The "why" behind decisions:

```markdown
# Iris Design Principles

## Core Philosophy: Prose-Orchestration
- Leverage LLM comprehension for decisions
- Use code/schema for storage and validation
- Use prose instructions for orchestration

## Separation of Concerns
[Table of what goes where]

## Variability Management
- Acceptable variability (reasoning paths)
- Unacceptable variability (output formats)
- How we control it

## Catalog + Comprehension
- Define comprehensive catalogs (what's possible)
- Let LLM reason about applicability (what's relevant)
- Validate outputs against schema (what's acceptable)
```

### SCHEMA_REFERENCE.md

Complete database schema documentation:

```markdown
# Iris Database Schema Reference

## Overview
- Schema version: X.X.X
- Location: `.claude/commands/iris/utils/database/schema.sql`
- Database file: `.tasks/iris_project.db`

## Tables

### Core Tables
[For each table: name, purpose, columns with types and descriptions]

### Research Tables
[research_opportunities, research_executions with full column details]

### Relationships
[Foreign key relationships, ER diagram if helpful]

### Indexes
[List of indexes and their purpose]

## Usage Patterns
[Common queries, how to insert/update, examples]

## Schema Evolution
[How the schema has changed, version history]
```

### docs/decisions/ (ADRs)

Architecture Decision Records - one file per major decision:

```
docs/decisions/
├── README.md (index)
├── 001-sqlite-over-json.md
├── 002-prose-orchestration.md
├── 003-parallel-research-subagents.md
├── 004-dynamic-research-opportunities.md
└── template.md
```

**ADR Template:**
```markdown
# ADR-NNN: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What problem were we solving? What was the situation?]

## Decision
[What did we decide to do?]

## Consequences
[What are the implications? Pros and cons?]

## Alternatives Considered
[What else did we consider? Why didn't we choose it?]
```

### CLAUDE.md

Context file specifically for AI collaboration:

```markdown
# Iris Framework - Claude Context

## Quick Orientation
- What is this project
- Key concepts in 2-3 sentences

## Key Files to Read First
1. ARCHITECTURE.md - System overview
2. DESIGN_PRINCIPLES.md - Philosophy
3. Relevant command .md files for current task

## Current State
- What's implemented
- What's in progress
- Known issues

## Conventions
- Naming patterns
- Code style
- Documentation patterns
- What to follow, what to avoid

## Active Work
- Current branch
- Current upgrade plan
- What's being worked on

## How to Contribute
- Read before writing
- Follow existing patterns
- Update docs when changing code
- Record decisions in ADRs
```

### COMMANDS.md

Quick reference for all commands:

```markdown
# Iris Commands Reference

## Primary Command
### /iris:autopilot <PRD>
[Description, usage, examples]

## Manual Commands
### /iris:plan <PRD>
[Description, usage, examples]

### /iris:execute [task-id]
[Description, usage, examples]

[etc.]
```

### EXAMPLES.md

Sample usage with real PRDs:

```markdown
# Iris Examples

## Example 1: Simple CLI Tool (MICRO complexity)
### PRD
[Sample PRD text]

### Expected Behavior
[What Iris does with this PRD]

### Result
[What gets created]

## Example 2: Web API (MEDIUM complexity)
[etc.]
```

---

## Implementation Order

### Phase 1: Foundation (Before major changes)
Priority: Establish baseline documentation of current system

1. **ARCHITECTURE.md** - Document current system before changing it
2. **DESIGN_PRINCIPLES.md** - Extract from RESEARCH_UPGRADE_PLAN.md, make standalone
3. **docs/decisions/** - Start ADR practice with template and first few records

### Phase 2: AI Collaboration (During active development)
Priority: Enable efficient Claude sessions

4. **CLAUDE.md** - AI context file
5. **Update PROCESS_FLOWS.md** - Reflect current/new flows

### Phase 3: Change Tracking (Ongoing)
Priority: Track changes as they happen

6. **CHANGELOG.md** - Start tracking versions
7. **Continue ADRs** - Record decisions as made

### Phase 4: User Documentation (After stabilization)
Priority: Help others use Iris

8. **COMMANDS.md** - Command reference
9. **EXAMPLES.md** - Usage examples
10. **FAQ.md** - Common questions

### Phase 5: Component Documentation (As needed)
Priority: Deep documentation for contributors

11. **docs/commands/*.md** - One per command
12. **docs/utilities/*.md** - Python utility docs

---

## Open Questions

1. **Where should docs live?**
   - Option A: `docs/` folder (organized, separate)
   - Option B: Root level (flat, visible)
   - Option C: Mix (important stuff at root, details in docs/)
   - **Leaning toward:** Option C - ARCHITECTURE.md, DESIGN_PRINCIPLES.md, CLAUDE.md at root; component docs in docs/

2. **ADR numbering scheme?**
   - Sequential (001, 002, 003)
   - Date-based (2024-12-30-decision-name)
   - **Leaning toward:** Sequential for simplicity

3. **How to handle existing upgrade plans?**
   - Move to docs/upgrades/
   - Keep at root during active work, archive when done
   - **Leaning toward:** Keep at root while active, move to docs/upgrades/ when complete

4. **Version scheme for CHANGELOG?**
   - Semantic versioning (1.0.0, 1.1.0)
   - Date-based (2024.12.30)
   - **Leaning toward:** Semantic versioning

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-12-30 | Create documentation upgrade plan | Need structured approach to documentation |
| 2024-12-30 | Five-tier documentation structure | Different audiences need different docs |
| 2024-12-30 | Defer implementation until after research upgrade | One thing at a time |

---

*This document will be updated as decisions are made and implementation progresses.*
