---
allowed-tools:
  - Bash
  - Read
  - Task
  - WebSearch
  - WebFetch
  - Glob
  - Grep
description: "Internal research module - invoked by plan.md for technology research"
---

# Iris Research Module

**Purpose:** Perform technology research to inform project planning decisions.
**Invoked by:** `/iris:plan` via prose-orchestration (not user-callable directly)

---

## Prose-Orchestration Context

This module is executed inline by the same Claude instance running `/iris:plan`. When plan.md instructs you to "read and follow research.md", you:

1. **Have access to the PRD** - The PRD content from plan.md's `$ARGUMENTS` is already in your conversation context
2. **Have access to $IRIS_DIR** - The Iris directory path was set earlier in plan.md
3. **Execute inline** - There is no subprocess; you follow these instructions directly
4. **Return control to plan.md** - After completing research, continue with milestone creation

---

## Research Opportunity Catalog

The following research opportunities are available. Select those that apply based on PRD analysis.

### Category A: Stack Selection (`stack`)

| ID | Name | Research Question |
|----|------|-------------------|
| `STACK_LANG` | Language Selection | What programming language best fits this project type and requirements? |
| `STACK_RUNTIME` | Runtime Selection | What runtime/version is appropriate? (Node/Deno/Bun, Python version) |
| `STACK_FRAMEWORK_UI` | UI Framework | What frontend framework fits the requirements? |
| `STACK_FRAMEWORK_API` | API Framework | What backend/API framework for the chosen language? |
| `STACK_FRAMEWORK_FULL` | Full-Stack Framework | Next.js vs Remix vs SvelteKit vs similar? |
| `STACK_DATABASE` | Database Selection | SQL vs NoSQL? Which specific database? |
| `STACK_ORM` | ORM/Query Builder | What ORM or query builder for this database+language? |
| `STACK_AUTH` | Authentication | Auth library, service, or approach? |
| `STACK_STYLING` | Styling Approach | CSS framework, Tailwind, styled-components, etc.? |
| `STACK_DEPLOY` | Deployment Platform | Vercel, AWS, Docker, etc.? |
| `STACK_QUEUE` | Message Queue | Redis, RabbitMQ, SQS for async processing? |
| `STACK_CACHE` | Caching Layer | Redis, Memcached, in-memory? |
| `STACK_SEARCH` | Search Engine | Elasticsearch, Algolia, built-in? |

### Category B: Version & Compatibility (`version`)

| ID | Name | Research Question |
|----|------|-------------------|
| `VERSION_LANG` | Language Version | What is the current stable/LTS version? |
| `VERSION_FRAMEWORK` | Framework Version | What is the current stable version? |
| `VERSION_DEPS` | Dependency Versions | What are current stable versions of major dependencies? |
| `COMPAT_MATRIX` | Compatibility Check | Do these specific versions work together? Known conflicts? |
| `DEPRECATION_CHECK` | Deprecation Scan | Are any components deprecated? Migration paths? |
| `LTS_STATUS` | LTS/Support Check | Is this LTS? When does support end? |
| `SECURITY_VERSIONS` | Security Advisory Check | Any known vulnerabilities in these versions? |

### Category C: Architecture & Patterns (`architecture`)

| ID | Name | Research Question |
|----|------|-------------------|
| `ARCH_PATTERN` | Architecture Pattern | Monolith vs microservices vs serverless vs modular monolith? |
| `ARCH_API_DESIGN` | API Design Pattern | REST vs GraphQL vs tRPC vs gRPC? |
| `ARCH_STATE_MGMT` | State Management | Redux, Zustand, Jotai, Context, signals? |
| `ARCH_DATA_PATTERN` | Data Access Pattern | Repository pattern, CQRS, event sourcing? |
| `ARCH_FILE_STRUCTURE` | Project Structure | Recommended folder structure for this stack? |
| `ARCH_ERROR_HANDLING` | Error Handling Strategy | Error handling patterns for this stack? |
| `ARCH_REALTIME` | Real-time Architecture | WebSockets, SSE, polling, CRDT? |

### Category D: Operational Concerns (`ops`)

| ID | Name | Research Question |
|----|------|-------------------|
| `OPS_TESTING` | Testing Strategy | Testing framework and approach for this stack? |
| `OPS_CI_CD` | CI/CD Pipeline | CI/CD approach for this stack and platform? |
| `OPS_MONITORING` | Monitoring/Logging | Logging and monitoring approach? |
| `OPS_SECURITY` | Security Practices | Security best practices for this stack? |
| `OPS_PERF` | Performance Optimization | Performance considerations for this use case? |
| `OPS_CONTAINER` | Containerization | Container strategy and configuration? |

### Category E: Custom (`custom`)

| ID | Name | Research Question |
|----|------|-------------------|
| `CUSTOM` | Custom Research | Dynamic - defined based on specific PRD needs not covered above |

---

## Phase 1: Foundation

**Purpose:** Establish context that all parallel research agents need.

### Step 1.1: Analyze PRD for Explicit Technology Choices

Read the PRD and identify any explicitly mentioned technologies:

```
EXPLICIT TECHNOLOGIES FOUND:
- Language: [specified or "not specified"]
- Framework: [specified or "not specified"]
- Database: [specified or "not specified"]
- Other: [list any other explicit tech mentions]
```

### Step 1.2: Detect Project Type and Constraints

Based on PRD analysis, determine:

```
PROJECT ANALYSIS:
- Project Type: [cli_tool | web_app | web_api | mobile_app | library | microservice | script | other]
- Has Frontend: [yes | no]
- Has Backend: [yes | no]
- Has Database: [yes | no]
- Has Authentication: [yes | no]
- Deployment Target: [specified target or "not specified"]
- Constraints: [list any constraints from PRD]
```

### Step 1.3: Select Research Opportunities

Based on the analysis above, select applicable opportunities from the catalog.

**Selection Rules:**
1. Skip opportunities where technology is explicitly specified in PRD
2. Always include `OPS_TESTING` (scaled by complexity)
3. Always include `VERSION_*` for any selected/specified technology
4. Include stack opportunities for any "not specified" areas that the project needs
5. Include architecture opportunities for non-trivial projects
6. Add `CUSTOM` if PRD has needs not covered by standard opportunities

**Output the selected opportunities:**

```
SELECTED RESEARCH OPPORTUNITIES:
1. [OPPORTUNITY_ID] - [Name] - [Brief rationale]
2. [OPPORTUNITY_ID] - [Name] - [Brief rationale]
...
```

### Step 1.4: Build Research Context

Create the shared context that will be passed to all research subagents:

```json
{
  "project_type": "[detected type]",
  "explicit_technologies": {
    "language": "[value or null]",
    "framework": "[value or null]",
    "database": "[value or null]"
  },
  "requirements": ["[requirement 1]", "[requirement 2]"],
  "constraints": ["[constraint 1]", "[constraint 2]"],
  "deployment_target": "[target or null]"
}
```

### Step 1.5: Store Foundation Results

Store the research context and selected opportunities in the database:

```bash
# Store research context in project_metadata
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Store research context
    context_items = [
        ('research_context_project_type', '[PROJECT_TYPE]'),
        ('research_context_language', '[LANGUAGE_OR_NULL]'),
        ('research_phase_status', 'foundation_complete')
    ]
    for key, value in context_items:
        conn.execute('INSERT OR REPLACE INTO project_metadata (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    print('✅ Research context stored')
"
```

Insert selected opportunities into database (execute once per opportunity):

```bash
# For each selected opportunity
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT INTO research_opportunities (id, category, name, research_question, status)
        VALUES (?, ?, ?, ?, 'pending')
    ''', ('[OPP_ID]', '[CATEGORY]', '[NAME]', '[QUESTION]'))
    conn.commit()
    print('✅ Opportunity [OPP_ID] queued')
"
```

---

## Phase 2: Parallel Research

**Purpose:** Execute research in parallel for wall-clock speed.

### Step 2.1: Prepare Subagent Prompts

For each selected opportunity, prepare a prompt using this template:

```markdown
You are a technology research agent. Research the following and provide a concise recommendation.

## Research Context
[Insert research_context JSON from Phase 1]

## Your Assignment
**Opportunity ID:** [OPPORTUNITY_ID]
**Research Question:** [RESEARCH_QUESTION from catalog]

## Instructions
1. Use WebSearch to find current, authoritative information
2. Use WebFetch to verify from official sources when possible
3. Focus on compatibility with the established context above
4. Prioritize stability and community support over cutting-edge features

## Required Output (Keep response under 300 words)

RECOMMENDATION: [Primary technology recommendation]
VERSION: [Specific version number - REQUIRED]
SOURCE: [Official URL where you verified this]
ALTERNATIVES: [1-2 alternatives with brief reason]
RATIONALE: [2-3 sentences on why this choice given the context]
COMPATIBILITY_NOTES: [Any compatibility considerations]
CONFIDENCE: [HIGH | MEDIUM | LOW]
```

### Step 2.2: Launch Parallel Research Agents

**CRITICAL:** Launch ALL research agents in a SINGLE message with multiple Task tool calls.

For each selected opportunity, invoke:

```
Task tool call:
- subagent_type: "general-purpose"
- description: "Research [OPPORTUNITY_ID]"
- prompt: [Prepared prompt from Step 2.1]
```

**Example for 3 opportunities:**
```
[Task 1: STACK_FRAMEWORK_API research]
[Task 2: OPS_TESTING research]
[Task 3: VERSION_FRAMEWORK research]
```

All tasks launch simultaneously for parallel execution.

### Step 2.3: Collect Results

As each subagent completes, parse the response and extract:
- RECOMMENDATION
- VERSION
- SOURCE
- ALTERNATIVES
- RATIONALE
- COMPATIBILITY_NOTES
- CONFIDENCE

### Step 2.4: Store Execution Records

For each completed research, store the execution record and update opportunity status:

```bash
# Record the execution and update opportunity
python3 -c "
import sys
from datetime import datetime
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Record execution
    conn.execute('''
        INSERT INTO research_executions
        (opportunity_id, execution_status, subagent_prompt, subagent_response, completed_at)
        VALUES (?, 'completed', ?, ?, ?)
    ''', ('[OPP_ID]', '''[PROMPT]''', '''[RESPONSE]''', datetime.now().isoformat()))

    # Update opportunity status
    conn.execute('''
        UPDATE research_opportunities
        SET status = 'completed',
            result_summary = ?,
            confidence = ?,
            researched_at = ?
        WHERE id = ?
    ''', ('[RECOMMENDATION]: [VERSION]', '[CONFIDENCE]', datetime.now().isoformat(), '[OPP_ID]'))

    conn.commit()
    print('✅ Execution recorded for [OPP_ID]')
"
```

---

## Phase 3: Review & Reconciliation

**Purpose:** Ensure coherent, conflict-free technology stack.

### Step 3.1: Aggregate All Results

List all research results in a summary:

```
RESEARCH RESULTS SUMMARY:
┌─────────────────────┬──────────────────┬─────────┬────────────┐
│ Opportunity         │ Recommendation   │ Version │ Confidence │
├─────────────────────┼──────────────────┼─────────┼────────────┤
│ STACK_FRAMEWORK_API │ FastAPI          │ 0.109.0 │ HIGH       │
│ OPS_TESTING         │ pytest           │ 8.0.0   │ HIGH       │
│ VERSION_FRAMEWORK   │ (verified)       │ 0.109.0 │ HIGH       │
└─────────────────────┴──────────────────┴─────────┴────────────┘
```

### Step 3.2: Check for Issues

Review results for:

**Coherence Check:**
- Do all selected technologies work together?
- Are there known incompatibilities?

**Conflict Check:**
- Did any agents make contradictory assumptions?
- Are there version mismatches?

**Gap Check:**
- Did we miss any critical technology decisions?
- Are there areas that need additional research?

**Confidence Check:**
- Are there any LOW confidence results?
- Should any be re-researched?

### Step 3.3: Resolve Issues (If Any)

**For minor issues:** Resolve directly using planner judgment.

**For research gaps:** Spawn targeted follow-up research:
```
"Given [CONTEXT], research [SPECIFIC QUESTION] considering [UPDATED CONTEXT]"
```

**For conflicts:** Determine which recommendation better fits the overall stack.

**For low confidence:** Consider re-research or flag for user input.

### Step 3.4: Approve and Commit Stack

Once all issues are resolved, commit the approved stack to database:

```bash
# For each approved technology
python3 -c "
import sys
import json
from datetime import datetime
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    # Insert technology
    conn.execute('''
        INSERT INTO technologies
        (name, category, version, decision_reason, opportunity_id, confidence, alternatives, compatibility_notes, source_type, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'researched', ?)
    ''', ('[NAME]', '[CATEGORY]', '[VERSION]', '[RATIONALE]', '[OPP_ID]', '[CONFIDENCE]',
          json.dumps(['[ALT1]', '[ALT2]']), '[COMPAT_NOTES]', datetime.now().isoformat()))

    # Add source URL
    conn.execute('''
        INSERT INTO technology_sources
        (technology_name, source_url, source_type, was_fetched, fetch_timestamp)
        VALUES (?, ?, 'official_docs', 1, ?)
    ''', ('[NAME]', '[SOURCE_URL]', datetime.now().isoformat()))

    conn.commit()
    print('✅ Technology [NAME] committed')
"
```

### Step 3.5: Update Research Status

```bash
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO project_metadata (key, value)
        VALUES ('research_phase_status', 'completed')
    ''')
    conn.commit()
    print('✅ Research phase completed')
"
```

---

## Phase 3 Output: Research Summary

After completing all phases, output a summary for plan.md:

```
═══════════════════════════════════════════════════════════════
                    RESEARCH COMPLETE
═══════════════════════════════════════════════════════════════

APPROVED TECHNOLOGY STACK:
──────────────────────────────────────────────────────────────
Language:    [language] [version]
Framework:   [framework] [version]
Database:    [database] [version] (if applicable)
Testing:     [testing framework] [version]
[Other technologies as applicable]

RESEARCH STATISTICS:
──────────────────────────────────────────────────────────────
Opportunities Researched: [N]
High Confidence:          [N]
Medium Confidence:        [N]
Low Confidence:           [N]

COMPATIBILITY VERIFIED: [YES/NO]
READY FOR PLANNING:     [YES/NO]

═══════════════════════════════════════════════════════════════
```

---

## Error Handling

### WebSearch Failure
If WebSearch fails or returns no results:
1. Retry with alternative query phrasing
2. If still failing, use LLM knowledge with MEDIUM confidence
3. Flag in compatibility_notes: "Verified via LLM knowledge, not web search"

### Subagent Timeout
If a subagent does not complete:
1. Record execution as 'failed' with error message
2. Attempt re-research once
3. If still failing, skip opportunity with status 'skipped'

### Parsing Failure
If subagent response doesn't match expected format:
1. Attempt to extract key information anyway
2. Set confidence to LOW
3. Flag for review in Phase 3

---

## Integration Notes

**This module is invoked by plan.md via prose-orchestration:**

plan.md instructs Claude to use the Read tool on `$IRIS_DIR/research.md` and execute its instructions inline. The invocation looks like:

```markdown
**CRITICAL:** Use the Read tool to read the file at `$IRIS_DIR/research.md`,
then execute its instructions inline as part of this planning session.
```

When invoked, Claude reads this file and follows all phases sequentially before returning control to plan.md for milestone creation.

**Database tables used:**
- `project_metadata` - Stores research context
- `research_opportunities` - Tracks selected opportunities and status
- `research_executions` - Records subagent execution history
- `technologies` - Stores approved technology stack
- `technology_sources` - Stores verification URLs

**Returns control to plan.md after:**
- Research summary is output
- All technologies are committed to database
- `research_phase_status` is set to 'completed'
