import math
import random
import cv2
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QMessageBox, QSplitter, QComboBox, QFormLayout, QLineEdit, QFrame, QGridLayout, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot, QThread
from PyQt5.QtGui import QPixmap, QFont, QImage
import time
import gc
from cvzone.HandTrackingModule import HandDetector
import os
from patient_dropdown import PatientDropdown

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
        # Draw a solid circle for food in case the image doesn't work
        cv2.circle(imgMain, (rx, ry), 20, (0, 0, 255), cv2.FILLED)
        
        try:
            # Now try to overlay the food image
            y1, y2 = ry - self.hFood // 2, ry + self.hFood // 2
            x1, x2 = rx - self.wFood // 2, rx + self.wFood // 2
            
            # Make sure coordinates are in bounds
            if 0 <= y1 < imgMain.shape[0] and 0 <= y2 < imgMain.shape[0] and 0 <= x1 < imgMain.shape[1] and 0 <= x2 < imgMain.shape[1]:
                # Get shapes for array slicing
                h, w = y2 - y1, x2 - x1
                
                if h > 0 and w > 0:
                    # Extract the alpha channel
                    alpha = self.imgFood[:h, :w, 3] / 255.0
                    alpha = np.expand_dims(alpha, axis=2)
                    
                    # Extract the BGR channels
                    food_bgr = self.imgFood[:h, :w, :3]
                    
                    # Get the destination region
                    dest_region = imgMain[y1:y2, x1:x2]
                    
                    # Blend using alpha
                    if dest_region.shape[:2] == food_bgr.shape[:2]:
                        imgMain[y1:y2, x1:x2] = dest_region * (1 - alpha) + food_bgr * alpha
        except Exception as e:
            print(f"Error drawing food: {e}")

        # Collision detection
        if rx - self.wFood // 2 < cx < rx + self.wFood // 2 and ry - self.hFood // 2 < cy < ry + self.hFood // 2:
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
        
    def run(self):
        # Initialize detector with improved settings for better accuracy
        try:
            print("Initializing hand detector...")
            # Increase detection confidence and enable maximum hand tracking
            self.detector = HandDetector(detectionCon=0.5, maxHands=1)
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
            # Fallback to creating a food image if file doesn't exist
            if not os.path.exists(food_path):
                print(f"Food image not found at {food_path}, creating a new one...")
                # Create a simple food image using OpenCV
                food_img = np.zeros((50, 50, 4), dtype=np.uint8)
                cv2.circle(food_img, (25, 25), 25, (0, 0, 255, 255), -1)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(food_path), exist_ok=True)
                
                cv2.imwrite(food_path, food_img)
                print(f"Created new food image at {food_path}")
                
            self.game = SnakeGameClass(food_path)
            print("Game created successfully")
        except Exception as e:
            print(f"Error creating game: {e}")
            return
        
        # Setup camera with improved settings for Windows
        try:
            print("Setting up camera...")
            # Try to use DirectShow backend on Windows for better performance
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            cap.set(3, WEBCAM_WIDTH)
            cap.set(4, WEBCAM_HEIGHT)
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
        
        # Add variables for framerate control
        last_frame_time = time.time()
        target_frame_time = 1.0 / 30  # Target 30 fps
        last_good_frame = None  # Store the last good frame
        
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
                # If we have a previous good frame, use it instead of skipping
                if last_good_frame is not None:
                    img = last_good_frame.copy()
                else:
                    time.sleep(0.1)
                    continue
            else:
                # Store this good frame for future use if needed
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
            
            # Add a text overlay to show the game is running
            cv2.putText(img, f"Score: {self.game.score}", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Add hand detection status indicator
            if frame_count % PROCESS_EVERY_N_FRAME == 0:
                hand_status = "Hand Tracking: Enabled" if self.detector is not None else "Hand Tracking: Disabled"
                cv2.putText(img, hand_status, (20, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)
            
            # Only process every Nth frame to improve performance
            if frame_count % PROCESS_EVERY_N_FRAME == 0:
                # Find hands
                finger_found = False
                
                try:
                    if self.detector is not None:
                        # Explicitly set draw parameter to True for better visualization
                        hands, img = self.detector.findHands(img, flipType=False, draw=True)
                        
                        if hands:
                            # Get the position of the index finger
                            lmList = hands[0]['lmList']
                            pointIndex = lmList[8][0:2]
                            last_point = pointIndex
                            finger_found = True
                            
                            # Draw all hand landmarks for better visualization
                            cv2.circle(img, tuple(pointIndex), 15, (0, 255, 0), cv2.FILLED)
                            cv2.circle(img, tuple(pointIndex), 18, (255, 255, 255), 2)
                            
                            # Add success indicator
                            cv2.putText(img, "Hand Detected!", (20, 110), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
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
                        cv2.putText(img, "Make sure your hand is well-lit and clearly visible", (20, 140), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Add a visual guide to show where hand should be
                        center_x, center_y = WEBCAM_WIDTH // 2, WEBCAM_HEIGHT // 2
                        cv2.circle(img, (center_x, center_y), 100, (0, 165, 255), 2)
                        cv2.line(img, (center_x - 110, center_y), (center_x - 90, center_y), (0, 165, 255), 2)
                        cv2.line(img, (center_x + 90, center_y), (center_x + 110, center_y), (0, 165, 255), 2)
                        cv2.line(img, (center_x, center_y - 110), (center_x, center_y - 90), (0, 165, 255), 2)
                        cv2.line(img, (center_x, center_y + 90), (center_x, center_y + 110), (0, 165, 255), 2)
                
                # Update game with finger position or last known position
                try:
                    img = self.game.update(img, last_point)
                    
                    # Emit score update
                    self.score_update_signal.emit(self.game.score)
                except Exception as e:
                    print(f"Error updating game: {e}")
            
            # Check if game time is up
            elapsed_time = time.time() - start_time
            remaining_time = max(0, game_duration - int(elapsed_time))
            
            # Add timer to display
            cv2.putText(img, f"Time: {remaining_time}s", (WEBCAM_WIDTH - 150, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if elapsed_time >= game_duration and not self.game.gameOver:
                print("Game over - time's up!")
                self.game.gameOver = True
                self.game_over_signal.emit(self.game.score)
                
                # Update the patient's score in database
                self.update_snake_score(self.patient_id, self.game.score)
                
                # Add game over text to the image
                cv2.putText(img, "GAME OVER!", (WEBCAM_WIDTH//2 - 100, WEBCAM_HEIGHT//2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                cv2.putText(img, f"Final Score: {self.game.score}", (WEBCAM_WIDTH//2 - 100, WEBCAM_HEIGHT//2 + 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            
                # Convert the image to Qt format and emit it
                self.change_pixmap_signal.emit(img)
                
                # Keep showing the final frame for a while
                time.sleep(3)
                break
            
            # Convert the image to Qt format and emit it
            self.change_pixmap_signal.emit(img)
            
            # Increment frame counter
            frame_count += 1
            
            # Slow down the loop slightly to reduce CPU usage
            time.sleep(0.01)
        
        # Release resources
        print("Releasing camera resources...")
        cap.release()
        print("Game thread finished")
    
    def stop(self):
        self.running = False
        self.wait()
    
    def update_snake_score(self, patient_id, score):
        """Update the patient's snake game score in the database"""
        try:
            from db_utils import db
            
            # Update score directly by patient ID
            if db.update_assessment_score(patient_id, "Snake", score):
                print(f"Successfully updated Snake score to {score} for patient ID {patient_id}")
            else:
                print(f"Failed to update Snake score for patient ID {patient_id}")
        except Exception as e:
            print(f"Error updating snake score: {e}")
    
    def ensure_base_frame(self, frame):
        """Make sure the base frame matches the size of the camera frame"""
        if self.base_frame is None or self.base_frame.shape != frame.shape:
            # Create or recreate the base frame with the exact same dimensions as the camera frame
            height, width = frame.shape[:2]
            self.base_frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add a subtle border to the game area
            cv2.rectangle(self.base_frame, (5, 5), (width-5, height-5), 
                         (50, 50, 100), 2)
            
            # Create text label backgrounds with consistent size and position
            # Score area
            cv2.rectangle(self.base_frame, (10, 10), (150, 60), 
                         (40, 40, 40), cv2.FILLED)
            
            # Timer area 
            cv2.rectangle(self.base_frame, (width-160, 10), (width-10, 60), 
                         (40, 40, 40), cv2.FILLED)

class GameUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
        # Initialize video thread as None
        self.video_thread = None
        self.game_started = False
        self.game_completed = False
        
        # Double buffering for smoother display
        self.current_pixmap = None
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self.swap_buffers)
        self.buffer_timer.start(33)  # ~30fps for buffer swapping
    
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
        user_info = QLabel("Assessment Games")
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
        
        # Page title and introduction
        page_title = QLabel("Neuro Rehabilitation Games")
        page_title.setObjectName("title")
        content_layout.addWidget(page_title)
        
        intro_container = QFrame()
        intro_container.setObjectName("dashboard_widget")
        intro_layout = QVBoxLayout(intro_container)
        
        intro_label = QLabel("Select a game to assess different cognitive and motor skills:")
        intro_label.setWordWrap(True)
        intro_layout.addWidget(intro_label)
        
        content_layout.addWidget(intro_container)
        
        # Add patient selection before games grid
        patient_container = QFrame()
        patient_container.setObjectName("dashboard_widget")
        patient_layout = QVBoxLayout(patient_container)
        
        patient_title = QLabel("Patient Selection")
        patient_title.setObjectName("dashboard_title")
        patient_layout.addWidget(patient_title)
        
        patient_form = QFormLayout()
        
        # Add patient dropdown
        self.patient_dropdown = PatientDropdown(self)
        self.patient_dropdown.patient_selected.connect(self.on_patient_selected)
        patient_form.addRow("", self.patient_dropdown)
        
        patient_layout.addLayout(patient_form)
        
        # Add patient container to content layout after intro
        content_layout.addWidget(patient_container)
        
        # Game cards in a modern grid layout
        games_grid = QGridLayout()
        games_grid.setSpacing(20)
        
        # Snake Game Card
        snake_card = QFrame()
        snake_card.setObjectName("dashboard_widget")
        snake_layout = QVBoxLayout(snake_card)
        
        snake_title = QLabel("Snake Game")
        snake_title.setObjectName("dashboard_title")
        snake_layout.addWidget(snake_title)
        
        snake_desc = QLabel("Test hand-eye coordination and fine motor control by using your index finger to control a snake.")
        snake_desc.setWordWrap(True)
        snake_desc.setStyleSheet("margin-bottom: 10px;")
        
        snake_image = QLabel()
        try:
            pixmap = QPixmap("images/snake_game.png")
            snake_image.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            snake_image.setText("[Snake Game Image]")
            snake_image.setStyleSheet("background-color: #ECEFF1; padding: 20px; color: #7F8C8D; border-radius: 4px;")
        
        snake_image.setAlignment(Qt.AlignCenter)
        
        snake_button = QPushButton("Play Snake Game")
        snake_button.setObjectName("primary")
        snake_button.setCursor(Qt.PointingHandCursor)
        snake_button.clicked.connect(self.start_snake_game)
        
        snake_layout.addWidget(snake_image)
        snake_layout.addWidget(snake_desc)
        snake_layout.addWidget(snake_button)
        
        # Emoji Game Card
        emoji_card = QFrame()
        emoji_card.setObjectName("dashboard_widget")
        emoji_layout = QVBoxLayout(emoji_card)
        
        emoji_title = QLabel("Emoji Matching Game")
        emoji_title.setObjectName("dashboard_title")
        emoji_layout.addWidget(emoji_title)
        
        emoji_desc = QLabel("Test memory and visual recognition by matching emojis. A great test for cognitive processing.")
        emoji_desc.setWordWrap(True)
        emoji_desc.setStyleSheet("margin-bottom: 10px;")
        
        emoji_image = QLabel()
        try:
            pixmap = QPixmap("images/emoji_game.png")
            emoji_image.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            emoji_image.setText("[Emoji Game Image]")
            emoji_image.setStyleSheet("background-color: #ECEFF1; padding: 20px; color: #7F8C8D; border-radius: 4px;")
        
        emoji_image.setAlignment(Qt.AlignCenter)
        
        emoji_button = QPushButton("Play Emoji Game")
        emoji_button.setObjectName("primary")
        emoji_button.setCursor(Qt.PointingHandCursor)
        emoji_button.clicked.connect(self.start_emoji_game)
        
        emoji_layout.addWidget(emoji_image)
        emoji_layout.addWidget(emoji_desc)
        emoji_layout.addWidget(emoji_button)
        
        # Ball Game Card
        ball_card = QFrame()
        ball_card.setObjectName("dashboard_widget")
        ball_layout = QVBoxLayout(ball_card)
        
        ball_title = QLabel("Ball Bouncing Game")
        ball_title.setObjectName("dashboard_title")
        ball_layout.addWidget(ball_title)
        
        ball_desc = QLabel("Test bilateral coordination by bouncing a ball between both hands. Great for assessing hand motion range.")
        ball_desc.setWordWrap(True)
        ball_desc.setStyleSheet("margin-bottom: 10px;")
        
        ball_image = QLabel()
        try:
            pixmap = QPixmap("images/ball_game.png")
            ball_image.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            ball_image.setText("[Ball Game Image]")
            ball_image.setStyleSheet("background-color: #ECEFF1; padding: 20px; color: #7F8C8D; border-radius: 4px;")
        
        ball_image.setAlignment(Qt.AlignCenter)
        
        ball_button = QPushButton("Play Ball Game")
        ball_button.setObjectName("primary")
        ball_button.setCursor(Qt.PointingHandCursor)
        ball_button.clicked.connect(self.start_ball_game)
        
        ball_layout.addWidget(ball_image)
        ball_layout.addWidget(ball_desc)
        ball_layout.addWidget(ball_button)
        
        # Speech Assessment Card
        speech_card = QFrame()
        speech_card.setObjectName("dashboard_widget")
        speech_layout = QVBoxLayout(speech_card)
        
        speech_title = QLabel("Speech Assessment")
        speech_title.setObjectName("dashboard_title")
        speech_layout.addWidget(speech_title)
        
        speech_desc = QLabel("Test speech clarity and articulation by reading phrases. Helps assess language and cognitive processing.")
        speech_desc.setWordWrap(True)
        speech_desc.setStyleSheet("margin-bottom: 10px;")
        
        speech_image = QLabel()
        try:
            pixmap = QPixmap("images/speech_game.png")
            speech_image.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            speech_image.setText("[Speech Assessment Image]")
            speech_image.setStyleSheet("background-color: #ECEFF1; padding: 20px; color: #7F8C8D; border-radius: 4px;")
        
        speech_image.setAlignment(Qt.AlignCenter)
        
        speech_button = QPushButton("Start Speech Assessment")
        speech_button.setObjectName("primary")
        speech_button.setCursor(Qt.PointingHandCursor)
        speech_button.clicked.connect(self.start_speech_game)
        
        speech_layout.addWidget(speech_image)
        speech_layout.addWidget(speech_desc)
        speech_layout.addWidget(speech_button)
        
        # Add game cards to grid layout
        games_grid.addWidget(snake_card, 0, 0)
        games_grid.addWidget(emoji_card, 0, 1)
        games_grid.addWidget(ball_card, 1, 0)
        games_grid.addWidget(speech_card, 1, 1)
        
        content_layout.addLayout(games_grid)
        
        # Instructions in a modern card
        instructions_container = QFrame()
        instructions_container.setObjectName("dashboard_widget")
        instructions_layout = QVBoxLayout(instructions_container)
        
        instructions_title = QLabel("Assessment Information")
        instructions_title.setObjectName("dashboard_title")
        instructions_layout.addWidget(instructions_title)
        
        instructions_grid = QGridLayout()
        instructions_grid.setColumnStretch(0, 1)
        instructions_grid.setColumnStretch(1, 1)
        
        instructions = [
            "Each game evaluates different aspects of neurological function, providing valuable assessment data.",
            "Results are automatically saved to the patient's profile for tracking progress over time.",
            "Each game takes approximately 30-60 seconds to complete.",
            "Game difficulty automatically adjusts based on patient performance."
        ]
        
        row = 0
        col = 0
        for instruction in instructions:
            instruction_label = QLabel(f"• {instruction}")
            instruction_label.setWordWrap(True)
            instructions_grid.addWidget(instruction_label, row, col)
            
            # Move to next column or row
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        instructions_layout.addLayout(instructions_grid)
        content_layout.addWidget(instructions_container)
        
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
    
    def on_patient_selected(self, patient_id, patient_name):
        """Handle when a patient is selected from the dropdown"""
        print(f"Patient selected: {patient_name} (ID: {patient_id})")
        # Store the selected patient ID for later use
        self.selected_patient_id = patient_id
        self.selected_patient_name = patient_name
    
    def start_snake_game(self):
        """Start the snake game assessment"""
        # Check if patient is selected
        if not hasattr(self, 'selected_patient_id') or self.selected_patient_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a patient first.")
            return
            
        # Import here to avoid circular imports
        from snake_game_ui import SnakeGameUI
        
        # Stop the buffer timer before switching screens
        if hasattr(self, 'buffer_timer'):
            try:
                self.buffer_timer.stop()
            except Exception as e:
                print(f"Error stopping buffer timer: {e}")
        
        # Create and show snake game window with patient info
        try:
            # Remove any existing snake game instances to prevent UI conflicts
            for i in range(self.parent.stacked_widget.count()):
                widget = self.parent.stacked_widget.widget(i)
                if isinstance(widget, SnakeGameUI):
                    print("Removing existing snake game instance")
                    self.parent.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
                    
            # Create a new snake game instance with patient info
            self.snake_game = SnakeGameUI(
                self.parent, 
                patient_id=self.selected_patient_id, 
                patient_name=self.selected_patient_name
            )
            self.snake_game.navigate_to_signal.connect(self.parent.navigate_to)
            self.parent.stacked_widget.addWidget(self.snake_game)
            self.parent.stacked_widget.setCurrentWidget(self.snake_game)
        except Exception as e:
            print(f"Error starting snake game: {e}")
            QMessageBox.warning(self, "Error", f"Could not start snake game: {str(e)}")
    
    def start_emoji_game(self):
        """Start the emoji matching game"""
        # Check if patient is selected
        if not hasattr(self, 'selected_patient_id') or self.selected_patient_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a patient first.")
            return
            
        # Import here to avoid circular imports
        from emoji_game_ui import EmojiGameUI
        
        # Create and show emoji game window with patient info
        try:
            # Remove any existing emoji game instances
            for i in range(self.parent.stacked_widget.count()):
                widget = self.parent.stacked_widget.widget(i)
                if isinstance(widget, EmojiGameUI):
                    self.parent.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
                    
            # Create a new emoji game instance with patient info
            self.emoji_game = EmojiGameUI(
                self.parent, 
                patient_id=self.selected_patient_id, 
                patient_name=self.selected_patient_name
            )
            self.emoji_game.navigate_to_signal.connect(self.parent.navigate_to)
            self.parent.stacked_widget.addWidget(self.emoji_game)
            self.parent.stacked_widget.setCurrentWidget(self.emoji_game)
        except Exception as e:
            print(f"Error starting emoji game: {e}")
            QMessageBox.warning(self, "Error", f"Could not start emoji game: {str(e)}")
    
    def start_ball_game(self):
        """Start the ball bouncing game"""
        # Check if patient is selected
        if not hasattr(self, 'selected_patient_id') or self.selected_patient_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a patient first.")
            return
            
        # Import here to avoid circular imports
        from ball_game_ui import BallGameUI
        
        # Create and show ball game window with patient info
        try:
            # Remove any existing ball game instances
            for i in range(self.parent.stacked_widget.count()):
                widget = self.parent.stacked_widget.widget(i)
                if isinstance(widget, BallGameUI):
                    self.parent.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
                    
            # Create a new ball game instance with patient info
            self.ball_game = BallGameUI(
                self.parent, 
                patient_id=self.selected_patient_id, 
                patient_name=self.selected_patient_name
            )
            self.ball_game.navigate_to_signal.connect(self.parent.navigate_to)
            self.parent.stacked_widget.addWidget(self.ball_game)
            self.parent.stacked_widget.setCurrentWidget(self.ball_game)
        except Exception as e:
            print(f"Error starting ball game: {e}")
            QMessageBox.warning(self, "Error", f"Could not start ball game: {str(e)}")
    
    def start_speech_game(self):
        """Start the speech assessment game"""
        # Check if patient is selected
        if not hasattr(self, 'selected_patient_id') or self.selected_patient_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a patient first.")
            return
            
        # Import here to avoid circular imports
        from speech_ui import SpeechUI
        
        # Create and show speech game window with patient info
        try:
            # Remove any existing speech UI instances
            for i in range(self.parent.stacked_widget.count()):
                widget = self.parent.stacked_widget.widget(i)
                if isinstance(widget, SpeechUI):
                    self.parent.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
                    
            # Create a new speech UI instance with patient info
            self.speech_game = SpeechUI(
                self.parent, 
                patient_id=self.selected_patient_id, 
                patient_name=self.selected_patient_name
            )
            self.speech_game.navigate_to_signal.connect(self.parent.navigate_to)
            self.parent.stacked_widget.addWidget(self.speech_game)
            self.parent.stacked_widget.setCurrentWidget(self.speech_game)
        except Exception as e:
            print(f"Error starting speech game: {e}")
            QMessageBox.warning(self, "Error", f"Could not start speech assessment: {str(e)}")
    
    def swap_buffers(self):
        """Update the UI with the latest frame from the buffer"""
        if hasattr(self, 'current_pixmap') and self.current_pixmap is not None and not self.current_pixmap.isNull():
            # Find the game display widget in snake game UI if it exists
            if hasattr(self, 'snake_game') and hasattr(self.snake_game, 'game_display'):
                self.snake_game.game_display.setPixmap(self.current_pixmap)
    
    def closeEvent(self, event):
        # Ensure all resources are properly cleaned up
        if hasattr(self, 'buffer_timer') and self.buffer_timer.isActive():
            self.buffer_timer.stop()
        
        # Clean up video thread
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()
            
        # Force garbage collection
        gc.collect()
        
        event.accept() 