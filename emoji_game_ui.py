import random
import pandas as pd
import time
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QGridLayout, QMessageBox, QLineEdit,
                            QFrame, QScrollArea, QSizePolicy, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont

class EmojiGameUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize game state variables first before UI
        self.emoji_bank = []
        self.target_emoji = ""
        self.emoji_buttons = {}
        self.expired_cells = []
        self.score = 0
        self.game_started = False
        self.game_completed = False
        self.patient_name = ""
        self.difficulty = "Easy"
        self.total_cells = 6  # 6x6 grid
        self.refresh_timer = None
        self.start_button = None
        
        # Now initialize the UI
        self.parent = parent
        self.init_ui()
        self.init_emoji_bank()
        
        # Verify that the button was created
        if self.start_button is None:
            print("WARNING: start_button was not initialized in init_ui")
    
    def init_emoji_bank(self):
        """Initialize the bank of emojis to use in the game"""
        # Animals
        animals = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', 
                  '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🦆', '🦉', '🐺', '🐗', '🐴', 
                  '🦄', '🐝', '🐛', '🦋', '🐞', '🐢', '🐍', '🦎', '🐙', '🐬', '🐳', 
                  '🐊', '🐆', '🦓', '🐘', '🦒', '🐄', '🐎', '🐖', '🐏', '🐐']
        # Vehicles
        vehicles = ['🚗', '🚕', '🚙', '🚌', '🚑', '🚒', '🚚', '🚜', '🚲', '🛵', 
                   '🚔', '🚘', '✈️', '🛫', '🚀', '🚁', '⛵️', '🚤', '🚢']
        # Foods
        foods = ['🍏', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', 
                '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🥑', '🥦', '🥬', '🥒', '🌶️', 
                '🌽', '🥕', '🧄', '🧅', '🥔', '🍞', '🥐', '🥨', '🧀', '🍗', '🍖', 
                '🥩', '🍤', '🍔', '🍟', '🍕', '🥪', '🍦', '🍩', '🍰', '🧁', '🥧']
        
        # Use different sets based on difficulty
        if self.difficulty == "Easy":
            self.emoji_bank = foods
        elif self.difficulty == "Medium":
            self.emoji_bank = animals
        else:  # Hard
            self.emoji_bank = animals + vehicles
    
    def init_ui(self):
        # Debug print to track initialization
        print("Initializing EmojiGameUI interface...")
        
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
        user_info = QLabel("Emoji Game Assessment")
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
        
        setup_title = QLabel("Emoji Game Setup")
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
        
        # Target emoji display
        target_container = QFrame()
        target_container.setObjectName("dashboard_widget")
        target_layout = QVBoxLayout(target_container)
        
        target_title = QLabel("Find this emoji")
        target_title.setObjectName("dashboard_title")
        target_layout.addWidget(target_title)
        
        self.target_label = QLabel("🎮")
        self.target_label.setFont(QFont("Arial", 100))
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setStyleSheet("""
            background-color: #3498DB;
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px;
        """)
        target_layout.addWidget(self.target_label)
        
        target_container.setVisible(False)
        content_layout.addWidget(target_container)
        self.target_container = target_container
        
        # Game board area
        game_board_container = QFrame()
        game_board_container.setObjectName("dashboard_widget")
        game_board_layout = QVBoxLayout(game_board_container)
        
        board_title = QLabel("Game Board")
        board_title.setObjectName("dashboard_title")
        game_board_layout.addWidget(board_title)
        
        # Status display for UI
        self.status_label = QLabel("Status: Ready to start")
        self.status_label.setStyleSheet("""
            color: #3498DB;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        game_board_layout.addWidget(self.status_label)
        
        # Score display
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2ECC71;
            margin-bottom: 10px;
        """)
        game_board_layout.addWidget(self.score_label)
        
        # Actual game board grid
        self.board_layout = QGridLayout()
        self.board_layout.setSpacing(10)
        grid_container = QFrame()
        grid_container.setLayout(self.board_layout)
        grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        game_board_layout.addWidget(grid_container)
        
        # Add instructions
        instructions_label = QLabel("Click on the emojis that match the target emoji above. The board will refresh periodically.")
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("color: #7F8C8D; margin-top: 10px;")
        game_board_layout.addWidget(instructions_label)
        
        game_board_container.setVisible(False)
        content_layout.addWidget(game_board_container)
        self.game_board_container = game_board_container
        
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
        """Start a new game"""
        # Get patient name
        self.patient_name = self.patient_name_input.text().strip()
        
        # Validate input
        if not self.patient_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a patient name.")
            return
        
        print(f"Starting emoji game for patient: {self.patient_name}")
        
        # Check if game is already running
        if self.game_started and not self.game_completed:
            # Confirm if user wants to restart
            reply = QMessageBox.question(self, "Restart Game", 
                                        "A game is already in progress. Do you want to restart?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Update UI state
        self.game_started = True
        self.game_completed = False
        self.score = 0
        self.score_label.setText(f"Score: {self.score}")
        self.status_label.setText("Status: Game in progress")
        
        # Disable start button
        try:
            self.start_button.setEnabled(False)
        except Exception as e:
            print(f"Error disabling start button: {e}")
        
        # Setup game board
        self.setup_game_board()
        
        # Setup refresh timer for periodic board updates
        self.setup_refresh_timer()
    
    def setup_game_board(self):
        """Setup the game board with emojis"""
        # Choose a random emoji for the target
        self.target_emoji = random.choice(self.emoji_bank)
        self.target_label.setText(self.target_emoji)
        
        # Make sure target emoji appears at least once on the board
        target_placed = False
        
        # Create the grid of emoji buttons
        for row in range(self.total_cells):
            for col in range(self.total_cells):
                cell_id = row * self.total_cells + col + 1
                
                # Create button
                button = QPushButton()
                button.setMinimumSize(60, 60)
                button.setFont(QFont("Arial", 24))
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #ECF0F1;
                        border: 2px solid #BDC3C7;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #D6DBDF;
                    }
                    QPushButton:pressed {
                        background-color: #3498DB;
                        color: white;
                    }
                """)
                
                # Decide if this should be the target emoji
                if not target_placed and random.random() < 0.1:  # 10% chance
                    emoji = self.target_emoji
                    target_placed = True
                else:
                    emoji = random.choice(self.emoji_bank)
                
                button.setText(emoji)
                
                # Use a lambda that captures the current value of cell_id
                button.clicked.connect(lambda checked, id=cell_id: self.on_emoji_clicked(id))
                
                # Store button reference and emoji
                self.emoji_buttons[cell_id] = {
                    "button": button,
                    "emoji": emoji,
                    "clicked": False,
                    "correct": emoji == self.target_emoji
                }
                
                # Add to layout
                self.board_layout.addWidget(button, row, col)
        
        # If we haven't placed the target emoji yet, replace a random cell
        if not target_placed:
            # Choose a random cell to replace
            cell_id = random.randint(1, self.total_cells * self.total_cells)
            button = self.emoji_buttons[cell_id]["button"]
            button.setText(self.target_emoji)
            
            # Update the cell data
            self.emoji_buttons[cell_id]["emoji"] = self.target_emoji
            self.emoji_buttons[cell_id]["correct"] = True
    
    def setup_refresh_timer(self):
        """Setup the timer to refresh the board periodically"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            
        # Create a new timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_board)
        
        # Start timer - refresh every 10 seconds
        refresh_interval = 10000  # 10 seconds
        self.refresh_timer.start(refresh_interval)
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def refresh_board(self):
        """Refresh the game board with new emojis"""
        if not self.game_started or self.game_completed:
            return
            
        print("Refreshing game board")
        
        # Replace all emojis that haven't been clicked
        target_placed = False
        
        # Keep track of new target positions
        target_positions = []
        
        for cell_id, cell_data in self.emoji_buttons.items():
            # Skip clicked cells
            if cell_data["clicked"]:
                continue
                
            # Get button reference
            button = cell_data["button"]
            
            # Decide if this should be the target emoji
            if random.random() < 0.1:  # 10% chance to be target
                emoji = self.target_emoji
                target_placed = True
                target_positions.append(cell_id)
            else:
                emoji = random.choice(self.emoji_bank)
            
            # Update button text and data
            try:
                button.setText(emoji)
                self.emoji_buttons[cell_id]["emoji"] = emoji
                self.emoji_buttons[cell_id]["correct"] = emoji == self.target_emoji
            except Exception as e:
                print(f"Error updating button {cell_id}: {e}")
                continue
        
        # If we haven't placed at least one target emoji, force it
        if not target_placed:
            # Find unclicked cells
            unclicked_cells = [cell_id for cell_id, data in self.emoji_buttons.items() 
                               if not data["clicked"]]
            
            if unclicked_cells:
                # Choose a random unclicked cell
                cell_id = random.choice(unclicked_cells)
                button = self.emoji_buttons[cell_id]["button"]
                
                try:
                    button.setText(self.target_emoji)
                    self.emoji_buttons[cell_id]["emoji"] = self.target_emoji
                    self.emoji_buttons[cell_id]["correct"] = True
                    target_positions.append(cell_id)
                except Exception as e:
                    print(f"Error setting forced target emoji: {e}")
        
        # Process events to keep UI responsive
        QApplication.processEvents()
        
        print(f"Refresh complete. Target emoji positions: {target_positions}")
    
    def on_emoji_clicked(self, cell_id):
        """Handle emoji button clicks"""
        if not self.game_started or self.game_completed:
            return
            
        # Get cell data
        cell_data = self.emoji_buttons.get(cell_id)
        if not cell_data or cell_data["clicked"]:
            return
            
        # Mark as clicked
        cell_data["clicked"] = True
        button = cell_data["button"]
        
        # Check if correct emoji
        if cell_data["correct"]:
            # Correct match
            self.score += 10
            button.setStyleSheet("""
                background-color: #2ECC71;
                color: white;
                border: 2px solid #27AE60;
                border-radius: 6px;
            """)
            self.score_label.setText(f"Score: {self.score}")
        else:
            # Incorrect match
            button.setStyleSheet("""
                background-color: #E74C3C;
                color: white;
                border: 2px solid #C0392B;
                border-radius: 6px;
            """)
            
        # Disable the button
        button.setEnabled(False)
        
        # Check if game should end
        remaining_unclicked = sum(1 for data in self.emoji_buttons.values() if not data["clicked"])
        if remaining_unclicked < 2:
            # Less than 2 cells left, end the game
            self.end_game()
            return
        
        # Check if all target emojis have been clicked
        target_remaining = any(not data["clicked"] and data["correct"] 
                             for data in self.emoji_buttons.values())
                             
        if not target_remaining:
            # Choose a new target emoji and refresh the board
            self.target_emoji = random.choice(self.emoji_bank)
            self.target_label.setText(self.target_emoji)
            self.refresh_board()
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def end_game(self):
        """End the game and display results"""
        print(f"EmojiGameUI - Ending game with final score: {self.score}")
        
        if self.refresh_timer:
            self.refresh_timer.stop()
            
        self.game_completed = True
        self.status_label.setText("Status: Game completed")
        
        try:
            # Re-enable start button
            if self.start_button:
                print(f"Re-enabling start button: {self.start_button}")
                self.start_button.setEnabled(True)
            else:
                print("Warning: start_button is None in end_game")
        except Exception as e:
            print(f"Error re-enabling start button: {e}")
        
        # Update the patient's score in database
        try:
            print(f"Updating emoji score for {self.patient_name} to {self.score}")
            result = self.update_emoji_score(self.patient_name, self.score)
            print(f"Score update {'successful' if result else 'failed'}")
        except Exception as e:
            print(f"Error updating score: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Show game over message
        try:
            QMessageBox.information(self, "Game Over", f"Game completed! Final score: {self.score}")
        except Exception as e:
            print(f"Error showing game over message: {e}")
    
    def update_emoji_score(self, patient_name, score):
        """Update the emoji score in the database"""
        try:
            print(f"Updating emoji score for {patient_name} to {score}")
            # Import the database utility
            from db_utils import db
            
            # Get patient data matching the name
            patient_data = db.get_patient_by_name(patient_name)
            
            if not patient_data.empty:
                # Get the first matching patient's ID
                patient_id = patient_data.iloc[0]['id']
                print(f"Found patient ID: {patient_id}")
                
                # Update the assessment score in the database
                db.update_assessment_score(patient_id, "emoji", score)
                print(f"Successfully updated emoji score to {score} for patient ID {patient_id}")
                return True
            else:
                print(f"Error: No patient found with name {patient_name}")
                return False
        except Exception as e:
            print(f"Error updating emoji score: {str(e)}")
            import traceback
            traceback.print_exc()
            return False 