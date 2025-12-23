# Tier 2: Terminal Snake Game

## Overview

Build a classic Snake game that runs in the terminal using Node.js. The player controls a snake that grows by eating food while avoiding walls and its own tail.

## Requirements

### Core Gameplay

1. **Snake Movement**
   - Snake moves continuously in the current direction
   - Player controls direction using arrow keys (or WASD)
   - Snake cannot reverse direction (e.g., cannot go left if moving right)
   - Movement updates at a consistent game tick rate

2. **Food System**
   - Food appears at random positions on the game board
   - When snake eats food, it grows by one segment
   - New food spawns immediately after eating
   - Food cannot spawn on the snake's body

3. **Collision Detection**
   - Game ends if snake hits the wall (board boundary)
   - Game ends if snake hits its own body
   - Display "Game Over" message when collision occurs

4. **Scoring**
   - Score increases by 10 points for each food eaten
   - Display current score during gameplay
   - Display final score on game over

### User Interface

1. **Game Board**
   - Render game board in terminal using ASCII characters
   - Minimum board size: 20x15 characters
   - Clear visual distinction between snake, food, and boundaries
   - Suggested characters:
     - Snake head: `@`
     - Snake body: `O`
     - Food: `*`
     - Border: `#` or box-drawing characters

2. **Display Elements**
   - Show current score above or below game board
   - Show controls hint at game start
   - Clear "Game Over" screen with final score

3. **Game Flow**
   - Start screen with "Press any key to start" message
   - Gameplay loop until collision
   - Game over screen with option to restart or quit

### Example Display

```
Score: 30

####################
#                  #
#                  #
#    *             #
#                  #
#        OOO@      #
#                  #
#                  #
####################

Controls: Arrow keys to move, Q to quit
```

## Technical Constraints

- **Language:** Node.js (JavaScript)
- **Terminal rendering:** Use a library like `blessed`, `ink`, or raw ANSI escape codes
- **Input handling:** Non-blocking keyboard input for real-time control
- Must be runnable via `npm start` or `node index.js`

## Out of Scope

- Multiple difficulty levels
- High score persistence
- Multiplayer mode
- Sound effects
- Pause functionality

## Success Criteria

| Criterion | Pass Condition |
|-----------|----------------|
| Game starts | Running `npm start` displays the game board |
| Snake moves | Arrow keys change snake direction |
| Food works | Eating food increases score and snake length |
| Wall collision | Hitting border ends game |
| Self collision | Hitting own body ends game |
| Score display | Score visible during and after gameplay |

## Verification Protocol

1. Start the game
2. Move snake in all four directions
3. Eat at least 3 food items (score should be 30+)
4. Verify snake grows with each food
5. Intentionally hit a wall - game should end
6. Restart and intentionally hit snake's tail - game should end

## Complexity Metrics

| Metric | Expected Range |
|--------|----------------|
| Milestones | 2-3 |
| Tasks | 10-15 |
| Files Created | 3-6 |
| Estimated Time | 30-60 minutes |
