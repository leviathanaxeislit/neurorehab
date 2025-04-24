import math
import random
import cv2
import numpy as np
import pandas as pd
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QMessageBox, QLineEdit, QApplication, 
                            QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont, QImage
from cvzone.HandTrackingModule import HandDetector
import cvzone
import os
from db_utils import db

# Higher resolution for better visibility
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
PROCESS_EVERY_N_FRAME = 3  # Only process every 3rd frame

class BallGameThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    score_update_signal = pyqtSignal(list)
    game_over_signal = pyqtSignal(int)  # Signal to send final score when game is over
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.detector = None
        self.patient_name = ""
        # Start the ball in the center of the screen with integer coordinates
        self.ball_pos = [int(WEBCAM_WIDTH // 2), int(WEBCAM_HEIGHT // 2)]
        self.speed_x = 7  # Reduce initial speed for easier gameplay
        self.speed_y = 7
        self.score = [0, 0]
        self.game_over = False
        self.images = {}
        
    def load_game_images(self):
        """Load game images like ball, background, bats"""
        # Define image paths
        image_paths = {
            "background": "images/Background.jpg",
            "game_over": "images/game_over.jpg",
            "ball": "images/ball.png",
            "left_bat": "images/left_bat.png",
            "right_bat": "images/right_bat.png"
        }
        
        images = {}
        for name, path in image_paths.items():
            try:
                if os.path.exists(path):
                    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                    if image is None:
                        # Create a simple fallback image
                        if name == "ball":
                            image = np.zeros((20, 20, 4), dtype=np.uint8)
                            cv2.circle(image, (10, 10), 10, (0, 0, 255, 255), -1)
                        elif name in ["left_bat", "right_bat"]:
                            image = np.zeros((80, 20, 4), dtype=np.uint8)
                            cv2.rectangle(image, (0, 0), (20, 80), (0, 255, 0, 255), -1)
                        else:
                            image = np.zeros((WEBCAM_HEIGHT, WEBCAM_WIDTH, 3), dtype=np.uint8)
                            cv2.putText(image, name, (WEBCAM_WIDTH//3, WEBCAM_HEIGHT//2), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    else:
                        # Optimize images by resizing
                        if name == "ball":
                            # Ensure ball is BGRA
                            if image.shape[2] == 3:
                                # Add alpha channel
                                alpha_channel = np.ones((image.shape[0], image.shape[1], 1), dtype=image.dtype) * 255
                                image = np.concatenate((image, alpha_channel), axis=2)
                            # Now resize
                            image = cv2.resize(image, (20, 20))  # Smaller ball
                        elif name in ["left_bat", "right_bat"]:
                            # Ensure bats are BGRA
                            if image.shape[2] == 3:
                                alpha_channel = np.ones((image.shape[0], image.shape[1], 1), dtype=image.dtype) * 255
                                image = np.concatenate((image, alpha_channel), axis=2)
                            image = cv2.resize(image, (20, 80))  # Smaller bats
                        elif name in ["background", "game_over"]:
                            image = cv2.resize(image, (WEBCAM_WIDTH, WEBCAM_HEIGHT))  # Match webcam resolution
                            
                            # Make sure these are BGR (no alpha)
                            if image.shape[2] == 4:
                                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                    
                    images[name] = image
                else:
                    # Create a simple fallback image
                    if name == "ball":
                        image = np.zeros((20, 20, 4), dtype=np.uint8)
                        cv2.circle(image, (10, 10), 10, (0, 0, 255, 255), -1)
                    elif name in ["left_bat", "right_bat"]:
                        image = np.zeros((80, 20, 4), dtype=np.uint8)
                        cv2.rectangle(image, (0, 0), (20, 80), (0, 255, 0, 255), -1)
                    else:
                        image = np.zeros((WEBCAM_HEIGHT, WEBCAM_WIDTH, 3), dtype=np.uint8)
                        cv2.putText(image, name, (WEBCAM_WIDTH//3, WEBCAM_HEIGHT//2), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    images[name] = image
            except Exception as e:
                print(f"Error loading image {name}: {e}")
                # Create a simple fallback image
                if name == "ball":
                    image = np.zeros((20, 20, 4), dtype=np.uint8)
                    cv2.circle(image, (10, 10), 10, (0, 0, 255, 255), -1)
                elif name in ["left_bat", "right_bat"]:
                    image = np.zeros((80, 20, 4), dtype=np.uint8)
                    cv2.rectangle(image, (0, 0), (20, 80), (0, 255, 0, 255), -1)
                else:
                    image = np.zeros((WEBCAM_HEIGHT, WEBCAM_WIDTH, 3), dtype=np.uint8)
                    cv2.putText(image, name, (WEBCAM_WIDTH//3, WEBCAM_HEIGHT//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                images[name] = image
                
        # Debug information
        for name, img in images.items():
            print(f"Image {name} loaded with shape: {img.shape}")
            
        return images
    
    def run(self):
        # Initialize detector with improved settings for accuracy
        try:
            print("Initializing hand detector...")
            # Lower detection confidence threshold for better detection in varied conditions
            self.detector = HandDetector(detectionCon=0.5, maxHands=2)
            print("Hand detector initialized successfully")
        except Exception as e:
            print(f"Error initializing hand detector: {e}")
            return
        
        # Make sure images directory exists
        try:
            if not os.path.exists("images"):
                os.makedirs("images")
                print("Created images directory")
        except Exception as e:
            print(f"Error creating images directory: {e}")
        
        # Load game images
        try:
            print("Loading game images...")
            self.images = self.load_game_images()
            print("Game images loaded successfully")
        except Exception as e:
            print(f"Error loading game images: {e}")
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
        game_duration = 60  # Extended to 60 seconds for better gameplay
        last_frame_time = time.time()  # Track when we last processed a frame
        target_frame_time = 1.0 / 30  # Target 30 fps (33ms per frame)
        
        # For smooth display, maintain the last good frame
        last_good_frame = None
        
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
                
            # Flip image for natural interaction
            img = cv2.flip(img, 1)
            
            # Apply brightness and contrast enhancement to improve hand detection
            try:
                # Increase brightness and contrast slightly
                alpha = 1.2  # Contrast control (1.0-3.0)
                beta = 10    # Brightness control (0-100)
                img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
            except Exception as e:
                print(f"Error enhancing image: {e}")
            
            # Only process every Nth frame to improve performance
            frame_count += 1
            process_hands = (frame_count % PROCESS_EVERY_N_FRAME == 0)
            
            # Update game state - ignore the game_over return value as we're using timer now
            img, self.ball_pos, self.speed_x, self.speed_y, self.score, _ = self.update_game(
                img, process_hands)
            
            # Emit score update (but not too frequently to avoid GUI thread overload)
            if frame_count % 5 == 0:
                self.score_update_signal.emit(self.score)
            
            # Check if game time is up
            elapsed_time = time.time() - start_time
            remaining_time = max(0, game_duration - int(elapsed_time))
            
            # Add timer to display
            cv2.putText(img, f"Time: {remaining_time}s", (WEBCAM_WIDTH - 150, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if elapsed_time >= game_duration:
                print("Game over - time's up!")
                # Show game over message on the last frame
                try:
                    if "game_over" in self.images:
                        img = self.images["game_over"].copy()
                    
                    # Add final score overlay
                    final_score = self.score[0] + self.score[1]
                    cv2.putText(img, "GAME OVER!", (WEBCAM_WIDTH//2 - 80, WEBCAM_HEIGHT//2 - 40), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(img, f"Final Score: {final_score}", 
                               (WEBCAM_WIDTH//2 - 80, WEBCAM_HEIGHT//2), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    
                    # Send the final image
                    self.change_pixmap_signal.emit(img)
                    
                    # Update the patient's score in database
                    self.update_ball_score(self.patient_name, final_score)
                    
                    # Signal game over
                    self.game_over_signal.emit(final_score)
                except Exception as e:
                    print(f"Error displaying game over: {e}")
                
                # Keep showing the final frame for a while
                time.sleep(3)
                break
            
            # Convert the image to Qt format and emit it
            self.change_pixmap_signal.emit(img)
        
        # Release resources
        print("Releasing camera resources...")
        cap.release()
        print("Game thread finished")
    
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
                         (50, 50, 100), 2)
            
            # Create text label backgrounds with consistent size and position
            # Score area
            cv2.rectangle(self.base_frame, (10, height-40), (width-10, height-10), 
                         (40, 40, 40), cv2.FILLED)
            
            # Timer area 
            cv2.rectangle(self.base_frame, (width-160, 10), (width-10, 40), 
                         (40, 40, 40), cv2.FILLED)
            
    def update_game(self, frame, process_hands=True):
        """Update game state and draw game elements"""
        # Ensure we have a valid frame
        if frame is None:
            return frame, self.ball_pos, self.speed_x, self.speed_y, self.score, True
        
        # Process Qt events to keep UI responsive
        QApplication.processEvents()
        
        # Ensure the base frame matches the camera frame dimensions
        self.ensure_base_frame(frame)
        
        # Create a fresh frame by blending with the base frame for consistent UI
        try:
            game_frame = frame.copy()
            overlay_alpha = 0.2  # Subtle overlay
            cv2.addWeighted(self.base_frame, overlay_alpha, game_frame, 1 - overlay_alpha, 0, game_frame)
            frame = game_frame
        except Exception as e:
            print(f"Error applying overlay: {e}")
            # Continue with original frame if blending fails
        
        # Blend with background if available
        try:
            if "background" in self.images:
                # Ensure background image has same dimensions as frame
                bg_img = self.images["background"]
                if bg_img.shape[:2] != frame.shape[:2] or bg_img.shape[2] != frame.shape[2]:
                    bg_img = cv2.resize(bg_img, (frame.shape[1], frame.shape[0]))
                    # Ensure same number of channels
                    if bg_img.shape[2] != frame.shape[2]:
                        if bg_img.shape[2] == 4:
                            bg_img = cv2.cvtColor(bg_img, cv2.COLOR_BGRA2BGR)
                        elif bg_img.shape[2] == 3 and frame.shape[2] == 4:
                            alpha_channel = np.ones((bg_img.shape[0], bg_img.shape[1], 1), dtype=bg_img.dtype) * 255
                            bg_img = np.concatenate((bg_img, alpha_channel), axis=2)
                    # Store resized version for future use
                    self.images["background"] = bg_img
                frame = cv2.addWeighted(frame, 0.5, bg_img, 0.5, 0)
        except Exception as e:
            print(f"Error blending background: {e}")
        
        # Process hands
        hands = []
        if process_hands:
            try:
                hands, frame = self.detector.findHands(frame, flipType=False, draw=True)
                
                # Draw more visible hand landmarks for better feedback
                if hands:
                    for hand in hands:
                        # Draw a circle at the index finger tip for better visual feedback
                        if 'lmList' in hand and len(hand['lmList']) > 8:
                            index_finger_tip = hand['lmList'][8][:2]
                            cv2.circle(frame, tuple(index_finger_tip), 15, (0, 255, 0), cv2.FILLED)
                            cv2.circle(frame, tuple(index_finger_tip), 18, (255, 255, 255), 2)
                            
                            # Add hand type indicator
                            hand_type = hand['type']
                            cv2.putText(frame, f"{hand_type} hand", 
                                       (index_finger_tip[0] - 20, index_finger_tip[1] - 20), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                else:
                    # Show guidance when no hands are detected
                    cv2.putText(frame, "No hands detected - Show both hands to camera", 
                              (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, "Make sure hands are well-lit and clearly visible", 
                              (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Draw guides for hand positioning
                    left_x, right_x = 80, WEBCAM_WIDTH - 80
                    center_y = WEBCAM_HEIGHT // 2
                    
                    # Left hand guide
                    cv2.circle(frame, (left_x, center_y), 70, (0, 165, 255), 2)
                    cv2.putText(frame, "Left Hand", (left_x - 40, center_y - 80),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    
                    # Right hand guide
                    cv2.circle(frame, (right_x, center_y), 70, (0, 165, 255), 2)
                    cv2.putText(frame, "Right Hand", (right_x - 40, center_y - 80),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            except Exception as e:
                print(f"Error finding hands: {e}")
                cv2.putText(frame, "Hand detection error - trying to recover", 
                          (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Handle hand detection and bat positioning
        if hands:
            for hand in hands:
                try:
                    x, y, w, h = hand['bbox']
                    h1, w1, _ = self.images["left_bat"].shape
                    
                    # Calculate center of hand for more intuitive paddle positioning
                    if 'center' in hand:
                        hand_center = hand['center']
                        y = hand_center[1]
                    
                    # Set paddle position with the hand center
                    y1 = y - h1 // 2
                    y1 = np.clip(y1, 20, WEBCAM_HEIGHT - h1 - 20)

                    if hand['type'] == "Left":
                        try:
                            left_bat = self.images["left_bat"]
                            # Check dimensions before overlay
                            if y1 + left_bat.shape[0] <= frame.shape[0]:
                                frame = cvzone.overlayPNG(frame, left_bat, (20, y1))
                            else:
                                # Draw a simple rectangle as fallback
                                cv2.rectangle(frame, (20, y1), (20 + 20, y1 + 80), (0, 255, 0), -1)
                        except Exception as e:
                            print(f"Error drawing left bat: {e}")
                            # Fallback to simple rectangle
                            cv2.rectangle(frame, (20, y1), (20 + 20, y1 + 80), (0, 255, 0), -1)
                            
                        # Handle collision - increased hit zone for better gameplay
                        # Expanded paddle hit zone by 10 pixels in each direction
                        paddle_left = 15  # Slightly before the visible paddle
                        paddle_right = 20 + w1 + 10  # Slightly after the visible paddle
                        paddle_top = y1 - 10  # Slightly above the visible paddle
                        paddle_bottom = y1 + h1 + 10  # Slightly below the visible paddle
                        
                        if paddle_left < self.ball_pos[0] < paddle_right and paddle_top < self.ball_pos[1] < paddle_bottom:
                            if self.speed_x < 0:  # Only bounce if ball is moving toward the paddle
                                self.speed_x = -self.speed_x
                                # Add slight random vertical variation for more interesting gameplay
                                self.speed_y += random.uniform(-1, 1)
                                # Make sure vertical speed doesn't get too extreme
                                self.speed_y = np.clip(self.speed_y, -10, 10)
                                
                                self.ball_pos[0] += 20
                                self.score[0] += 1

                    if hand['type'] == "Right":
                        try:
                            right_bat = self.images["right_bat"]
                            # Check dimensions before overlay
                            if y1 + right_bat.shape[0] <= frame.shape[0]:
                                frame = cvzone.overlayPNG(frame, right_bat, (WEBCAM_WIDTH - 40, y1))
                            else:
                                # Draw a simple rectangle as fallback
                                cv2.rectangle(frame, (WEBCAM_WIDTH - 40, y1), (WEBCAM_WIDTH - 40 + 20, y1 + 80), (0, 255, 0), -1)
                        except Exception as e:
                            print(f"Error drawing right bat: {e}")
                            # Fallback to simple rectangle
                            cv2.rectangle(frame, (WEBCAM_WIDTH - 40, y1), (WEBCAM_WIDTH - 40 + 20, y1 + 80), (0, 255, 0), -1)
                            
                        # Handle collision - increased hit zone for better gameplay
                        # Expanded paddle hit zone by 10 pixels in each direction
                        paddle_left = WEBCAM_WIDTH - 40 - 30 - 10  # Slightly before the visible paddle 
                        paddle_right = WEBCAM_WIDTH - 40 + 10  # Slightly after the visible paddle
                        paddle_top = y1 - 10  # Slightly above the visible paddle
                        paddle_bottom = y1 + h1 + 10  # Slightly below the visible paddle
                        
                        if paddle_left < self.ball_pos[0] < paddle_right and paddle_top < self.ball_pos[1] < paddle_bottom:
                            if self.speed_x > 0:  # Only bounce if ball is moving toward the paddle
                                self.speed_x = -self.speed_x
                                # Add slight random vertical variation for more interesting gameplay
                                self.speed_y += random.uniform(-1, 1)
                                # Make sure vertical speed doesn't get too extreme
                                self.speed_y = np.clip(self.speed_y, -10, 10)
                                
                                self.ball_pos[0] -= 20
                                self.score[1] += 1
                except Exception as e:
                    print(f"Error handling bat: {e}")
        
        # Move the Ball
        if self.ball_pos[1] >= WEBCAM_HEIGHT - 40 or self.ball_pos[1] <= 20:
            self.speed_y = -self.speed_y

        # Update ball position and ensure they stay as integers
        self.ball_pos[0] += self.speed_x
        self.ball_pos[1] += self.speed_y
        
        # Make sure ball position values are integers
        self.ball_pos[0] = int(self.ball_pos[0])
        self.ball_pos[1] = int(self.ball_pos[1])
        
        # Keep ball within horizontal boundaries (bounce off sides if no paddle)
        if self.ball_pos[0] < 40:
            self.ball_pos[0] = 40
            self.speed_x = abs(self.speed_x)  # Reverse direction
        elif self.ball_pos[0] > WEBCAM_WIDTH - 40:
            self.ball_pos[0] = WEBCAM_WIDTH - 40
            self.speed_x = -abs(self.speed_x)  # Reverse direction

        # Draw the ball
        try:
            if "ball" in self.images:
                ball_img = self.images["ball"]
                x_pos = int(self.ball_pos[0] - ball_img.shape[1] // 2)
                y_pos = int(self.ball_pos[1] - ball_img.shape[0] // 2)
                
                # Make sure ball stays within frame boundaries
                x_pos = max(0, min(x_pos, frame.shape[1] - ball_img.shape[1]))
                y_pos = max(0, min(y_pos, frame.shape[0] - ball_img.shape[0]))
                
                # Draw a solid circle as fallback in case overlay fails
                ball_center = (int(self.ball_pos[0]), int(self.ball_pos[1]))
                cv2.circle(frame, ball_center, 8, (0, 0, 255), -1)
                
                # Try overlay if we have a valid position
                if x_pos >= 0 and y_pos >= 0 and x_pos + ball_img.shape[1] <= frame.shape[1] and y_pos + ball_img.shape[0] <= frame.shape[0]:
                    try:
                        # Make sure ball image has alpha channel
                        if ball_img.shape[2] == 3:
                            alpha_channel = np.ones((ball_img.shape[0], ball_img.shape[1], 1), dtype=ball_img.dtype) * 255
                            ball_img_with_alpha = np.concatenate((ball_img, alpha_channel), axis=2)
                            frame = cvzone.overlayPNG(frame, ball_img_with_alpha, (x_pos, y_pos))
                        else:
                            frame = cvzone.overlayPNG(frame, ball_img, (x_pos, y_pos))
                    except Exception as e:
                        print(f"Falling back to circle for ball: {e}")
                        # Circle already drawn above as fallback
            else:
                ball_center = (int(self.ball_pos[0]), int(self.ball_pos[1]))
                cv2.circle(frame, ball_center, 8, (0, 0, 255), -1)
        except Exception as e:
            print(f"Error drawing ball: {e}")
            # Last resort fallback - using direct integer coordinates
            try:
                ball_center = (int(self.ball_pos[0]), int(self.ball_pos[1]))
                cv2.circle(frame, ball_center, 8, (0, 0, 255), -1)
            except Exception as e2:
                print(f"Critical error drawing ball: {e2}")
                # If we can't even draw a circle, just continue without drawing

        # Display scores - use consistent positioning and font size
        score_text = f"Left: {self.score[0]}  Right: {self.score[1]}"
        text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_COMPLEX, 0.7, 1)[0]
        text_x = (WEBCAM_WIDTH - text_size[0]) // 2  # Center text
        cv2.putText(frame, score_text, (text_x, WEBCAM_HEIGHT-20), 
                   cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 1)
        
        # The game is now purely time-based, returning False for game_over
        return frame, self.ball_pos, self.speed_x, self.speed_y, self.score, False
    
    def stop(self):
        self.running = False
        self.wait()
    
    def update_ball_score(self, patient_name, score):
        """Update the ball score in the database"""
        try:
            print(f"Updating ball score for {patient_name} to {score}")
            # Find patient by name in the database
            patient_df = db.get_patient_by_name(patient_name)
            
            if not patient_df.empty:
                # Get the first matching patient's ID
                patient_id = patient_df.iloc[0]['id']
                print(f"Found patient ID: {patient_id}")
                
                # Update the score in the database
                db.update_assessment_score(patient_id, "ball", score)
                print(f"Successfully updated ball score to {score} for patient ID {patient_id}")
                return True
            else:
                print(f"Error: No patient found with name {patient_name}")
                return False
        except Exception as e:
            print(f"Error updating ball score: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

class BallGameUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize game state variables first before UI
        self.game_started = False
        self.game_completed = False
        self.video_thread = None
        self.start_button = None  # Will be set in init_ui
        self.next_frame = None
        
        # Now initialize the UI
        self.parent = parent
        self.init_ui()
        
        # Add buffer for smoother rendering
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self.swap_buffers)
        self.buffer_timer.start(33)  # ~30fps
        
        # Verify that the button was created
        if self.start_button is None:
            print("WARNING: start_button was not initialized in init_ui")
    
    def init_ui(self):
        # Debug print to track initialization
        print("Initializing BallGameUI interface...")
        
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
        user_info = QLabel("Ball Game Assessment")
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
        
        setup_title = QLabel("Ball Game Setup")
        setup_title.setObjectName("dashboard_title")
        setup_layout.addWidget(setup_title)
        
        # Form for patient name
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Enter patient name")
        form_layout.addRow("Patient Name:", self.patient_name_input)
        
        setup_layout.addLayout(form_layout)
        
        # Initialization of start button
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
        
        # Game display area with better size
        display_container = QFrame()
        display_container.setObjectName("dashboard_widget")
        display_layout = QVBoxLayout(display_container)
        
        display_title = QLabel("Game Display")
        display_title.setObjectName("dashboard_title")
        display_layout.addWidget(display_title)
        
        # Status display for UI
        self.status_label = QLabel("Status: Ready to start")
        self.status_label.setStyleSheet("""
            color: #3498DB;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        display_layout.addWidget(self.status_label)
        
        # Score display
        self.score_label = QLabel("Score: Left 0 - 0 Right")
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
        instructions_label = QLabel("Use your hands to bounce the ball back and forth. Each time you successfully bounce the ball, you gain a point.")
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
        print(f"Start game called. Button state: {self.start_button}")
        
        # Get patient name
        patient_name = self.patient_name_input.text().strip()
        
        # Validate input
        if not patient_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a patient name.")
            return
        
        # More debug info
        print(f"Patient name: {patient_name}")
        print(f"Game started: {self.game_started}, Game completed: {self.game_completed}")
        
        # Check if game is already running
        if self.game_started and not self.game_completed:
            # Confirm if user wants to restart
            reply = QMessageBox.question(self, "Restart Game", 
                                       "A game is already in progress. Do you want to restart?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            else:
                # Stop current game
                if self.video_thread:
                    self.video_thread.stop()
        
        # Update UI state
        self.game_started = True
        self.game_completed = False
        self.score_label.setText("Score: Left 0 - 0 Right")
        self.status_label.setText("Status: Game in progress")
        
        try:
            # Try to disable the start button
            if self.start_button:
                print(f"Disabling start button: {self.start_button}")
                self.start_button.setEnabled(False)
            else:
                print("Warning: start_button is None")
        except Exception as e:
            print(f"Error disabling start button: {e}")
            # Create a new button if needed (fallback)
            try:
                print("Attempting to recreate start button")
                self.start_button = QPushButton("Start Game")
                self.start_button.clicked.connect(self.start_game)
                # We can't add it to the layout here as it would mess up the UI
            except Exception as e2:
                print(f"Failed to recreate button: {e2}")
        
        # Start video thread
        self.video_thread = BallGameThread()
        self.video_thread.patient_name = patient_name
        
        # Connect signals
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.score_update_signal.connect(self.update_score)
        self.video_thread.game_over_signal.connect(self.game_over)
        
        # Start thread
        self.video_thread.start()
    
    def swap_buffers(self):
        """Swap the front and back buffers to update the display"""
        if hasattr(self, 'next_frame') and self.next_frame is not None and not self.next_frame.isNull():
            self.game_display.setPixmap(self.next_frame)
            # Process events to keep UI responsive
            QApplication.processEvents()
    
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
    
    @pyqtSlot(list)
    def update_score(self, score):
        """Update the score display"""
        self.score_label.setText(f"Score: Left {score[0]} - {score[1]} Right")
    
    @pyqtSlot(int)
    def game_over(self, final_score):
        """Handle game over event"""
        print(f"BallGameUI - Game over called with score: {final_score}")
        
        self.game_completed = True
        self.score_label.setText(f"Score: Final - {final_score}")
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
        
        # Update the patient's score in the database
        try:
            patient_name = self.patient_name_input.text().strip()
            print(f"Updating patient score for {patient_name} with score {final_score}")
            if self.video_thread:
                success = self.video_thread.update_ball_score(patient_name, final_score)
                print(f"Score update {'successful' if success else 'failed'}")
            else:
                print("Error: Video thread is None when trying to update score")
        except Exception as e:
            print(f"Error updating patient score: {str(e)}")
            import traceback
            traceback.print_exc()
        
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
        import gc
        gc.collect()
        
        event.accept() 