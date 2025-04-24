from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QLineEdit, QMessageBox, QFrame, QSizePolicy,
                            QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont, QImage
import cv2
import numpy as np
import pandas as pd
import os
import time
from cvzone.HandTrackingModule import HandDetector

# Constants for webcam
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480

class HandTrackingThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    score_update_signal = pyqtSignal(int)
    test_complete_signal = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.patient_name = ""
        self.score = 0
        self.landmarks_detected = 0
        self.start_time = 0
        self.total_frames = 0
        self.successful_frames = 0
        self.test_duration = 30  # seconds
        
    def run(self):
        # Initialize hand detector
        try:
            print("Initializing hand detector...")
            self.detector = HandDetector(detectionCon=0.8, maxHands=2)
            print("Hand detector initialized successfully")
        except Exception as e:
            print(f"Error initializing hand detector: {e}")
            return
            
        # Setup camera
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
            return
            
        # Initialize variables
        self.start_time = time.time()
        self.running = True
        last_frame_time = time.time()
        target_frame_time = 1.0 / 30  # Target 30 fps
        
        # For smooth display, maintain the last good frame
        last_good_frame = None
        
        # Test goals - landmarks to detect
        target_gestures = [
            {"name": "Open Hand", "description": "Spread all fingers", "completed": False},
            {"name": "Fist", "description": "Close all fingers", "completed": False},
            {"name": "Peace Sign", "description": "Index and middle finger up", "completed": False},
            {"name": "Thumb Up", "description": "Only thumb extended", "completed": False},
            {"name": "Pinch", "description": "Thumb and index finger together", "completed": False}
        ]
        current_gesture_index = 0
        
        print("Starting hand tracking loop...")
        while self.running:
            # Control frame rate for smoother display
            current_time = time.time()
            elapsed_since_last_frame = current_time - last_frame_time
            
            # If we haven't waited long enough for the next frame, sleep
            if elapsed_since_last_frame < target_frame_time:
                time.sleep(target_frame_time - elapsed_since_last_frame)
                continue
                
            # Grab a frame
            success, img = cap.read()
            if not success:
                print("Failed to get frame from camera")
                if last_good_frame is not None:
                    img = last_good_frame.copy()
                else:
                    time.sleep(0.1)
                    continue
            else:
                last_good_frame = img.copy()
                
            last_frame_time = time.time()
                
            # Flip image for natural interaction
            img = cv2.flip(img, 1)
            
            # Detect hands
            hands, img = self.detector.findHands(img, draw=True)
            
            # Update frame counter
            self.total_frames += 1
            
            # Process hands
            if hands:
                # Increment successful frames
                self.successful_frames += 1
                
                # Get landmarks from first hand
                hand = hands[0]
                landmarks = hand["lmList"]
                
                # Add gesture detection based on landmarks
                if landmarks:
                    # Check for current target gesture
                    current_gesture = target_gestures[current_gesture_index]
                    gesture_name = current_gesture["name"]
                    gesture_detected = False
                    
                    # Simple gesture detection logic
                    if gesture_name == "Open Hand" and self.is_open_hand(hand):
                        gesture_detected = True
                    elif gesture_name == "Fist" and self.is_fist(hand):
                        gesture_detected = True
                    elif gesture_name == "Peace Sign" and self.is_peace_sign(hand):
                        gesture_detected = True
                    elif gesture_name == "Thumb Up" and self.is_thumb_up(hand):
                        gesture_detected = True
                    elif gesture_name == "Pinch" and self.is_pinch(hand):
                        gesture_detected = True
                    
                    # If gesture detected, move to next one
                    if gesture_detected and not current_gesture["completed"]:
                        current_gesture["completed"] = True
                        self.score += 20  # Each gesture is worth 20 points
                        self.score_update_signal.emit(self.score)
                        
                        # Move to next gesture if available
                        if current_gesture_index < len(target_gestures) - 1:
                            current_gesture_index += 1
            
            # Display gesture information on frame
            current_gesture = target_gestures[current_gesture_index]
            cv2.putText(img, f"Make this gesture: {current_gesture['name']}", (20, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 128, 255), 2)
            cv2.putText(img, current_gesture['description'], (20, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 128, 255), 2)
                       
            # Display score
            cv2.putText(img, f"Score: {self.score}", (WEBCAM_WIDTH - 150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                       
            # Display time remaining
            elapsed_time = time.time() - self.start_time
            remaining_time = max(0, self.test_duration - int(elapsed_time))
            cv2.putText(img, f"Time: {remaining_time}s", (WEBCAM_WIDTH - 150, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Check if all gestures completed or time's up
            if all(gesture["completed"] for gesture in target_gestures) or elapsed_time >= self.test_duration:
                # Calculate final score
                final_score = self.score
                success_rate = (self.successful_frames / max(1, self.total_frames)) * 100
                
                # Add bonus for high success rate
                if success_rate > 80:
                    bonus = int(10 * (success_rate - 80) / 20)  # Up to 10 points bonus
                    final_score += bonus
                    
                # Show completion message
                cv2.putText(img, "Test Complete!", (WEBCAM_WIDTH//2 - 100, WEBCAM_HEIGHT//2), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                
                # Update the patient's score in CSV
                self.update_hand_score(self.patient_name, final_score)
                
                # Emit complete signal
                self.test_complete_signal.emit(final_score)
                
                # Send the final frame and end
                self.change_pixmap_signal.emit(img)
                time.sleep(2)  # Show final frame for 2 seconds
                break
            
            # Emit the image
            self.change_pixmap_signal.emit(img)
        
        # Release resources
        print("Releasing camera resources...")
        cap.release()
        print("Hand tracking thread finished")
    
    def stop(self):
        self.running = False
        self.wait()
    
    def is_open_hand(self, hand):
        """Detect if hand is open with all fingers extended"""
        fingers = self.detector.fingersUp(hand)
        return sum(fingers) >= 4  # At least 4 fingers up
    
    def is_fist(self, hand):
        """Detect if hand is closed in a fist"""
        fingers = self.detector.fingersUp(hand)
        return sum(fingers) <= 1  # At most 1 finger up (might be thumb)
    
    def is_peace_sign(self, hand):
        """Detect peace sign (index and middle fingers extended)"""
        fingers = self.detector.fingersUp(hand)
        return fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0 and fingers[3] == 0 and fingers[4] == 0
    
    def is_thumb_up(self, hand):
        """Detect thumb up gesture"""
        fingers = self.detector.fingersUp(hand)
        return fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0
    
    def is_pinch(self, hand):
        """Detect pinch gesture (thumb and index finger close together)"""
        landmarks = hand["lmList"]
        if len(landmarks) >= 9:
            # Calculate distance between thumb tip and index tip
            thumb_tip = landmarks[4][:2]  # x,y coordinates of thumb tip
            index_tip = landmarks[8][:2]  # x,y coordinates of index tip
            distance = ((thumb_tip[0] - index_tip[0])**2 + (thumb_tip[1] - index_tip[1])**2)**0.5
            return distance < 40  # Threshold for pinch
        return False
        
    def update_hand_score(self, patient_name, score):
        """Update the hand tracking score in the CSV file"""
        try:
            patients_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "patients_data.csv")
            df = pd.read_csv(patients_data_path)
            # Find patient by name (case-insensitive partial match)
            patient_idx = df[df['name'].str.contains(patient_name, case=False, na=False)].index
            if len(patient_idx) > 0:
                # Update hand score column - since there's no hand score in your CSV,
                # let's use the first available column (Speech Score for example)
                df.loc[patient_idx[0], 'Hand Score'] = score
                df.to_csv(patients_data_path, index=False)
                return True
            return False
        except Exception as e:
            print(f"Error updating hand score: {e}")
            return False

class HandUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tracking_thread = None
        self.init_ui()
    
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
        user_info = QLabel("Hand Tracking Assessment")
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
        
        # Create navigation buttons with modern style
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
            if section["name"] == "Hand":
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
        
        # Setup area
        setup_container = QFrame()
        setup_container.setObjectName("dashboard_widget")
        setup_layout = QVBoxLayout(setup_container)
        
        setup_title = QLabel("Hand Movement Assessment")
        setup_title.setObjectName("dashboard_title")
        setup_layout.addWidget(setup_title)
        
        # Test instructions
        instructions_text = """
        This assessment evaluates your hand motor skills and dexterity.
        
        You will be asked to perform several hand gestures in front of the camera:
        - Open Hand (all fingers extended)
        - Fist (all fingers closed)
        - Peace Sign (index and middle fingers extended)
        - Thumb Up (only thumb extended)
        - Pinch (thumb and index finger touching)
        
        Position your hand clearly in view of the camera and follow the on-screen prompts.
        The assessment will last for 30 seconds.
        """
        
        instructions_label = QLabel(instructions_text)
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("""
            background-color: #ECF0F1;
            padding: 15px;
            border-radius: 5px;
        """)
        setup_layout.addWidget(instructions_label)
        
        # Patient name input
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Enter patient name")
        form_layout.addRow("Patient Name:", self.patient_name_input)
        
        setup_layout.addLayout(form_layout)
        
        # Start button
        self.start_button = QPushButton("Start Assessment")
        self.start_button.setObjectName("success")
        self.start_button.setStyleSheet("""
            background-color: #2ECC71;
            font-size: 12pt;
            padding: 10px;
        """)
        self.start_button.clicked.connect(self.start_test)
        setup_layout.addWidget(self.start_button)
        
        content_layout.addWidget(setup_container)
        
        # Video feed display
        feed_container = QFrame()
        feed_container.setObjectName("dashboard_widget")
        feed_layout = QVBoxLayout(feed_container)
        
        feed_title = QLabel("Camera Feed")
        feed_title.setObjectName("dashboard_title")
        feed_layout.addWidget(feed_title)
        
        # Video display label
        self.video_label = QLabel("Camera feed will appear here when test starts")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            background-color: #2C3E50;
            color: white;
            padding: 20px;
            font-size: 14pt;
            min-height: 480px;
        """)
        feed_layout.addWidget(self.video_label)
        
        # Score display
        score_layout = QHBoxLayout()
        
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2C3E50;
        """)
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("""
            font-size: 14pt;
            color: #3498DB;
        """)
        
        score_layout.addWidget(self.score_label)
        score_layout.addStretch()
        score_layout.addWidget(self.status_label)
        
        feed_layout.addLayout(score_layout)
        
        content_layout.addWidget(feed_container)
        
        # Instructions area
        gesture_container = QFrame()
        gesture_container.setObjectName("dashboard_widget")
        gesture_layout = QVBoxLayout(gesture_container)
        
        gesture_title = QLabel("Hand Gestures Guide")
        gesture_title.setObjectName("dashboard_title")
        gesture_layout.addWidget(gesture_title)
        
        # Gesture descriptions
        gestures_text = """
        <b>Open Hand:</b> Extend all your fingers, spreading them slightly apart.
        
        <b>Fist:</b> Close all fingers into a tight fist.
        
        <b>Peace Sign:</b> Extend only your index and middle fingers while keeping other fingers closed.
        
        <b>Thumb Up:</b> Make a fist but extend only your thumb upward.
        
        <b>Pinch:</b> Touch your thumb and index finger together, forming an 'O' shape.
        """
        
        gestures_label = QLabel(gestures_text)
        gestures_label.setTextFormat(Qt.RichText)
        gestures_label.setWordWrap(True)
        gestures_label.setStyleSheet("""
            background-color: #ECF0F1;
            padding: 15px;
            border-radius: 5px;
            line-height: 1.5;
        """)
        gesture_layout.addWidget(gestures_label)
        
        content_layout.addWidget(gesture_container)
        
        # Set scroll area widget
        scroll_area.setWidget(content_container)
        
        # Add all major containers to the main layout
        main_layout.addWidget(header_container)
        main_layout.addWidget(navbar)
        main_layout.addWidget(scroll_area, 1)  # Give it a stretch factor
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def start_test(self):
        # Get patient name
        patient_name = self.patient_name_input.text().strip()
        
        # Validate input
        if not patient_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a patient name.")
            return
        
        # Check if test is already running
        if self.tracking_thread and self.tracking_thread.isRunning():
            # Confirm if user wants to restart
            reply = QMessageBox.question(self, "Restart Test", 
                                       "A test is already in progress. Do you want to restart?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            else:
                # Stop current test
                self.tracking_thread.stop()
        
        # Update UI state
        self.tracking_thread = HandTrackingThread()
        self.tracking_thread.patient_name = patient_name
        
        # Connect signals
        self.tracking_thread.change_pixmap_signal.connect(self.update_image)
        self.tracking_thread.score_update_signal.connect(self.update_score)
        self.tracking_thread.test_complete_signal.connect(self.test_complete)
        
        # Start thread
        self.tracking_thread.start()
    
    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.video_label.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
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
    def test_complete(self, final_score):
        """Handle test completion"""
        self.status_label.setText("Status: Test completed")
        self.start_button.setEnabled(True)
        
        # Show test complete message
        QMessageBox.information(self, "Test Complete", 
                             f"Hand tracking test completed!\nFinal score: {final_score}")
        
        # Clean up video thread
        if self.tracking_thread:
            self.tracking_thread.stop()
            self.tracking_thread = None
    
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            # Clean up before navigating
            if self.tracking_thread and self.tracking_thread.isRunning():
                self.tracking_thread.stop()
            
            self.navigate_to_signal.emit(section)
        return handler
        
    def closeEvent(self, event):
        # Clean up resources
        if self.tracking_thread and self.tracking_thread.isRunning():
            self.tracking_thread.stop()
            
        event.accept() 