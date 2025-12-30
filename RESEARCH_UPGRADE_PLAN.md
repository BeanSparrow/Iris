# Research Module Upgrade Plan

**Branch:** `researcher-upgrade`
**Status:** Implementation Complete - Testing Phase
**Last Updated:** 2024-12-30

---

## Table of Contents

1. [Objective](#objective)
2. [Design Principles](#design-principles)
3. [Current State Analysis](#current-state-analysis)
4. [Current Invocation Patterns](#current-invocation-patterns)
5. [Subagent Capabilities Discussion](#subagent-capabilities-discussion)
6. [Known Issues & Limitations](#known-issues--limitations)
7. [Research Opportunity Taxonomy](#research-opportunity-taxonomy)
8. [Proposed Execution Model](#proposed-execution-model)
9. [Proposed Design](#proposed-design)
10. [Implementation Plan](#implementation-plan)
11. [Open Questions](#open-questions)

---

## Objective

Extract research functionality from `plan.md` into a dedicated `research.md` module that:
- Has its own instruction set for maintainability and expansion
- Performs actual web-based research (not codebase exploration)
- Integrates cleanly with the existing autopilot flow
- Addresses current limitations in technology research

---

## Design Principles

### Core Philosophy: Prose-Orchestration

> **Leverage LLM comprehension for decisions that benefit from reasoning. Use code/schema for storage and validation. Use prose instructions for orchestration.**

This framework intentionally uses prose-based instructions rather than coded orchestration because:

1. **Models evolve fast** - Prose instructions adapt as capabilities improve
2. **Reasoning is the strength** - LLMs excel at inference, judgment, and context understanding
3. **Flexibility with guardrails** - Controlled variability is a feature, not a bug

### Separation of Concerns

| Concern | Approach | Rationale |
|---------|----------|-----------|
| Decision-making | LLM reasoning | Inference, judgment, context |
| State storage | SQLite database | Consistency, queryability, persistence |
| Orchestration | Prose instructions | Flexibility, readability, adaptability |
| Validation | Schema + LLM review | Deterministic checks + coherence review |
| Complex logic | Python utilities | Testable, reusable, versionable |

### Variability Management

**Acceptable variability:** Reasoning paths, technology choices based on context, adaptive responses to different PRDs.

**Unacceptable variability:** Output formats, database schema violations, skipped phases, inconsistent state.

**How we control it:**
- Clear instruction sets with explicit expectations
- Structured output requirements (database schema)
- Validation gates (review phases)
- Database as source of truth

### Key Principle: Catalog + Comprehension

Rather than hardcoding decision logic (if X then Y), we:
1. Define comprehensive catalogs (what's possible)
2. Let the LLM reason about applicability (what's relevant)
3. Validate outputs against schema (what's acceptable)

This allows the framework to handle novel situations while maintaining consistency.

---

## Current State Analysis

### Where Research Lives Today

Research is embedded inline in `plan.md` (Phase 2A - Adaptive Research, lines 173-278).

### Current Research Flow

```
plan.md receives PRD
    │
    ▼
iris_adaptive.py → ProjectAnalyzer.analyze()
    │
    ├─► Returns: complexity, project_type, research_agents_count
    │
    ▼
plan.md checks RESEARCH_AGENTS count
    │
    ├─► If 0 (MICRO): Insert default Python tech, skip research
    │
    └─► If > 0: Launch Task tools with subagent_type="Explore"
            │
            ▼
        Agents return recommendations
            │
            ▼
        Store in technologies table
```

### Research Agent Configuration (from iris_adaptive.py)

| Complexity | Agents | Skip Cache | Depth |
|------------|--------|------------|-------|
| MICRO | 0 | Yes | shallow |
| SMALL | 2 | Yes | shallow |
| MEDIUM | 4 | No | standard |
| LARGE | 6 | No | deep |
| ENTERPRISE | 8 | No | deep |

### ResearchOrchestrator Class (iris_adaptive.py:342-442)

Currently provides:
- `get_research_agents()` - Returns agent configs based on complexity
- `_check_cache()` - Checks hardcoded COMMON_DECISIONS dict
- `COMMON_DECISIONS` - Static dict with outdated tech versions

---

## Current Invocation Patterns

### How Commands Call Each Other

Based on analysis of the codebase, there are **two patterns** used:

#### Pattern 1: Prose Instructions (Primary Method)

Commands don't directly invoke other commands programmatically. Instead, they use **prose instructions** that tell Claude what to do next:

**autopilot.md → plan.md:**
```markdown
1. Invoke `/iris:plan` with the PRD content from `$ARGUMENTS`
2. **CRITICAL: After `/iris:plan` completes, YOU MUST CONTINUE to Phase 2 below**
```

**autopilot.md → validate.md:**
```markdown
Now invoke `/iris:validate` to run the final validation checks.
```

**execute.md → validate.md:**
```markdown
Run: /iris:validate [milestone-id]
```

#### Pattern 2: Python Utility Calls

For shared functionality, commands call Python utilities directly via bash:
```bash
python3 "$IRIS_DIR/utils/document_generator.py" \
    --project-root "$PROJECT_ROOT" \
    --iris-dir "$IRIS_DIR" \
    --milestone "$COMPLETED_MS"
```

### Key Observations

1. **No direct command chaining** - Commands are prose instructions to Claude
2. **Autopilot is the orchestrator** - It sequences: plan → execute → validate → document
3. **Commands are self-contained** - Each can run standalone with database state
4. **Python utilities are helpers** - Complex logic lives in Python, called via bash
5. **Database is the shared state** - All commands read/write SQLite for coordination

### Invocation Consistency Guidelines

To stay consistent with the framework:
- Research should be invoked via **prose instruction** from plan.md
- Research results should be stored in **database** (technologies table)
- Research can use **Python utilities** for complex logic
- Research should be **callable by plan.md only** (for now)

---

## Subagent Capabilities Discussion

### Current Understanding

The Task tool spawns subagents with different `subagent_type` values:

| subagent_type | Purpose | Tools Available |
|---------------|---------|-----------------|
| `Explore` | Codebase exploration | Glob, Grep, Read |
| `general-purpose` | Multi-step tasks | All tools (*) |
| `Plan` | Planning tasks | All tools |

### Questions to Resolve

1. **What can Explore agents actually do?**
   - Can they use WebSearch/WebFetch?
   - Are they limited to local file operations?

2. **Should research use `general-purpose` instead?**
   - This would give access to WebSearch, WebFetch
   - But adds overhead of full agent capabilities

3. **Can we run WebSearch directly without subagents?**
   - Would be simpler and faster
   - But loses parallelism

4. **What is the token/cost tradeoff?**
   - Subagents consume tokens
   - Parallel execution vs sequential WebSearch calls

### Current Research Problem

plan.md instructs:
```markdown
Each agent should be invoked with `subagent_type: "Explore"` and these prompts
```

But Explore agents are for **codebase exploration**, not web research. This is likely why research doesn't actually perform web searches - the wrong tool is being used.

### Proposed Resolution

**Option A:** Use `general-purpose` subagents with explicit WebSearch instructions
- Pros: Full web research capability, parallel execution
- Cons: Higher token cost, more complex

**Option B:** Direct WebSearch calls from research.md (no subagents)
- Pros: Simpler, lower cost, direct control
- Cons: Sequential execution, can't parallelize

**Option C:** Hybrid approach
- Use direct WebSearch for primary research
- Use subagents only for deep-dive verification
- Balance between speed and thoroughness

**Decision:** TBD after discussion

---

## Known Issues & Limitations

### Issue 1: Agent Prompts Are Vague

**Current State:**
```markdown
| Agent ID | Description | Search Topics |
| SA-1-LANG | Language Selection | "best {project_type} programming languages" |
```

**Problem:** Just search topic strings, no structured instructions for:
- What to look for
- How to evaluate options
- What format to return
- How to verify information

**Solution:** Create detailed agent prompts with specific instructions.

---

### Issue 2: Wrong Tool for Web Research

**Current State:**
```markdown
Each agent should be invoked with `subagent_type: "Explore"`
```

**Problem:** Explore agents are for codebase exploration (Glob, Grep, Read), NOT web research. They likely can't use WebSearch/WebFetch.

**Solution:** Either:
- Use `general-purpose` subagents with WebSearch access
- Call WebSearch directly from research.md without subagents

---

### Issue 3: Hardcoded Technology Cache

**Current State (iris_adaptive.py:346-362):**
```python
COMMON_DECISIONS = {
    "web_frontend_2024": {
        "React": {"version": "18.2.0", ...},
        "Next.js": {"version": "14.1.0", ...}
    },
    ...
}
```

**Problem:**
- Versions are outdated (hardcoded "2024")
- No mechanism to refresh
- Limited technology coverage
- Bypasses actual research

**Solution:** Remove hardcoded cache, always perform live research (with optional database caching of recent results).

---

### Issue 4: No Source Verification

**Current State:** Agents return recommendations but:
- No URL fetching to verify versions
- No checking official documentation
- No validation that recommended tech exists

**Problem:** Recommendations could be hallucinated or outdated.

**Solution:** Research flow should:
1. WebSearch for technology
2. WebFetch official docs/releases
3. Extract actual current version
4. Store with source URL for traceability

---

### Issue 5: Loose Return Format

**Current State:**
```markdown
**Expected return format from each agent:**
{
    "agent_id": "SA-X-NAME",
    "recommendation": "<technology>",
    ...
}
```

**Problem:** JSON format is described but not enforced. No validation that agents actually return this structure.

**Solution:** Create structured output schema and validate responses before storing.

---

### Issue 6: Research Not Used During Execution

**Current State:** execute.md validates against `technologies` table but:
- Doesn't influence actual implementation choices
- Just checks compliance after the fact

**Problem:** Research is performed but not actively used to guide development.

**Solution:** Consider how research results should inform task execution (future enhancement).

---

### Issue 7: Research Depth is Unused

**Current State (iris_adaptive.py):**
```python
"research_depth": "shallow",  # or "standard", "deep"
```

**Problem:** This value is set but never actually changes agent behavior.

**Solution:** Replace rigid depth levels with dynamic research opportunities selected by the planner based on PRD analysis.

---

## Research Opportunity Taxonomy

Rather than hardcoding "X agents for Y complexity," we define a **catalog of research opportunities** that the planner selects from based on PRD analysis.

### Category A: Stack Selection
*What technologies to use*

| Opportunity ID | Name | Trigger Conditions | Research Question |
|----------------|------|-------------------|-------------------|
| `STACK_LANG` | Language Selection | No language specified in PRD | What programming language best fits this project type and requirements? |
| `STACK_RUNTIME` | Runtime Selection | Language has multiple runtimes (Node/Deno/Bun, Python version) | What runtime/version is appropriate? |
| `STACK_FRAMEWORK_UI` | UI Framework | Frontend/UI mentioned or implied | What frontend framework fits the requirements? |
| `STACK_FRAMEWORK_API` | API Framework | Backend/API mentioned or implied | What backend/API framework for the chosen language? |
| `STACK_FRAMEWORK_FULL` | Full-Stack Framework | Full-stack app, SSR, or integrated frontend+backend | Next.js vs Remix vs SvelteKit vs similar? |
| `STACK_DATABASE` | Database Selection | Data persistence, storage, or state mentioned | SQL vs NoSQL? Which specific database? |
| `STACK_ORM` | ORM/Query Builder | Database selected, complex data models | What ORM or query builder for this database+language? |
| `STACK_AUTH` | Authentication | User accounts, login, auth, or security mentioned | Auth library, service, or approach? |
| `STACK_STYLING` | Styling Approach | UI needed | CSS framework, Tailwind, styled-components, etc.? |
| `STACK_DEPLOY` | Deployment Platform | Production, hosting, or deployment mentioned | Vercel, AWS, Docker, etc.? |
| `STACK_QUEUE` | Message Queue | Async processing, background jobs, events | Redis, RabbitMQ, SQS? |
| `STACK_CACHE` | Caching Layer | Performance, scale, or caching mentioned | Redis, Memcached, in-memory? |
| `STACK_SEARCH` | Search Engine | Search functionality mentioned | Elasticsearch, Algolia, built-in? |

### Category B: Version & Compatibility
*What versions to use - addresses the "outdated DLL" problem*

| Opportunity ID | Name | Trigger Conditions | Research Question |
|----------------|------|-------------------|-------------------|
| `VERSION_LANG` | Language Version | Language selected | What is the current stable/LTS version? |
| `VERSION_FRAMEWORK` | Framework Version | Framework selected | What is the current stable version? |
| `VERSION_DEPS` | Dependency Versions | Key dependencies identified | What are current stable versions of major dependencies? |
| `COMPAT_MATRIX` | Compatibility Check | Multiple technologies selected | Do these specific versions work together? Known conflicts? |
| `DEPRECATION_CHECK` | Deprecation Scan | Building on existing code, or using older tech | Are any components deprecated? Migration paths? |
| `LTS_STATUS` | LTS/Support Check | Production deployment, long-term maintenance | Is this LTS? When does support end? |
| `SECURITY_VERSIONS` | Security Advisory Check | Security-sensitive project | Any known vulnerabilities in these versions? |

### Category C: Architecture & Patterns
*How to structure the solution*

| Opportunity ID | Name | Trigger Conditions | Research Question |
|----------------|------|-------------------|-------------------|
| `ARCH_PATTERN` | Architecture Pattern | Non-trivial project, multiple components | Monolith vs microservices vs serverless vs modular monolith? |
| `ARCH_API_DESIGN` | API Design Pattern | API needed | REST vs GraphQL vs tRPC vs gRPC? |
| `ARCH_STATE_MGMT` | State Management | Complex UI, client-side state | Redux, Zustand, Jotai, Context, signals? |
| `ARCH_DATA_PATTERN` | Data Access Pattern | Complex data, multiple sources | Repository pattern, CQRS, event sourcing? |
| `ARCH_FILE_STRUCTURE` | Project Structure | New project setup | Recommended folder structure for this stack? |
| `ARCH_ERROR_HANDLING` | Error Handling Strategy | Production app, reliability focus | Error handling patterns for this stack? |
| `ARCH_REALTIME` | Real-time Architecture | Real-time, live updates, collaboration | WebSockets, SSE, polling, CRDT? |

### Category D: Operational Concerns
*How to run and maintain*

| Opportunity ID | Name | Trigger Conditions | Research Question |
|----------------|------|-------------------|-------------------|
| `OPS_TESTING` | Testing Strategy | Always (scaled by complexity) | Testing framework and approach for this stack? |
| `OPS_CI_CD` | CI/CD Pipeline | Deployment, automation mentioned | CI/CD approach for this stack and platform? |
| `OPS_MONITORING` | Monitoring/Logging | Production, observability mentioned | Logging and monitoring approach? |
| `OPS_SECURITY` | Security Practices | Auth, sensitive data, compliance | Security best practices for this stack? |
| `OPS_PERF` | Performance Optimization | Scale, performance, speed mentioned | Performance considerations for this use case? |
| `OPS_CONTAINER` | Containerization | Docker, containers, K8s mentioned | Container strategy and configuration? |

### Category E: Custom/Escape Hatch
*For situations not covered by standard categories*

| Opportunity ID | Name | Trigger Conditions | Research Question |
|----------------|------|-------------------|-------------------|
| `CUSTOM` | Custom Research | Planner identifies need not in catalog | Dynamic - defined by planner based on PRD |

### Opportunity Selection Process

The planner uses **LLM comprehension** to select opportunities:

1. **Read the PRD** and understand requirements
2. **Review the opportunity catalog** above
3. **Identify which opportunities apply** based on:
   - Explicit mentions (PRD says "use PostgreSQL" → skip `STACK_DATABASE`, add `VERSION_DEPS` for PostgreSQL)
   - Implicit requirements (PRD says "user accounts" → add `STACK_AUTH`)
   - Gaps that need filling (PRD doesn't specify language → add `STACK_LANG`)
4. **Output a list of opportunity IDs** with brief rationale
5. **Categorize as Required vs Conditional:**
   - Required: `OPS_TESTING`, `VERSION_*` for selected tech
   - Conditional: Everything else based on PRD analysis

### Default Opportunities by Complexity

While the planner has full discretion, these are typical minimums:

| Complexity | Typical Minimum Opportunities |
|------------|------------------------------|
| MICRO | `OPS_TESTING`, `VERSION_*` for any tech used |
| SMALL | Above + 1-2 from STACK if not specified |
| MEDIUM | Above + architecture considerations |
| LARGE | Above + operational concerns |
| ENTERPRISE | Full catalog review recommended |

---

## Proposed Execution Model

### Three-Phase Research Execution

Based on discussion, we adopt **Option D: Parallel with Context Sharing** plus a **Review Phase**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                          │
│                      (Sequential)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Analyze PRD for explicit technology choices                │
│  2. Detect project type and complexity                         │
│  3. Select research opportunities from catalog                 │
│  4. Make foundational decisions (language, project type)       │
│  5. Create "research context" document with knowns             │
│                                                                 │
│  Output: Research context + list of opportunities to research  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: PARALLEL RESEARCH                   │
│                (Parallel general-purpose Subagents)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For each selected opportunity, spawn a subagent WITH context: │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Agent:      │ │ Agent:      │ │ Agent:      │  ...          │
│  │ STACK_DB    │ │ OPS_TESTING │ │ VERSION_*   │               │
│  │             │ │             │ │             │               │
│  │ Context:    │ │ Context:    │ │ Context:    │               │
│  │ "Python,    │ │ "Python,    │ │ "FastAPI    │               │
│  │  FastAPI,   │ │  FastAPI    │ │  selected"  │               │
│  │  web API"   │ │  web API"   │ │             │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│         │               │               │                       │
│         └───────────────┴───────────────┘                       │
│                         │                                       │
│                         ▼                                       │
│              Collect all research results                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 3: REVIEW & RECONCILIATION                │
│                        (Sequential)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Planner reviews ALL research results and checks for:          │
│                                                                 │
│  ✓ COHERENCE: Do these technologies work together?             │
│  ✓ CONFLICTS: Did any agents make contradictory assumptions?   │
│  ✓ GAPS: Did we miss anything important?                       │
│  ✓ VERSIONS: Are all versions compatible with each other?      │
│  ✓ COMPLETENESS: Do we have enough info to proceed?            │
│                                                                 │
│  If issues found:                                               │
│  ├─► Minor: Resolve directly with planner judgment             │
│  ├─► Research gap: Spawn targeted re-research with new context │
│  └─► Ambiguous: Flag for user input (rare)                     │
│                                                                 │
│  If coherent:                                                   │
│  └─► Commit approved stack to database                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE COMMIT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Store to `technologies` table:                                 │
│  - Technology name, category, version                          │
│  - Source URLs for verification                                 │
│  - Decision rationale                                           │
│  - Compatibility notes                                          │
│                                                                 │
│  Store to `research_opportunities` table (new):                 │
│  - Which opportunities were researched                          │
│  - Results summary                                              │
│  - Research timestamp                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Continue to Milestone Creation
```

### Ownership Delineation

**Critical:** Clear separation between plan.md and research.md responsibilities.

```
plan.md                              research.md
────────                             ───────────
   │
   │  1. Receive PRD
   │  2. Run ProjectAnalyzer (complexity)
   │  3. Invoke research process:
   │
   │     "Perform technology research
   │      following the research protocol"
   │─────────────────────────────────────►│
   │                                      │
   │                                      ├─► Phase 1: Foundation
   │                                      │   - Analyze PRD for explicit tech
   │                                      │   - Select opportunities from catalog
   │                                      │   - Build research context
   │                                      │
   │                                      ├─► Phase 2: Parallel Research
   │                                      │   - Spawn general-purpose subagents
   │                                      │   - Each researches one opportunity
   │                                      │
   │                                      ├─► Phase 3: Review & Reconciliation
   │                                      │   - Check coherence, conflicts, gaps
   │                                      │   - Re-research if needed
   │                                      │
   │                                      ├─► Commit to database
   │                                      │
   │◄─────────────────────────────────────│
   │  (research complete, stack in DB)
   │
   │  4. Read approved stack from DB
   │  5. Create milestones and tasks
   │  6. Store plan to database
   │
```

| Responsibility | Owner | Notes |
|---------------|-------|-------|
| PRD intake | plan.md | Entry point |
| Complexity analysis | plan.md | Uses ProjectAnalyzer |
| Research invocation | plan.md | Prose instruction |
| Opportunity selection | research.md | Dynamic, based on PRD gaps |
| Subagent orchestration | research.md | Parallel execution |
| Result reconciliation | research.md | Coherence checking |
| Technology storage | research.md | Commits to DB |
| Milestone creation | plan.md | After research complete |
| Task creation | plan.md | Based on approved stack |

### Dynamic Research Determination

**IMPORTANT:** The old model of fixed agent counts per complexity level is REMOVED.

**Old model (deprecated):**
```python
# NO LONGER USED
research_agents_count: int  # Was: 0, 2, 4, 6, 8 based on complexity
skip_common_research: bool  # Was: bypass research for simple projects
```

**New model:**
- Research opportunities are ALWAYS dynamically determined
- Planner analyzes PRD for explicit tech mentions vs gaps
- Planner selects applicable opportunities from catalog
- Number of subagents = number of selected opportunities
- Complexity provides guidance, not prescription

**Examples:**

| PRD | Complexity | Old Model | New Model |
|-----|------------|-----------|-----------|
| "Python CLI tool" | MICRO | 0 agents, skip research | `OPS_TESTING`, `VERSION_LANG` → 2 opportunities |
| "React app with Supabase" | MEDIUM | 4 fixed agents | Tech specified → `VERSION_*`, `OPS_TESTING` → 3 opportunities |
| "Build a web app" (vague) | MEDIUM | 4 fixed agents | Many gaps → 6+ opportunities |
| "E-commerce platform" | LARGE | 6 fixed agents | Comprehensive → 10+ opportunities |

The research scope adapts to **actual gaps in the PRD**, not assumed complexity.

### Phase 1 Details: Foundation

**Purpose:** Establish context that all parallel research agents need.

**Inputs:**
- Raw PRD from user
- Opportunity catalog (defined above)

**Process:**
1. Parse PRD for explicit technology mentions
2. Run complexity analysis (existing `ProjectAnalyzer`)
3. Identify project type
4. Select applicable research opportunities
5. Make any obvious foundational decisions (if PRD says "Python" → language is decided)

**Outputs:**
- `research_context`: JSON blob with all knowns
- `opportunities_to_research`: List of opportunity IDs
- `foundational_decisions`: Any tech already decided

**Example research_context:**
```json
{
  "project_type": "web_api",
  "complexity": "medium",
  "language": "python",
  "language_source": "explicit_prd",
  "requirements": ["rest api", "user auth", "postgresql mentioned"],
  "constraints": ["must use postgresql"],
  "unknowns": ["framework", "auth approach", "testing strategy"]
}
```

### Phase 2 Details: Parallel Research

**Purpose:** Execute research in parallel for wall-clock speed.

**Subagent Type:** `general-purpose` (has WebSearch, WebFetch access)

**Each agent receives:**
1. The research_context from Phase 1
2. Their specific opportunity ID and research question
3. Structured output requirements

**Subagent Prompt Template:**
```markdown
You are researching [OPPORTUNITY_ID]: [OPPORTUNITY_NAME]

## Context
[research_context JSON]

## Your Research Question
[Research question from catalog]

## Instructions
1. Use WebSearch to find current, authoritative information
2. Use WebFetch to verify from official sources when possible
3. Focus on compatibility with the established context above

## Required Output
Provide your findings in this exact structure:

RECOMMENDATION: [Primary recommendation]
VERSION: [Specific version number]
SOURCE: [Official URL where you verified this]
ALTERNATIVES: [1-2 alternatives if applicable]
RATIONALE: [Why this choice given the context]
COMPATIBILITY_NOTES: [Any compatibility considerations with other context items]
CONFIDENCE: [HIGH/MEDIUM/LOW]
```

### Phase 3 Details: Review & Reconciliation

**Purpose:** Ensure coherent, conflict-free technology stack.

**Planner reviews and checks:**

| Check | Description | Resolution |
|-------|-------------|------------|
| Coherence | Do all pieces work together? | Flag conflicts |
| Version compatibility | Do these versions have known conflicts? | Research specific compatibility |
| Completeness | Any gaps in the stack? | Add missed opportunities |
| Redundancy | Multiple agents recommend same thing differently? | Consolidate |
| Confidence | Any LOW confidence results? | Consider re-research or flagging |

**Re-research trigger:**
If issues found that can't be resolved by judgment, spawn targeted follow-up:
```
"Given [CONFLICT DESCRIPTION], research [SPECIFIC QUESTION] considering [UPDATED CONTEXT]"
```

### Why This Model Works

1. **Foundation phase ensures coherent context** - Agents don't make conflicting assumptions
2. **Parallel execution for speed** - Wall clock wins
3. **Review phase catches problems** - Planner sees full picture
4. **Re-research is targeted** - Only redo what's needed, not everything
5. **Database commit is atomic** - Either we have a complete approved stack or we don't

---

## Proposed Design

### New File: research.md

**Location:** `.claude/commands/iris/research.md`

**Allowed Tools:**
```yaml
allowed-tools:
  - Bash
  - Read
  - WebSearch
  - WebFetch
  - Task (if using subagents)
```

**NOT a user-callable command** (for now) - only invoked by plan.md

### Integration with plan.md

plan.md Phase 2A changes from inline research to:
```markdown
### Phase 2A — Technology Research

**INSTRUCTION:** Now perform technology research by following the research protocol.

[Include research.md content here OR instruct Claude to follow research process]
```

### Research Flow (New)

```
plan.md triggers research
    │
    ▼
Load complexity config from database
    │
    ▼
Determine research scope (agents needed)
    │
    ▼
For each research area:
    ├─► WebSearch for current recommendations
    ├─► WebFetch official docs for version verification
    └─► Validate and structure results
    │
    ▼
Store in technologies table with sources
    │
    ▼
Return summary to plan.md
    │
    ▼
plan.md continues to milestone creation
```

### Research Areas (Refined)

| Area | Trigger | Research Focus |
|------|---------|----------------|
| Language | Always (if agents > 0) | Best language for project type, current LTS version |
| Testing | Always (if agents > 0) | Testing framework for chosen language |
| Architecture | agents >= 4 | Patterns for project type |
| Frontend | Full-stack projects | Framework comparison, current versions |
| Backend | API/Full-stack | Framework for chosen language |
| Database | Data-heavy projects | SQL vs NoSQL for use case |

---

## Implementation Plan

### Phase 1: Documentation & Design
- [x] Analyze current research flow
- [x] Document invocation patterns
- [x] Resolve subagent questions (use `general-purpose`)
- [x] Finalize design decisions
- [x] Define research opportunity taxonomy
- [x] Design three-phase execution model
- [x] Document ownership delineation (plan.md vs research.md)

### Phase 2: Schema Updates
- [x] Design new tables (`research_opportunities`, `research_executions`)
- [x] Design table modifications (`technologies`, `technology_sources`)
- [x] Update schema.sql to version 2.0.0
- [x] Update db_manager.py validation

### Phase 3: Create research.md
- [x] Write research.md with detailed instructions
- [x] Implement Phase 1: Foundation (PRD analysis, opportunity selection)
- [x] Implement Phase 2: Parallel Research (subagent orchestration)
- [x] Implement Phase 3: Review & Reconciliation
- [x] Define subagent prompt templates with brevity requirements
- [x] Add database commit logic

### Phase 4: Modify plan.md
- [x] Remove inline research (current Phase 2A)
- [x] Add prose instruction to invoke research process
- [x] Update final report to include research results

### Phase 5: Update iris_adaptive.py
- [x] Remove ResearchOrchestrator class
- [x] Remove COMMON_DECISIONS cache
- [x] Remove `research_agents_count` from AdaptiveConfig
- [x] Remove `skip_common_research` logic
- [x] Keep ProjectAnalyzer for complexity detection

### Phase 6: Flow Fixes & Verification
- [x] Standardize IRIS_DIR detection (use .claude as root marker)
- [x] Add explicit Read instruction for research.md in plan.md
- [x] Remove hardcoded year references from research.md
- [x] Update integration notes in research.md
- [x] Add research verification step (check research_phase_status = 'completed')
- [x] Add --research flag to document.md for TECH_DECISIONS.md generation
- [x] Add Phase 2B to plan.md (invoke document.md --research)

### Phase 7: Documentation
- [x] Update README.md with prose-orchestration approach and research changes
- [x] Update PROCESS_FLOWS.md with new research flow and research module section
- [ ] Update help.md with research information

### Phase 8: Testing
- [ ] Test with MICRO project (minimal research)
- [ ] Test with MEDIUM project (moderate research)
- [ ] Test with LARGE project (comprehensive research)
- [ ] Test full autopilot flow end-to-end

---

## Open Questions

### Resolved

1. ~~**Subagent vs Direct WebSearch:** Which approach for research execution?~~
   - **RESOLVED:** Use parallel `general-purpose` subagents with context sharing (Option D)

2. ~~**Research Depth Implementation:** How do shallow/standard/deep actually differ in execution?~~
   - **RESOLVED:** Replaced with dynamic Research Opportunity selection based on PRD analysis

3. ~~**Schema Updates:** What new tables/columns needed for research opportunities?~~
   - **RESOLVED:** Schema updated to version 2.0.0. See [Schema Changes Implemented](#schema-changes-implemented) below.

### Remaining

4. **Research Caching:** Should we cache results in database for repeated runs?
   - Consider: Project-level cache (reuse within same project) vs global cache (reuse across projects)
   - Risk: Stale data if project runs over multiple days

5. **Failure Handling:** What if WebSearch fails or returns no results?
   - Options: Fallback to LLM knowledge, flag for user input, retry with different query
   - Need to define retry/fallback strategy

6. **Version Verification:** How deep should we verify (just fetch, or parse version numbers)?
   - Minimum: Fetch official source, confirm version exists
   - Ideal: Parse release dates, check if truly "current"

7. **Technology Conflicts:** What if research recommends different tech than PRD specifies?
   - PRD explicit mentions should override research recommendations
   - Research should still verify versions of PRD-specified tech

8. **Subagent Result Parsing:** How do we reliably extract structured data from subagent responses?
   - Text parsing vs asking for specific format
   - Error handling for malformed responses

---

## Schema Changes Implemented

**Schema Version:** 2.0.0
**File:** `.claude/commands/iris/utils/database/schema.sql`

### New Tables

#### `research_opportunities`
Tracks which research opportunities were selected and their outcomes.

```sql
CREATE TABLE research_opportunities (
    id TEXT PRIMARY KEY,                    -- STACK_LANG, VERSION_DEPS, OPS_TESTING, etc.
    category TEXT NOT NULL,                 -- stack, version, architecture, ops, custom
    name TEXT NOT NULL,                     -- Human-readable name
    research_question TEXT,                 -- The question being researched
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, skipped
    result_summary TEXT,                    -- Brief summary of findings
    confidence TEXT,                        -- HIGH, MEDIUM, LOW
    researched_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `research_executions`
Tracks subagent executions for debugging and audit.

```sql
CREATE TABLE research_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL,
    execution_status TEXT NOT NULL,         -- started, completed, failed, retrying
    subagent_prompt TEXT,                   -- The prompt sent to subagent
    subagent_response TEXT,                 -- Full response (kept concise via prompt)
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (opportunity_id) REFERENCES research_opportunities(id) ON DELETE CASCADE
);
```

### Modified Tables

#### `technologies` - New Columns
```sql
opportunity_id TEXT,            -- Links to research_opportunities.id
confidence TEXT,                -- HIGH, MEDIUM, LOW
alternatives TEXT,              -- JSON array: ["Vue", "Svelte"]
compatibility_notes TEXT,       -- Notes on compatibility with other stack items
source_type TEXT                -- explicit_prd, researched, default
```

#### `technology_sources` - New Columns
```sql
source_type TEXT,               -- official_docs, blog, comparison, release_notes
was_fetched BOOLEAN,            -- Did we actually fetch and verify this URL?
fetch_timestamp DATETIME        -- When was it fetched?
```

### New Indexes
```sql
CREATE INDEX idx_research_opp_status ON research_opportunities(status);
CREATE INDEX idx_research_opp_category ON research_opportunities(category);
CREATE INDEX idx_tech_opportunity ON technologies(opportunity_id);
CREATE INDEX idx_research_exec_opp ON research_executions(opportunity_id);
```

### Category Mapping

The `research_opportunities.category` field maps to our taxonomy:

| Category Value | Taxonomy Section |
|---------------|------------------|
| `stack` | Category A: Stack Selection |
| `version` | Category B: Version & Compatibility |
| `architecture` | Category C: Architecture & Patterns |
| `ops` | Category D: Operational Concerns |
| `custom` | Category E: Custom/Escape Hatch |

### Context Storage

Research context (Phase 1 output) is stored in the existing `project_metadata` table using keys like:
- `research_context_project_type`
- `research_context_language`
- `research_context_constraints`
- `research_phase_status`

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-12-30 | Create upgrade plan document | Need to document thinking before implementation |
| 2024-12-30 | Research only callable from plan.md (for now) | Nail down framework before exposing as standalone |
| 2024-12-30 | Adopt prose-orchestration philosophy | LLMs excel at reasoning; leverage comprehension over hardcoded logic |
| 2024-12-30 | Use parallel subagents with context sharing (Option D) | Wall-clock speed with coherent context; review phase catches conflicts |
| 2024-12-30 | Replace depth levels with opportunity catalog | Dynamic selection based on PRD analysis; more flexible and comprehensive |
| 2024-12-30 | Add Review & Reconciliation phase | Planner reviews all results for coherence; can trigger targeted re-research |
| 2024-12-30 | Use `general-purpose` subagent type | Explore agents lack WebSearch/WebFetch; general-purpose has all tools |
| 2024-12-30 | Remove hardcoded COMMON_DECISIONS | Always perform live research; no outdated static cache |
| 2024-12-30 | No schema versioning/migration | DB created fresh per project; breaking changes acceptable |
| 2024-12-30 | Use existing project_metadata for context | No need for separate research_context table |
| 2024-12-30 | Store full subagent responses | Add brevity requirements to prompts; store everything for debugging |
| 2024-12-30 | Schema v2.0.0 implemented | Added research_opportunities, research_executions tables; extended technologies and technology_sources |
| 2024-12-30 | research.md created | Three-phase research module with opportunity catalog, parallel subagents, and review phase |
| 2024-12-30 | plan.md updated | Removed inline research, added invocation of research.md process |
| 2024-12-30 | iris_adaptive.py v2.0.0 | Removed ResearchOrchestrator, COMMON_DECISIONS, research_agents_count; research now fully dynamic |
| 2024-12-30 | Standardize on Python DatabaseManager | All DB operations use DatabaseManager for consistency; removed raw sqlite3 CLI calls from research.md |
| 2024-12-30 | Add prose-orchestration context to research.md | Clarifies that PRD and $IRIS_DIR are available from plan.md context |
| 2024-12-30 | Update README.md | Added prose-orchestration section, dynamic research, updated architecture diagram |
| 2024-12-30 | Standardize IRIS_DIR detection | All commands now use .claude folder as project root marker for consistency |
| 2024-12-30 | Add explicit Read instruction | plan.md now explicitly instructs Claude to use Read tool on research.md |
| 2024-12-30 | Add research verification | plan.md checks research_phase_status = 'completed' before proceeding |
| 2024-12-30 | Add document.md --research flag | Generates TECH_DECISIONS.md for transparency and debugging |
| 2024-12-30 | Add Phase 2B to plan.md | Research documentation via document.md --research after research completion |
| 2024-12-30 | Update PROCESS_FLOWS.md | Added Research Module Flow section, updated command ecosystem diagram, version 2.0 |

---

## Next Steps

### Completed
1. ~~**Review this document** - Ensure alignment on design decisions~~
2. ~~**Define schema updates** - What tables/columns needed for new research model~~
3. ~~**Create research.md** - Implement the three-phase research process~~
4. ~~**Update plan.md** - Remove inline research, add research invocation~~
5. ~~**Update iris_adaptive.py** - Remove ResearchOrchestrator, keep ProjectAnalyzer~~
6. ~~**Flow fixes** - Standardize IRIS_DIR, add verification, add research docs~~
7. ~~**Update documentation** - README.md, PROCESS_FLOWS.md~~

### Remaining
8. **Update help.md** - Add research information to user-facing help
9. **Test the flow** - Validate with sample PRDs of varying complexity

---

## Files Modified

| File | Changes |
|------|---------|
| `.claude/commands/iris/utils/database/schema.sql` | v2.0.0 - Added research_opportunities, research_executions tables; extended technologies and technology_sources |
| `.claude/commands/iris/utils/database/db_manager.py` | Added new tables to validation |
| `.claude/commands/iris/research.md` | **NEW** - Three-phase research module with prose-orchestration context |
| `.claude/commands/iris/plan.md` | Replaced inline research; added Phase 2A (research invocation) and Phase 2B (research docs); standardized IRIS_DIR |
| `.claude/commands/iris/document.md` | Added --research flag for TECH_DECISIONS.md generation; standardized IRIS_DIR |
| `.claude/commands/iris/autopilot.md` | Standardized IRIS_DIR detection using .claude folder |
| `.claude/commands/iris/utils/iris_adaptive.py` | v2.0.0 - Removed ResearchOrchestrator, research_agents_count, skip_common_research |
| `SQLITE_ARCHITECTURE.md` | Updated with research tables and data flow |
| `README.md` | Added prose-orchestration section, dynamic research, schema v2.0.0, architecture flow diagram |
| `PROCESS_FLOWS.md` | v2.0 - Added Research Module Flow section, updated command ecosystem, updated plan flow |

---

*This document will be updated as decisions are made and implementation progresses.*
