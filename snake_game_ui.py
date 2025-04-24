import math
import random
import cv2
import numpy as np
import pandas as pd
import time
import os
import gc
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QLineEdit, QMessageBox, QApplication, 
                            QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont, QImage
from cvzone.HandTrackingModule import HandDetector

# Set a higher resolution for the webcam for better visibility
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
PROCESS_EVERY_N_FRAME = 3  # Only process every 3rd frame

class SnakeGameClass:
    def __init__(self, pathFood):
        self.points = []     # Stores snake body points
        self.lengths = []  
        self.currentLength = 0    # Total snake length
        self.allowedLength = 150
        self.previousHead = (0, 0)
        
        # Optimize image loading
        try:
            self.imgFood = cv2.imread(pathFood, cv2.IMREAD_UNCHANGED)
            if self.imgFood is None:
                # Use a simple colored circle instead if image loading fails
                self.imgFood = np.zeros((50, 50, 4), dtype=np.uint8)
                cv2.circle(self.imgFood, (25, 25), 25, (0, 0, 255, 255), -1)
            else:
                # Resize food image to smaller dimensions to improve performance
                self.imgFood = cv2.resize(self.imgFood, (50, 50))
                
                if self.imgFood.shape[2] == 3:  
                    # Convert to BGRA if needed
                    self.imgFood = cv2.cvtColor(self.imgFood, cv2.COLOR_BGR2BGRA)
        except Exception as e:
            print(f"Error loading food image: {e}")
            # Fallback to a simple colored circle
            self.imgFood = np.zeros((50, 50, 4), dtype=np.uint8)
            cv2.circle(self.imgFood, (25, 25), 25, (0, 0, 255, 255), -1)
            
        self.hFood, self.wFood, _ = self.imgFood.shape
        self.foodPoint = (0, 0)
        self.score = 0
        self.gameOver = False
        self.randomFoodLocation()
        
    def randomFoodLocation(self):
        self.foodPoint = random.randint(100, WEBCAM_WIDTH-50), random.randint(80, WEBCAM_HEIGHT-50)
        
    def update(self, imgMain, currentHead):
        if self.gameOver:
            return imgMain

        # Process Qt events to keep UI responsive
        QApplication.processEvents()
        
        px, py = self.previousHead
        cx, cy = currentHead

        self.points.append([cx, cy])
        distance = math.hypot(cx - px, cy - py)
        self.lengths.append(distance)
        self.currentLength += distance
        self.previousHead = cx, cy

        # Length Reduction 
        while self.currentLength > self.allowedLength and self.lengths:
            self.currentLength -= self.lengths[0]
            self.lengths.pop(0)
            self.points.pop(0)
       
        # Draw snake
        if len(self.points) > 1:
            for i in range(1, len(self.points)):
                cv2.line(imgMain, tuple(self.points[i - 1]), tuple(self.points[i]), (0, 0, 255), 15)  # Thicker red line
            
            # Draw head
            if self.points:
                cv2.circle(imgMain, tuple(self.points[-1]), 15, (0, 255, 0), cv2.FILLED)  # Green head

        # Draw Food - improved drawing code
        rx, ry = self.foodPoint
        # Draw a solid circle for food instead of using image overlay to reduce flickering
        cv2.circle(imgMain, (rx, ry), 20, (0, 0, 255), cv2.FILLED)
        cv2.circle(imgMain, (rx, ry), 22, (255, 255, 255), 2)  # Add white border for better visibility
        
        # Collision detection
        if rx - 25 < cx < rx + 25 and ry - 25 < cy < ry + 25:
            self.randomFoodLocation()
            self.allowedLength += 50
            self.score += 1
            print(f"Score: {self.score}")  # Debug score updates

        return imgMain

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    score_update_signal = pyqtSignal(int)
    game_over_signal = pyqtSignal(int)  # Signal to send final score when game is over
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.game = None
        self.detector = None
        self.patient_id = None
        self.patient_name = None
        # Add buffer for smoother display
        self.base_frame = None
        # Set the initial game state
        self.game_over_shown = False
        
    def run(self):
        # Initialize detector with improved settings for better accuracy
        try:
            print("Initializing hand detector...")
            self.detector = HandDetector(detectionCon=0.7, maxHands=1)
            print("Hand detector initialized successfully")
        except Exception as e:
            print(f"Error initializing hand detector: {e}")
            # Continue without the detector - we'll use mouse position instead
            self.detector = None
        
        # Initialize game
        try:
            print("Creating game...")
            # Use relative path for better portability
            food_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "food.png")
            # Always create a fresh food image to ensure consistent behavior
            print("Creating a new food image...")
            # Create a simple food image using OpenCV
            food_img = np.zeros((50, 50, 4), dtype=np.uint8)
            cv2.circle(food_img, (25, 25), 25, (0, 0, 255, 255), -1)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(food_path), exist_ok=True)
            
            try:
                cv2.imwrite(food_path, food_img)
                print(f"Created new food image at {food_path}")
            except Exception as e:
                print(f"Error saving food image: {e}, using in-memory image instead")
                # Continue without saving to file
            
            self.game = SnakeGameClass(food_path)
            print("Game created successfully")
        except Exception as e:
            print(f"Error creating game: {e}")
            return
        
        # Create a fixed overlay for static UI elements to reduce flickering
        self.create_static_overlays()
        
        # Setup camera with improved settings for Windows
        try:
            print("Setting up camera...")
            # Try to use DirectShow backend on Windows for better performance
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
            cap.set(cv2.CAP_PROP_FPS, 30)  # Set target FPS
            
            if not cap.isOpened():
                print("Error: Could not open webcam with DirectShow, trying default")
                cap = cv2.VideoCapture(0)
                cap.set(3, WEBCAM_WIDTH)
                cap.set(4, WEBCAM_HEIGHT)
                
                if not cap.isOpened():
                    print("Error: Could not open webcam with any backend")
                    return
                
            print("Camera set up successfully")
        except Exception as e:
            print(f"Error setting up camera: {e}")
            try:
                # Fallback to basic camera setup
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    print("Error: Could not open webcam with fallback method")
                    return
            except Exception as e2:
                print(f"Fatal error setting up camera: {e2}")
                return
        
        # Initialize variables
        frame_count = 0
        start_time = time.time()
        game_duration = 60  # 60 seconds game duration
        
        # For mouse fallback if hand detection fails
        last_point = [WEBCAM_WIDTH // 2, WEBCAM_HEIGHT // 2]  # Default center position
        
        # Variables for framerate control
        last_frame_time = time.time()
        target_frame_time = 1.0 / 30  # Target 30 fps
        last_good_frame = None  # Keep track of the last successful frame
        
        # Create static UI elements
        self.create_static_overlays()
        
        self.running = True
        print("Starting game loop...")
        while self.running:
            # Control frame rate for smoother display
            current_time = time.time()
            elapsed_since_last_frame = current_time - last_frame_time
            
            # If we haven't waited long enough for the next frame, sleep
            if elapsed_since_last_frame < target_frame_time:
                sleep_time = target_frame_time - elapsed_since_last_frame
                time.sleep(sleep_time)
                continue
                
            # Grab a frame
            success, img = cap.read()
            if not success:
                print("Failed to get frame from camera")
                # Use the last good frame if available
                if last_good_frame is not None:
                    img = last_good_frame.copy()
                else:
                    time.sleep(0.1)
                    continue
            else:
                # Store this good frame for future use
                last_good_frame = img.copy()
                
            last_frame_time = time.time()  # Update our frame timing
                
            # Mirror the image for more intuitive control
            img = cv2.flip(img, 1)
            
            # Apply brightness and contrast enhancement to improve hand detection
            try:
                # Increase brightness and contrast slightly
                alpha = 1.2  # Contrast control (1.0-3.0)
                beta = 10    # Brightness control (0-100)
                img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
            except Exception as e:
                print(f"Error enhancing image: {e}")
            
            # Ensure the base frame matches the camera frame dimensions
            self.ensure_base_frame(img)
            
            # Create a fresh frame by blending with the base frame for consistent UI
            try:
                game_frame = img.copy()
                overlay_alpha = 0.2  # Subtle overlay
                cv2.addWeighted(self.base_frame, overlay_alpha, game_frame, 1 - overlay_alpha, 0, game_frame)
                img = game_frame
            except Exception as e:
                print(f"Error applying overlay: {e}")
                # Continue with original frame if blending fails
            
            # Only process every Nth frame to improve performance
            if frame_count % PROCESS_EVERY_N_FRAME == 0:
                # Find hands
                finger_found = False
                
                try:
                    if self.detector is not None:
                        # Create a clean frame for hand detection
                        detection_frame = img.copy()
                        
                        # Explicitly set draw parameter to True for better visualization
                        hands, detection_frame = self.detector.findHands(detection_frame, flipType=False, draw=True)
                        
                        # Use the detection result frame
                        img = detection_frame
                        
                        if hands:
                            # Get the position of the index finger
                            lmList = hands[0]['lmList']
                            
                            # Use different finger positions based on what's available
                            if len(lmList) > 8:
                                # First try index finger (for precise control)
                                pointIndex = lmList[8][0:2]
                                
                                # Draw a more visible cursor at the control point
                                cv2.circle(img, tuple(pointIndex), 15, (0, 255, 0), cv2.FILLED)
                                cv2.circle(img, tuple(pointIndex), 18, (255, 255, 255), 2)
                                
                                # Create tracking trail for the snake head
                                if frame_count % 2 == 0:  # Only add trail every other frame
                                    # Draw a line from last point to current point for visual continuity
                                    if not np.array_equal(last_point, pointIndex) and not np.array_equal(last_point, [WEBCAM_WIDTH // 2, WEBCAM_HEIGHT // 2]):
                                        cv2.line(img, tuple(last_point), tuple(pointIndex), (0, 255, 255), 4)
                                
                                last_point = pointIndex
                                finger_found = True
                            
                            # Add success indicator
                            cv2.putText(img, "Hand Detected!", (20, 110), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            
                            # Add visual guidance for improving tracking
                            if 'center' in hands[0]:
                                hand_center = hands[0]['center']
                                # Display distance from center to encourage keeping hand in frame
                                dist_from_center = np.sqrt((hand_center[0] - WEBCAM_WIDTH/2)**2 + (hand_center[1] - WEBCAM_HEIGHT/2)**2)
                                if dist_from_center > WEBCAM_WIDTH/3:
                                    cv2.putText(img, "Move hand closer to center", (20, 140), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                except Exception as e:
                    print(f"Error detecting hands: {e}")
                
                if not finger_found:
                    # Draw a circle at the last known position as a visual feedback
                    cv2.circle(img, tuple(last_point), 15, (0, 255, 255), cv2.FILLED)
                    cv2.circle(img, tuple(last_point), 18, (255, 255, 255), 2)
                    
                    if self.detector is not None:
                        # Add help message if detector exists but no hand is found
                        cv2.putText(img, "No hand detected - Show your hand to camera", (20, 110), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        # Add additional guidance
                        cv2.putText(img, "Make sure your index finger is visible", (20, 140), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Update game with finger position or last known position
                try:
                    img = self.game.update(img, last_point)
                    
                    # Emit score update (but not too frequently to avoid GUI thread overload)
                    if frame_count % 5 == 0:
                        self.score_update_signal.emit(self.game.score)
                except Exception as e:
                    print(f"Error updating game: {e}")
                    
                # Apply smoothing to the last_point to reduce jitter when hand not detected
                if not finger_found and frame_count > 5:
                    # If we lose tracking, don't jump immediately, smooth the transition
                    # This helps prevent sudden jumps in the snake position
                    smoothing_factor = 0.8  # 80% old position, 20% new position when tracking lost
                    last_point[0] = int(last_point[0] * smoothing_factor + WEBCAM_WIDTH/2 * (1 - smoothing_factor))
                    last_point[1] = int(last_point[1] * smoothing_factor + WEBCAM_HEIGHT/2 * (1 - smoothing_factor))
            
            # Check if game time is up
            elapsed_time = time.time() - start_time
            remaining_time = max(0, game_duration - int(elapsed_time))
            
            # Draw UI elements and game state in a clean, consistent way
            # Create a display buffer that we'll draw everything to - start with a clean copy of img
            display_buffer = img.copy()
            
            # Add a text overlay to show the game is running - on display buffer
            cv2.putText(display_buffer, f"Score: {self.game.score}", (20, 40), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Add hand detection status indicator
            hand_status = "Hand Tracking: Enabled" if self.detector is not None else "Hand Tracking: Disabled"
            cv2.putText(display_buffer, hand_status, (20, 90), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add timer to display
            cv2.putText(display_buffer, f"Time: {remaining_time}s", (WEBCAM_WIDTH - 150, 40), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            if elapsed_time >= game_duration and not self.game.gameOver:
                print("Game over - time's up!")
                self.game.gameOver = True
                
                # Create a clean game over overlay
                game_over_overlay = np.zeros_like(display_buffer)
                
                # Add semi-transparent dark background
                cv2.rectangle(game_over_overlay, (0, 0), (WEBCAM_WIDTH, WEBCAM_HEIGHT), (0, 0, 0), cv2.FILLED)
                
                # Add game over text
                cv2.putText(game_over_overlay, "GAME OVER!", (WEBCAM_WIDTH//2 - 120, WEBCAM_HEIGHT//2 - 20), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                cv2.putText(game_over_overlay, f"Final Score: {self.game.score}", (WEBCAM_WIDTH//2 - 120, WEBCAM_HEIGHT//2 + 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
                
                # Blend the game over overlay with the display buffer
                alpha = 0.7  # 70% overlay, 30% original image
                cv2.addWeighted(game_over_overlay, alpha, display_buffer, 1-alpha, 0, display_buffer)
                            
                # Convert the image to Qt format and emit it
                self.change_pixmap_signal.emit(display_buffer)
                
                # Wait a moment before signaling game over to ensure UI has time to update
                time.sleep(0.5)
                
                # Time expired, end game
                print(f"Game over! Final score: {self.game.score}")
                
                # Only send game over signal if not already shown
                if not self.game_over_shown:
                    # Update the patient's score in database
                    print(f"Updating score for patient ID: {self.patient_id} with score: {self.game.score}")
                    self.update_snake_score(self.patient_id, self.game.score)
                    
                    # Send game over signal
                    print(f"Emitting game_over_signal with score: {self.game.score}")
                    self.game_over_signal.emit(self.game.score)
                    self.game_over_shown = True
                
                # Keep showing the final frame for a while but don't sleep in this thread
                # The main thread will handle the dialog and cleanup
                break
            
            # Convert the image to Qt format and emit it
            self.change_pixmap_signal.emit(display_buffer)
            
            # Increment frame counter
            frame_count += 1
        
        # Release resources
        print("Releasing camera resources...")
        cap.release()
        print("Game thread finished")
    
    def stop(self):
        self.running = False
        self.wait()
        
        # Explicitly clean up resources to prevent memory leaks
        self.game = None
        self.detector = None
        self.base_frame = None
        gc.collect()  # Force garbage collection
    
    def update_snake_score(self, patient_id, score):
        """Update the patient's snake game score in the database"""
        try:
            print(f"Updating snake score for patient ID: {patient_id} with score: {score}")
            from db_utils import db
            
            # Update score directly using patient ID
            if db.update_assessment_score(patient_id, "Snake", score):
                print(f"Successfully updated Snake score to {score} for patient ID {patient_id}")
            else:
                print(f"Failed to update Snake score for patient ID {patient_id}")
        except Exception as e:
            print(f"Error updating snake score: {e}")
            import traceback
            traceback.print_exc()
    
    def create_static_overlays(self):
        """Create static overlay elements to reduce redrawing and flickering"""
        # We'll create the base frame dynamically when we have the actual camera frame
        # Just initialize with None for now
        self.base_frame = None
        
    def ensure_base_frame(self, frame):
        """Make sure the base frame matches the size of the camera frame"""
        if self.base_frame is None or self.base_frame.shape != frame.shape:
            # Create or recreate the base frame with the exact same dimensions as the camera frame
            height, width = frame.shape[:2]
            self.base_frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add a subtle border to the game area
            cv2.rectangle(self.base_frame, (5, 5), (width-5, height-5), 
                         (30, 30, 50), 2)
            
            # Create text label backgrounds with consistent size and position
            # Score area - top left
            cv2.rectangle(self.base_frame, (10, 10), (150, 60), 
                         (30, 30, 30), cv2.FILLED)
            
            # Hand tracking status area - top left, below score
            cv2.rectangle(self.base_frame, (10, 70), (350, 100), 
                         (30, 30, 30), cv2.FILLED)
            
            # Timer area - top right
            cv2.rectangle(self.base_frame, (width-160, 10), (width-10, 60), 
                         (30, 30, 30), cv2.FILLED)
            
            # Game area
            cv2.rectangle(self.base_frame, (10, 50), (width-10, height-50), 
                         (20, 20, 20), 1)

class SnakeGameUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None, patient_id=None, patient_name=None):
        super().__init__(parent)
        self.parent = parent
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.init_ui()
        
        # Initialize variables
        self.video_thread = None
        self.game_started = False
        self.game_finished = False
        self.current_score = 0
        
        # For double buffering
        self.current_pixmap = None
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self.swap_buffers)
        self.buffer_timer.start(33)  # ~30fps for buffer swapping
        
        # Start the game automatically if patient info is provided
        if patient_id is not None:
            self.start_game()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create modern header/title bar
        header_container = QFrame()
        header_container.setObjectName("header_container")
        header_container.setStyleSheet("""
            #header_container {
                background-color: #2C3E50;
                min-height: 70px;
            }
        """)
        
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # App logo/title
        logo_label = QLabel("NeuroWell")
        logo_label.setStyleSheet("""
            font-size: 22pt;
            font-weight: bold;
            color: white;
        """)
        
        # User info display
        user_info = QLabel("Snake Game Assessment")
        user_info.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 12pt;
        """)
        
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        header_layout.addWidget(user_info)
        
        # Create modern navigation bar
        navbar = QFrame()
        navbar.setObjectName("navbar")
        navbar.setMaximumHeight(60)
        
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setSpacing(5)
        
        # Create navigation buttons for healthcare provider UI
        sections = [
            {"name": "Home", "icon": "home"},
            {"name": "Physio", "icon": "accessibility"},
            {"name": "Hand", "icon": "pan_tool"},
            {"name": "Game", "icon": "sports_esports"},
            {"name": "Result", "icon": "analytics"},
            {"name": "Logout", "icon": "logout"}
        ]
        
        for section in sections:
            button = QPushButton(section["name"])
            button.setObjectName(f"nav_{section['name'].lower()}")
            
            # Highlight current page
            if section["name"] == "Game":
                button.setStyleSheet("""
                    background-color: rgba(255, 255, 255, 0.2);
                    font-weight: bold;
                """)
                button.setChecked(True)
            
            # Connect the navigation handler
            button.clicked.connect(self.create_navigation_handler(section["name"]))
            navbar_layout.addWidget(button)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Content area
        content_container = QFrame()
        content_container.setObjectName("content_container")
        content_container.setStyleSheet("""
            #content_container {
                background-color: #F5F7FA;
            }
        """)
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Game setup area
        setup_container = QFrame()
        setup_container.setObjectName("dashboard_widget")
        setup_layout = QVBoxLayout(setup_container)
        
        setup_title = QLabel("Snake Game Setup")
        setup_title.setObjectName("dashboard_title")
        setup_layout.addWidget(setup_title)
        
        # Replace manual patient input with display of selected patient
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        
        if self.patient_id is not None and self.patient_name is not None:
            patient_display = QLabel(f"{self.patient_name} (ID: {self.patient_id})")
            patient_display.setStyleSheet("font-weight: bold; color: #3498DB;")
            form_layout.addRow("Selected Patient:", patient_display)
        else:
            patient_display = QLabel("No patient selected")
            patient_display.setStyleSheet("color: #E74C3C; font-style: italic;")
            form_layout.addRow("Patient:", patient_display)

        setup_layout.addLayout(form_layout)
        
        # Debug print to track initialization
        print("Initializing SnakeGameUI interface...")
        
        # Initialization of start_button
        print("Creating start button...")
        self.start_button = QPushButton("Start Game")
        self.start_button.setObjectName("success")
        self.start_button.setStyleSheet("""
            background-color: #2ECC71;
            font-size: 12pt;
            padding: 10px;
        """)
        self.start_button.clicked.connect(self.start_game)
        setup_layout.addWidget(self.start_button)
        print(f"Start button created and configured: {self.start_button}")
        
        content_layout.addWidget(setup_container)
        
        # Game display area with better size - make it larger to fit the webcam properly
        display_container = QFrame()
        display_container.setObjectName("dashboard_widget")
        display_layout = QVBoxLayout(display_container)
        
        display_title = QLabel("Game Display")
        display_title.setObjectName("dashboard_title")
        display_layout.addWidget(display_title)
        
        # Status display for backward compatibility
        self.status_label = QLabel("Status: Ready to start")
        self.status_label.setStyleSheet("""
            color: #3498DB;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        display_layout.addWidget(self.status_label)
        
        # Score display
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2ECC71;
            margin-bottom: 10px;
        """)
        display_layout.addWidget(self.score_label)
        
        # Game display - webcam feed
        self.game_display = QLabel()
        self.game_display.setAlignment(Qt.AlignCenter)
        self.game_display.setMinimumSize(WEBCAM_WIDTH, WEBCAM_HEIGHT)
        self.game_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.game_display.setStyleSheet("""
            background-color: #000;
            border: 2px solid #3498DB;
            border-radius: 5px;
        """)
        display_layout.addWidget(self.game_display)
        
        # Game instructions
        instructions_label = QLabel("Use your index finger to control the snake. Collect food items to grow the snake and increase your score.")
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("color: #7F8C8D; margin-top: 10px;")
        display_layout.addWidget(instructions_label)
        
        # Add spacer to ensure the game display is centered when window is larger
        display_layout.addStretch()
        
        content_layout.addWidget(display_container)
        
        # Set the content widget for the scroll area
        scroll_area.setWidget(content_container)
        
        # Add all major containers to the main layout
        main_layout.addWidget(header_container)
        main_layout.addWidget(navbar)
        main_layout.addWidget(scroll_area, 1)  # Give it a stretch factor
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler
    
    def start_game(self):
        # Debug information
        print("Starting snake game...")
        if self.patient_id is None:
            print("No patient ID provided, game may not save scores")
        else:
            print(f"Patient ID: {self.patient_id}, Name: {self.patient_name}")
        
        # Cleanup any existing video thread
        self.cleanup_video_thread()
        
        # Start the game
        try:
            # Create a new thread for the camera
            self.video_thread = VideoThread()
            
            # Set patient information
            self.video_thread.patient_id = self.patient_id
            self.video_thread.patient_name = self.patient_name
            
            # Connect signals and slots
            self.video_thread.change_pixmap_signal.connect(self.update_image)
            self.video_thread.score_update_signal.connect(self.update_score)
            self.video_thread.game_over_signal.connect(self.game_over)
            
            # Start the video thread
            self.video_thread.running = True
            self.video_thread.start()
            
            # Update UI
            self.game_started = True
            self.status_label.setText("Status: Game in progress")
            self.start_button.setEnabled(False)
            self.start_button.setText("Game in Progress")
            
        except Exception as e:
            print(f"Error starting game: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to start game: {str(e)}")
    
    def swap_buffers(self):
        """Swap the front and back buffers to update the display"""
        if hasattr(self, 'next_frame') and self.next_frame is not None and not self.next_frame.isNull():
            try:
                self.game_display.setPixmap(self.next_frame)
                # Process events to keep UI responsive
                QApplication.processEvents()
            except Exception as e:
                print(f"Error updating game display: {str(e)}")
    
    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        # Store the next frame in the buffer instead of immediately updating
        # This reduces UI thread contention and prevents flickering
        self.next_frame = qt_img
        
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        # Make sure the image has the right dimensions
        if cv_img.shape[1] != WEBCAM_WIDTH or cv_img.shape[0] != WEBCAM_HEIGHT:
            cv_img = cv2.resize(cv_img, (WEBCAM_WIDTH, WEBCAM_HEIGHT))
            
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(WEBCAM_WIDTH, WEBCAM_HEIGHT, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
    @pyqtSlot(int)
    def update_score(self, score):
        """Update the score display"""
        self.score_label.setText(f"Score: {score}")
    
    @pyqtSlot(int)
    def game_over(self, final_score):
        """Handle game over event"""
        print(f"Game over called with score: {final_score}")
        
        self.game_finished = True
        self.score_label.setText(f"Score: {final_score}")
        self.status_label.setText("Status: Game completed")
        
        try:
            # Try to re-enable the start button
            if self.start_button:
                print(f"Re-enabling start button: {self.start_button}")
                self.start_button.setEnabled(True)
            else:
                print("Warning: start_button is None in game_over")
        except Exception as e:
            print(f"Error re-enabling start button: {e}")
            # Don't try to recreate here as it's less critical
        
        # Show game over message with final score after a short delay
        # to let the UI finish showing the game over screen
        QTimer.singleShot(500, lambda: self.show_game_over_dialog(final_score))
    
    def show_game_over_dialog(self, final_score):
        """Show game over dialog in a safer way"""
        try:
            QMessageBox.information(self, "Game Over", f"Game completed! Final score: {final_score}")
        except Exception as e:
            print(f"Error showing game over message: {e}")
        
        # Clean up video thread after showing the dialog
        self.cleanup_video_thread()
    
    def cleanup_video_thread(self):
        """Clean up video thread safely"""
        if self.video_thread:
            try:
                if self.video_thread.isRunning():
                    self.video_thread.stop()
                self.video_thread = None
            except Exception as e:
                print(f"Error cleaning up video thread: {e}")
            
    def closeEvent(self, event):
        # Stop the buffer timer
        try:
            self.buffer_timer.stop()
        except Exception as e:
            print(f"Error stopping buffer timer: {e}")
        
        # Clean up video thread
        self.cleanup_video_thread()
        
        # Force garbage collection
        gc.collect()
        
        event.accept() 