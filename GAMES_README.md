# NeuroWell Games Module

This module contains all the neuro-rehabilitation games for the NeuroWell native application.

## Available Games

### 1. Snake Game
- Tests hand-eye coordination and fine motor control
- Uses the webcam and hand tracking to control a snake using the index finger
- Eating food increases the snake's length and the player's score
- Duration: 60 seconds

### 2. Emoji Matching Game
- Tests memory and visual recognition
- Displays a target emoji that the patient must find on a 6x6 grid
- Correct matches earn points while incorrect ones result in point deductions
- Board refreshes every 20 seconds with a new target emoji

### 3. Ball Bouncing Game 
- Tests bilateral coordination and reflexes
- Uses both hands to bounce a ball between two paddles
- Each successful bounce earns points
- Duration: 30 seconds

## How to Use

1. From the main application, navigate to the "Game" section
2. Select the desired game from the game selection screen
3. Enter the patient's name to track their progress
4. Click "Start Game" to begin
5. After the game completes, the score will be automatically saved to the patient's profile

## Technical Details

### Hand Tracking
- Uses the MediaPipe library through cvzone's HandTrackingModule
- Tracks hand landmarks in real-time
- Uses the index finger position (landmark 8) to control game elements

### Game Architecture
- Each game is implemented as a separate QWidget that can be added to the main application
- Games run in their own threads to maintain UI responsiveness
- Camera and hand tracking settings are optimized for Windows systems

### Score Storage
- All game scores are stored in the patients_data.csv file
- Each game updates a separate column in the CSV:
  - Snake Game → Snake Score
  - Emoji Game → Emoji Score
  - Ball Game → Ball Score

## Adding New Games

To add a new game:
1. Create a new game UI file (e.g., `new_game_ui.py`)
2. Implement the game logic and UI components
3. Add navigation support via the `navigate_to_signal`
4. Add score tracking functionality
5. Import the new game in `main.py`
6. Add a button to launch the game in `game_ui.py` 