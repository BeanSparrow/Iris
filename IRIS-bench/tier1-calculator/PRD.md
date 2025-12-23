# Tier 1: Command-Line Calculator

## Overview

Build a command-line calculator application in Node.js that evaluates mathematical expressions.

## Requirements

### Core Functionality

1. **Expression Evaluation**
   - Accept a mathematical expression as a command-line argument
   - Support basic operations: addition (+), subtraction (-), multiplication (*), division (/)
   - Handle decimal numbers
   - Respect standard order of operations (PEMDAS/BODMAS)

2. **Input Handling**
   - Read expression from command-line arguments
   - Handle expressions with or without spaces (e.g., "5+3" and "5 + 3" both work)
   - Display clear error message for invalid expressions

3. **Output**
   - Display the result to stdout
   - Round results to 2 decimal places when necessary
   - Handle division by zero gracefully with an error message

### Example Usage

```bash
node calculator.js "5 + 3"
# Output: 8

node calculator.js "10 * 2 + 5"
# Output: 25

node calculator.js "100 / 4 - 10"
# Output: 15

node calculator.js "3.5 * 2"
# Output: 7

node calculator.js "10 / 0"
# Output: Error: Division by zero
```

## Technical Constraints

- **Language:** Node.js (JavaScript)
- **No external dependencies** for core logic (may use built-in modules only)
- Single file implementation is acceptable
- Must be runnable via `node calculator.js "<expression>"`

## Out of Scope

- Parentheses support
- Advanced operations (exponents, square roots, etc.)
- Interactive mode (REPL)
- History or memory functions

## Success Criteria

| Criterion | Pass Condition |
|-----------|----------------|
| Runs without errors | `node calculator.js "1 + 1"` executes |
| Basic arithmetic | All four operations produce correct results |
| Order of operations | `2 + 3 * 4` returns `14`, not `20` |
| Decimal handling | `5.5 + 2.5` returns `8` |
| Error handling | Division by zero shows error, doesn't crash |

## Complexity Metrics

| Metric | Expected Range |
|--------|----------------|
| Milestones | 1 |
| Tasks | 5-8 |
| Files Created | 1-3 |
| Estimated Time | 10-20 minutes |
