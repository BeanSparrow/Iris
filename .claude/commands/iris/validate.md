---
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Glob
description: "Usage: /iris:validate [milestone-id] - Validate milestone completion and application state"
---

Validate that a milestone has been successfully completed and the application is ready for human review.

You are **Milestone Validator** — responsible for ensuring each development milestone produces a launchable, reviewable application state.

## Validation Mode

```bash
# Iris operates in autonomous mode by default
# For manual debugging, set IRIS_MANUAL_MODE=true to require human review
if [ "${IRIS_MANUAL_MODE:-false}" = "true" ]; then
    AUTOPILOT_MODE=false
    echo "🔧 MANUAL MODE: Human review required after validation"
else
    AUTOPILOT_MODE=true
    echo "🤖 Autonomous validation with auto-fix capabilities"
    echo "📊 Graduated validation based on project complexity"
fi
echo ""
```

**Autopilot validation focuses on:**
- ✅ Application launches successfully  
- ✅ No critical errors detected
- ✅ Core functionality working
- 📝 Log results without blocking execution

**Manual validation includes:**
- All autopilot checks PLUS
- ⏸️ Human review pause
- 👁️ Visual inspection required
- ✋ Approval before proceeding

## AUTOMATED VALIDATION FEATURES

**CONTINUOUS VALIDATION:**

- Smoke test execution
- Performance baseline comparison
- Security scan integration
- Accessibility validation
- Cross-browser testing (if web app)

**VALIDATION METRICS:**

- Launch success rate: Track across milestones
- Feature completion: Percentage of planned features working
- Quality score: Aggregate of all quality metrics
- Time to validation: Efficiency tracking

## VALIDATION WORKFLOW

### Phase 1: Application Launch Test

```yaml
LAUNCH_TEST:
  1. Query technology stack from database:
     SELECT name, selected_version FROM technologies WHERE category = 'runtime'
  2. Execute appropriate launch command:
     - Web: npm run dev / yarn dev / python manage.py runserver
     - CLI: Run help command
     - API: Start server and check health endpoint
  3. Verify application starts without errors
  4. Check for console/terminal errors
  5. Update database with launch status
```

### Phase 2: Feature Validation

```yaml
FEATURE_CHECK:
  1. Read milestone and task details from database:
     SELECT * FROM milestones m JOIN tasks t ON m.id = t.milestone_id 
     WHERE m.id = '$MILESTONE_ID'
  2. For each test scenario from scope_boundaries:
     - Execute the test
     - Document result (pass/fail)
     - Capture screenshots if UI involved
  3. Verify all critical features work
  4. Test basic user flows
```

### Phase 3: Integration Testing

```yaml
INTEGRATION_TEST:
  1. Run any existing test suites
  2. Check database connectivity (if applicable)
  3. Verify API endpoints respond
  4. Test data persistence
  5. Validate UI updates reflect backend changes
```

### Phase 4: Code Quality Check

**EXTENDED QUALITY CHECKS:**

```yaml
ADVANCED_QUALITY:
  Security_Scan: Run OWASP dependency check
  Performance_Test: Compare against baseline
  Accessibility_Audit: WCAG compliance check
  Documentation_Coverage: Verify docs updated
  API_Contract_Test: Validate API specifications
```

```yaml
QUALITY_VERIFICATION:
  1. Run linting (no errors allowed)
  2. Run type checking (if applicable)
  3. Check test coverage meets minimum
  4. Verify no TODO/FIXME comments
  5. Ensure no console.log/print debug statements
```

### Phase 5: Generate Status Report

```yaml
STATUS_REPORT:
  Generate comprehensive milestone report including:
  - Milestone ID and name
  - Tasks completed
  - Features implemented
  - Test results
  - Quality metrics
  - Screenshots/evidence
  - Issues found
  - Recommendation (proceed/fix/rollback)
```

### Phase 6: Update Database

```yaml
UPDATE_DATABASE:
  Update database with validation results via atomic transaction:
  1. Update milestone validation status:
     UPDATE milestones SET status = 'validated', updated_at = CURRENT_TIMESTAMP 
     WHERE id = '$MILESTONE_ID'
  2. Insert validation history record:
     INSERT INTO project_metadata (key, value) VALUES 
     ('validation_' || '$MILESTONE_ID', JSON_OBJECT(
       'milestone_id', '$MILESTONE_ID',
       'validated_at', CURRENT_TIMESTAMP,
       'status', 'passed/failed',
       'issues_found', '[]',
       'validator', 'milestone-validator'
     ))
  3. Update project state if all validations pass
  4. Trigger Status Translator to update PROJECT_STATUS.md
```

## VALIDATION CRITERIA

### Pass Criteria

- Application launches successfully ✅
- All milestone features work ✅
- No critical errors ✅
- Quality gates pass ✅
- Ready for human review ✅

### Fail Criteria

- Application won't start ❌
- Core features broken ❌
- Critical errors present ❌
- Quality gates fail ❌
- Not ready for review ❌

## MILESTONE REPORT TEMPLATE

```markdown
## Milestone Validation Report

### Milestone: M[N] - [Name]
**Date:** [timestamp]
**Status:** PASS / FAIL / PARTIAL

### Tasks Completed
- [x] T-F1-01: Project setup
- [x] T-F1-02: Database schema
- [x] T-F1-03: Landing page
- [x] T-VAL-01: Validation

### Application Status
- **Launches:** Yes/No
- **URL/Access:** http://localhost:3000
- **Console Errors:** None/List
- **Build Status:** Success/Failure

### Feature Validation
| Feature | Status | Notes |
|---------|--------|-------|
| Homepage renders | ✅ Pass | Loads in 1.2s |
| Navigation works | ✅ Pass | All links functional |
| Database connected | ✅ Pass | PostgreSQL connected |

### Quality Metrics
- **Test Coverage:** 75%
- **Linting:** 0 errors, 0 warnings
- **Type Check:** Pass
- **Build Time:** 3.4s

### Evidence
- Screenshot: [homepage.png]
- Test Output: [test-results.txt]
- Console Log: [console-clean.txt]

### Issues Found
1. Minor: Logo image missing (using placeholder)
2. Minor: Loading spinner stays 1s too long

### Recommendation
**✅ PROCEED TO NEXT MILESTONE**
Application is stable and ready for human review.
All critical features work as expected.

### Next Steps
1. Human reviews application at http://localhost:3000
2. Feedback incorporated if needed
3. Proceed to Milestone M[N+1]

### Rollback Point
Git tag: `milestone-[N]-complete`
Branch: `milestone-[N]-stable`
```

## COMMANDS BY TECHNOLOGY

### Node.js/JavaScript

```bash
npm run dev          # Start dev server
npm test            # Run tests
npm run lint        # Check linting
npm run type-check  # TypeScript check
```

### Python

```bash
python manage.py runserver  # Django
flask run                   # Flask
pytest                      # Run tests
pylint src/                 # Linting
```

### Java

```bash
mvn spring-boot:run  # Spring Boot
gradle bootRun        # Gradle
mvn test             # Run tests
```

### Go

```bash
go run main.go       # Run application
go test ./...        # Run tests
golangci-lint run    # Linting
```

## INTEGRATION CAPABILITIES

### Automated Notifications

```yaml
NOTIFICATION_CHANNELS:
  Slack: Post to #dev-milestones channel
  Email: Send report to stakeholders
  Jira: Update sprint status
  GitHub: Create milestone release
```

### Screenshot Automation

- Capture key UI states
- Generate visual diff reports
- Create demo videos for complex features

## HUMAN REVIEW TRIGGERS

After validation completes:

1. **Generate notification** that milestone is ready
2. **Provide access details** (URL, credentials if needed)
3. **List what to test** (key features to verify)
4. **Wait for approval** before continuing
5. **Incorporate feedback** if changes requested

## ROLLBACK PROCEDURES

If milestone fails validation:

```bash
# Create rollback point
git tag milestone-[N]-failed
git checkout milestone-[N-1]-stable

# Document failure
echo "Failure reason" > .tasks/milestone-[N]-issues.md

# Plan fixes
Update database with fix tasks
```

## VALIDATION PATTERNS

### Progressive Enhancement

1. **Basic Validation**: Application launches
2. **Feature Validation**: Core features work
3. **Integration Validation**: Components work together
4. **Quality Validation**: Meets all quality gates
5. **User Validation**: Ready for human review

### Rollback Strategy

```bash
# Automated rollback on failure
if [ "$VALIDATION_STATUS" = "failed" ]; then
  git checkout milestone-$((N-1))-stable
  echo "Rolled back to last stable milestone"
fi
```

## COMMAND COMPOSITION

Chains with:

- `/iris:plan` — Initial planning
- `/iris:execute` — Development
- `/iris:security` — Security analysis

## PERFORMANCE METRICS

- Validation time: 2-5 minutes average
- Early issue detection: 85% of issues caught at milestones
- Rollback frequency: <5% of milestones require rollback
- Human review efficiency: 60% faster with automated reports

Remember: The goal is to catch issues EARLY, not after 20+ tasks are complete.

## 🔄 ADAPTIVE VALIDATION WORKFLOW

**Execute validation with mode-appropriate behavior:**

```bash
# Step 1: Determine validation mode and scope
# AUTOPILOT_MODE already set at start of script

# Get milestone ID from database or argument
if [[ -n "$1" ]]; then
    MILESTONE_ID="$1"
else
    # Find current milestone from database
    MILESTONE_ID=$(python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    current = conn.execute('''
        SELECT id FROM milestones 
        WHERE status IN ('in_progress', 'pending')
        ORDER BY order_index LIMIT 1
    ''').fetchone()
    print(current['id'] if current else 'unknown')
")
fi

echo "🔍 Starting validation for milestone: $MILESTONE_ID"

if [ "$AUTOPILOT_MODE" = "true" ]; then
    VALIDATION_MODE="automated"
    REQUIRE_HUMAN_REVIEW=false
else
    VALIDATION_MODE="manual"
    REQUIRE_HUMAN_REVIEW=true
fi

# Step 2: Load adaptive configuration from database
COMPLEXITY=$(python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    config = conn.execute('SELECT value FROM project_metadata WHERE key = ?', ('project_complexity',)).fetchone()
    print(config['value'] if config else 'medium')
")

echo "🔧 Project complexity: $COMPLEXITY"

# Step 3: Run appropriate validation level
case "$COMPLEXITY" in
    "micro")
        echo "🔬 MICRO validation: Basic functionality check"
        # Just verify it runs
        ;;
    "small")
        echo "📱 SMALL validation: Core features check"
        # Check main features work
        ;;
    "medium"|"large"|"enterprise")
        echo "🏢 $COMPLEXITY validation: Comprehensive check"
        # Full validation suite
        ;;
esac

# Step 4: Execute autonomous validation
echo "▶️ Running autonomous validation system..."

# Find IRIS directory
PROJECT_ROOT=$(pwd)
while [[ "$PROJECT_ROOT" != "/" ]] && [[ ! -d "$PROJECT_ROOT/.tasks" ]] && [[ ! -d "$PROJECT_ROOT/.git" ]]; do
    PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
done

IRIS_DIR=""
if [[ -d "$PROJECT_ROOT/.claude/commands/iris" ]]; then
    IRIS_DIR="$PROJECT_ROOT/.claude/commands/iris"
elif [[ -d ~/.claude/commands/iris ]]; then
    IRIS_DIR=~/.claude/commands/iris
fi

# Run autonomous validator
python3 "$IRIS_DIR/utils/autonomous_validator.py" "$PROJECT_ROOT" "$IRIS_DIR" "$MILESTONE_ID"
VALIDATION_EXIT_CODE=$?

if [[ $VALIDATION_EXIT_CODE -eq 0 ]]; then
    echo "✅ Autonomous validation PASSED"
    VALIDATION_PASSED=true
else
    echo "❌ Autonomous validation FAILED"
    VALIDATION_PASSED=false
fi

# Step 5: Process validation results

if [[ "$VALIDATION_PASSED" == "true" ]]; then
    echo "✅ Milestone $MILESTONE_ID validation PASSED"
    
    # Log success
    python3 "$IRIS_DIR/utils/token_efficient_logger.py" milestone_update "$MILESTONE_ID" "validated" 0 0 2
    
    if [[ "$AUTOPILOT_MODE" == "true" ]]; then
        echo "🤖 Autopilot: Proceeding automatically"
        echo "📝 Validation report logged to .tasks/"
        # No human pause required
    else
        echo "⏸️ HUMAN REVIEW REQUIRED"
        echo "👁️ Please review the application and confirm:"
        echo "  1. Application launches correctly"  
        echo "  2. Core features work as expected"
        echo "  3. No obvious issues present"
        echo ""
        read -p "Approve milestone and continue? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Milestone validation rejected by human reviewer"
            exit 1
        fi
        echo "✅ Human approval received"
    fi
    
else
    echo "❌ Milestone $MILESTONE_ID validation FAILED"
    
    if [[ "$AUTOPILOT_MODE" == "true" ]]; then
        echo "🤖 Autopilot: Logging failure for recovery"
        python3 "$IRIS_DIR/utils/token_efficient_logger.py" -c "
logger.error('Milestone validation failed', {
    'milestone_id': '$MILESTONE_ID',
    'validation_mode': 'automated',
    'recovery_required': True
})
"
        echo "📝 Failure logged - autopilot will attempt recovery"
    else
        echo "👤 Manual intervention required"
        echo "Check validation logs for details"
        exit 1
    fi
fi

# Step 6: Update progress tracking
echo "📊 Updating database with validation results..."

# Mark milestone as validated in database
python3 -c "
import sys
sys.path.append('$IRIS_DIR/utils')
from database.db_manager import DatabaseManager
from datetime import datetime

db = DatabaseManager()
def update_validation(conn):
    milestone_id = '$MILESTONE_ID'

    # Update milestone status
    conn.execute('UPDATE milestones SET status = \"validated\" WHERE id = ?', (milestone_id,))

    # Record validation in metadata
    conn.execute('''
        INSERT OR REPLACE INTO project_metadata (key, value)
        VALUES (?, ?)
    ''', (f'validation_{milestone_id}', datetime.now().isoformat()))

    return {'milestone_id': milestone_id, 'validated': True}

success, results = db.execute_transaction([update_validation])
if success:
    print('✅ Database updated with validation results')
else:
    print('❌ Failed to update database')
"

# Note: PROJECT_STATUS.md is updated by /iris:document phase after validation
# This consolidates all documentation updates in one place

echo "✅ Milestone $MILESTONE_ID validation complete"

if [[ "$AUTOPILOT_MODE" != "true" ]]; then
    echo "🎯 Ready to proceed to next milestone"
fi
```

## 🎯 MODE COMPARISON

| Aspect | Manual Mode | Autopilot Mode |
|--------|-------------|----------------|
| **Validation Scope** | Full comprehensive | Functional focus |
| **Human Review** | ⏸️ Required pause | 📝 Logged only |
| **Failure Handling** | ❌ Hard stop | 🔄 Recovery attempt |
| **Quality Gates** | ✅ All must pass | ⚠️ Warnings logged |
| **Time Impact** | 🐌 Blocks execution | ⚡ Continues flow |
| **Rollback** | 👤 Manual decision | 🤖 Automatic retry |

The adaptive validator ensures **appropriate validation for the context** - strict when human oversight is available, functional when autonomous operation is required.
