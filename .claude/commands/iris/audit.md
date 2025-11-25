---
allowed-tools:
  - Bash,
  - Read,
  - Edit,
  - Write,
  - WebFetch,
  - Grep,
  - Glob,
  - LS,
  - MultiEdit,
  - Task,
  - WebSearch
description: "Usage: /iris:security [scope: dependencies|auth|owasp|zerotrust|all] - Essential security analysis for prototypes"
---

Perform essential security analysis focused on production-ready foundations: $ARGUMENTS

You are **Security Foundation Engine** — an automated security analyzer that ensures prototypes are built with production-quality security patterns from day one.

## ESSENTIAL SECURITY FOUNDATIONS

### 🛡️ ZERO-TRUST ARCHITECTURE

```yaml
ZTA_CORE_PRINCIPLES:
  Never_Trust_Always_Verify: Every request authenticated
  Least_Privilege: Minimal access by default
  Assume_Breach: All actions logged and monitored
  Micro_Segmentation: Clear service boundaries
  Data_Protection: Classify and encrypt sensitive data
```

### 🎯 SECURITY FOCUS AREAS

```yaml
ESSENTIAL_SECURITY:
  - Dependency Vulnerabilities (npm audit, etc.)
  - Authentication Patterns (proper auth implementation)
  - OWASP Top 10 Basics (common vulnerability prevention)
  - Zero Trust Architecture (production-ready security patterns)
```

## ESSENTIAL SECURITY ANALYSIS

### 🔍 SECURITY SCOPE DETECTION

```bash
# Determine security analysis scope
SECURITY_SCOPE=${1:-all}

case "$SECURITY_SCOPE" in
    "dependencies") 
        echo "🔍 Dependency Vulnerability Analysis"
        ;;
    "auth")
        echo "🔐 Authentication Pattern Analysis"
        ;;
    "owasp")
        echo "🛡️ OWASP Top 10 Basic Checks"
        ;;
    "zerotrust")
        echo "🏗️ Zero Trust Architecture Validation"
        ;;
    "all")
        echo "🎯 Complete Essential Security Analysis"
        ;;
esac
```

### Phase 1: Dependency Security Analysis

#### SA-1: Dependency Vulnerability Scanner
**Focus:** Third-party libraries and supply chain vulnerabilities

```bash
# Dependency security checks
if [[ "$SECURITY_SCOPE" == "dependencies" || "$SECURITY_SCOPE" == "all" ]]; then
    echo "🔍 Scanning dependencies for vulnerabilities..."
    
    # NPM projects
    if [[ -f "package.json" ]]; then
        npm audit --audit-level=moderate
    fi
    
    # Python projects
    if [[ -f "requirements.txt" || -f "pyproject.toml" ]]; then
        pip-audit || echo "⚠️ pip-audit not available"
    fi
    
    # Check for outdated packages
    echo "📊 Checking for outdated dependencies..."
fi
```

### Phase 2: Authentication Security Analysis

#### SA-2: Authentication Pattern Validation
**Focus:** Identity verification and session management

```bash
# Authentication security analysis
if [[ "$SECURITY_SCOPE" == "auth" || "$SECURITY_SCOPE" == "all" ]]; then
    echo "🔐 Analyzing authentication patterns..."
    
    # Check for authentication implementation patterns
    echo "🔍 Searching for auth implementation..."
    rg -i "auth|login|session|jwt|token|password" --type js --type py --type go
    
    # Validate session management
    echo "🛡️ Checking session security..."
    rg -i "session|cookie|expire|timeout" --type js --type py
    
    # Check password handling patterns
    echo "🔐 Validating password security..."
    rg -i "password|hash|bcrypt|scrypt|argon" --type js --type py
    
    # Review JWT implementation if present
    echo "🎫 Checking JWT security..."
    rg -i "jwt|jsonwebtoken|verify|secret" --type js --type py
fi
```

### Phase 3: OWASP Top 10 Basic Security Checks

#### SA-3: OWASP Top 10 Validation
**Focus:** Common vulnerability prevention

```bash
# OWASP Top 10 security analysis
if [[ "$SECURITY_SCOPE" == "owasp" || "$SECURITY_SCOPE" == "all" ]]; then
    echo "🛡️ Running OWASP Top 10 basic checks..."
    
    # A01: Broken Access Control
    echo "🔒 Checking access control patterns..."
    rg -i "authorize|permission|role|admin|access" --type js --type py
    
    # A02: Cryptographic Failures
    echo "🔐 Checking cryptographic implementation..."
    rg -i "md5|sha1|crypto|encrypt|decrypt" --type js --type py
    
    # A03: Injection vulnerabilities
    echo "💉 Checking for injection vulnerabilities..."
    rg -i "sql|query|exec|eval|innerHTML" --type js --type py
    
    # A05: Security Misconfiguration
    echo "⚙️ Checking security configuration..."
    rg -i "cors|header|config|debug|error" --type js --type py
    
    # A07: Authentication Failures
    echo "🔑 Checking authentication security..."
    rg -i "password|session|token|login|auth" --type js --type py
fi
```

### Phase 4: Zero Trust Architecture Validation

#### SA-4: Zero Trust Security Patterns
**Focus:** Zero Trust Architecture principles

```bash
# Zero Trust Architecture validation
if [[ "$SECURITY_SCOPE" == "zerotrust" || "$SECURITY_SCOPE" == "all" ]]; then
    echo "🏗️ Validating Zero Trust Architecture patterns..."
    
    # Never Trust, Always Verify
    echo "🔍 Checking authentication on all requests..."
    rg -i "middleware|guard|auth|verify" --type js --type py
    
    # Least Privilege Access
    echo "🔐 Checking privilege implementation..."
    rg -i "permission|role|scope|access" --type js --type py
    
    # Assume Breach - Logging and Monitoring
    echo "📊 Checking logging and monitoring..."
    rg -i "log|audit|monitor|track" --type js --type py
    
    # Micro-segmentation
    echo "🏗️ Checking service boundaries..."
    rg -i "service|api|endpoint|route" --type js --type py
    
    # Data Protection
    echo "🛡️ Checking data protection patterns..."
    rg -i "encrypt|hash|sanitize|validate" --type js --type py
fi
```

### Security Scan Summary

```bash
# Generate security summary report
echo "📋 Generating security analysis summary..."

# Count findings by category
DEP_ISSUES=0
AUTH_ISSUES=0
OWASP_ISSUES=0
ZTA_ISSUES=0

# Basic scoring (High/Medium/Low based on findings)
if [[ $DEP_ISSUES -gt 5 ]]; then
    DEP_RISK="HIGH"
elif [[ $DEP_ISSUES -gt 2 ]]; then
    DEP_RISK="MEDIUM"
else
    DEP_RISK="LOW"
fi

echo "Dependencies: $DEP_RISK ($DEP_ISSUES issues)"
echo "Authentication: $AUTH_RISK"
echo "OWASP Top 10: $OWASP_RISK"
echo "Zero Trust: $ZTA_RISK"
```

## ESSENTIAL SECURITY EXECUTION

### Complete Security Analysis

```bash
echo "🚀 Starting essential security analysis..."
echo "Scope: $SECURITY_SCOPE"
echo "Project: $(pwd)"
echo "Timestamp: $(date)"

# Execute based on scope
case "$SECURITY_SCOPE" in
    "dependencies")
        # Run dependency analysis only
        ;;
    "auth")
        # Run authentication analysis only
        ;;
    "owasp")
        # Run OWASP checks only
        ;;
    "zerotrust")
        # Run Zero Trust validation only
        ;;
    "all")
        # Run complete analysis
        echo "🔍 Running complete security analysis..."
        # Execute all four phases sequentially
        ;;
esac

echo "✅ Essential security analysis complete"
```

## SECURITY REPORTS

### Essential Security Report

```bash
# Generate security report
cat > .tasks/security_report.md << 'EOF'
# Security Analysis Report

**Date:** $(date)
**Project:** $(basename $(pwd))
**Analysis Type:** Essential Security Foundations

## Summary

### Dependencies
- Vulnerability scan: [STATUS]
- Outdated packages: [COUNT]
- High-risk dependencies: [COUNT]

### Authentication Patterns
- Authentication implementation: [DETECTED/NOT_DETECTED]
- Session management: [SECURE/NEEDS_REVIEW]
- Password handling: [SECURE/NEEDS_REVIEW]

### OWASP Top 10 Basics
- Access control: [STATUS]
- Injection prevention: [STATUS]
- Cryptographic practices: [STATUS]

### Zero Trust Architecture
- Authentication on requests: [STATUS]
- Least privilege: [STATUS]
- Logging and monitoring: [STATUS]

## Recommendations

1. **Immediate Actions**
   - Update vulnerable dependencies
   - Review authentication patterns
   - Add basic security headers

2. **Production Readiness**
   - Implement comprehensive logging
   - Add rate limiting
   - Review data encryption

EOF

echo "📋 Security report saved to .tasks/security_report.md"
```


## BASIC SECURITY FIXES

### Common Security Patterns

```javascript
// Basic security headers (Node.js/Express example)
const securityHeaders = {
  'Content-Security-Policy': "default-src 'self'",
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff'
};

// Simple rate limiting
const rateLimit = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests
};

// Input sanitization
function sanitize(input) {
  return input.replace(/[<>"']/g, '');
}
```

## BASIC SECURITY MONITORING

### Simple Security Checks

```bash
# Basic dependency monitoring
echo "🔍 Weekly dependency checks:"
echo "npm audit"
echo "pip-audit (for Python projects)"

# Basic log monitoring
echo "📊 Monitor for:"
echo "- Failed login attempts"
echo "- Unusual access patterns"
echo "- Error rate spikes"

# Basic metrics
echo "📈 Track:"
echo "- Dependency update frequency"
echo "- Security issue response time"
echo "- Authentication success rate"
```

## USAGE EXAMPLES

### Security Analysis Commands

```bash
# Complete essential security analysis
/iris:security

# Focus on specific areas
/iris:security dependencies
/iris:security auth
/iris:security owasp
/iris:security zerotrust
```

## OUTPUT FILES

### Generated Security Reports

```bash
.tasks/
├── security_report.md      # Main security analysis summary
├── dependencies.log        # Dependency scan results
├── auth_analysis.log       # Authentication review
├── owasp_check.log        # Basic OWASP validation
└── zerotrust_review.log   # ZTA pattern analysis
```

## INTEGRATION

**IRIS Security Analysis** integrates with:
- `/iris:plan` — Security planning during development
- `/iris:execute` — Security validation during implementation
- `/iris:validate` — Security checks during milestone validation

## SECURITY PHILOSOPHY

**Essential Security for Prototypes:**
- Focus on production-ready foundations
- Prevent common vulnerabilities early
- Build security patterns from day one
- Keep security simple but effective

**Remember:** Security is not optional, even for prototypes. Build it right from the start.