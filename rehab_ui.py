from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
                            QHeaderView, QSplitter, QFileDialog, QMessageBox,
                            QTabWidget, QTextEdit, QProgressBar, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon

class RehabUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
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
        user_info = QLabel("Patient Dashboard")
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
        
        # Create navigation buttons with modern style for patient UI
        sections = [
            {"name": "Home", "icon": "home"},
            {"name": "Rehab", "icon": "fitness_center"},
            {"name": "Community", "icon": "groups"},
            {"name": "Logout", "icon": "logout"}
        ]
        
        for section in sections:
            button = QPushButton(section["name"])
            button.setObjectName(f"nav_{section['name'].lower()}")
            
            # Highlight current page
            if section["name"] == "Rehab":
                button.setStyleSheet("""
                    background-color: rgba(255, 255, 255, 0.2);
                    font-weight: bold;
                """)
                button.setChecked(True)
            
            # Connect the navigation handler
            button.clicked.connect(self.create_navigation_handler(section["name"]))
            navbar_layout.addWidget(button)
        
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
        
        # Page title
        page_title = QLabel("Rehabilitation Exercises")
        page_title.setObjectName("title")
        content_layout.addWidget(page_title)
        
        # Create tabs for different types of exercises with modern styling
        exercise_tabs = QTabWidget()
        exercise_tabs.setDocumentMode(True)  # Use modern-looking tabs
        
        # Daily exercises tab
        daily_tab = QWidget()
        daily_layout = QVBoxLayout(daily_tab)
        daily_layout.setContentsMargins(15, 15, 15, 15)
        
        # Instructions card
        instructions_card = QFrame()
        instructions_card.setObjectName("dashboard_widget")
        instructions_card_layout = QVBoxLayout(instructions_card)
        
        daily_instructions = QLabel("These exercises should be performed daily to maintain progress and improve your motor skills.")
        daily_instructions.setWordWrap(True)
        daily_instructions.setStyleSheet("color: #3498DB; font-weight: bold;")
        instructions_card_layout.addWidget(daily_instructions)
        
        daily_layout.addWidget(instructions_card)
        
        # Exercise list with modern styling
        daily_exercises_container = QFrame()
        daily_exercises_container.setObjectName("dashboard_widget")
        daily_exercises_layout = QVBoxLayout(daily_exercises_container)
        
        exercises_title = QLabel("Today's Exercises")
        exercises_title.setObjectName("dashboard_title")
        daily_exercises_layout.addWidget(exercises_title)
        
        daily_exercises = QListWidget()
        daily_exercises.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
            }
            QListWidget::item { 
                border-bottom: 1px solid #EEEEEE; 
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        # Add exercise items with completion status and modern design
        exercises = [
            {"name": "Finger Tapping", "description": "Tap each finger to your thumb 10 times", "completed": True},
            {"name": "Wrist Flexion", "description": "Gently bend your wrist forward and backward 15 times", "completed": True},
            {"name": "Shoulder Rotation", "description": "Rotate your shoulders in circles, 10 times forward and 10 times backward", "completed": False},
            {"name": "Arm Raises", "description": "Raise your arms to shoulder height and hold for 5 seconds, repeat 10 times", "completed": False},
            {"name": "Hand Squeeze", "description": "Squeeze a soft ball in your palm for 5 seconds, release, and repeat 15 times", "completed": False}
        ]
        
        for exercise in exercises:
            item = QListWidgetItem()
            item_text = f"{exercise['name']}: {exercise['description']}"
            item.setText(item_text)
            
            if exercise["completed"]:
                item.setIcon(QIcon.fromTheme("dialog-ok", QIcon.fromTheme("emblem-checked")))
                item.setBackground(Qt.green)
                item.setForeground(Qt.white)
            
            daily_exercises.addItem(item)
            
        daily_exercises_layout.addWidget(daily_exercises)
        
        # Add progress tracking with modern design
        progress_container = QFrame()
        progress_container.setObjectName("dashboard_widget")
        progress_layout = QVBoxLayout(progress_container)
        
        progress_title = QLabel("Daily Progress")
        progress_title.setObjectName("dashboard_title")
        progress_layout.addWidget(progress_title)
        
        progress_label = QLabel("You've completed 2 out of 5 exercises today")
        progress_label.setStyleSheet("color: #3498DB; margin-top: 5px;")
        progress_layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setValue(40)  # 40% complete
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #ECEFF1;
                border-radius: 4px;
                text-align: center;
                color: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2ECC71;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(progress_bar)
        
        # Add all containers to the daily layout
        daily_layout.addWidget(daily_exercises_container)
        daily_layout.addWidget(progress_container)
        
        # Weekly exercises tab (with similar modern styling)
        weekly_tab = QWidget()
        weekly_layout = QVBoxLayout(weekly_tab)
        weekly_layout.setContentsMargins(15, 15, 15, 15)
        
        weekly_instructions_card = QFrame()
        weekly_instructions_card.setObjectName("dashboard_widget")
        weekly_card_layout = QVBoxLayout(weekly_instructions_card)
        
        weekly_instructions = QLabel("These exercises should be performed 2-3 times per week to build strength and coordination.")
        weekly_instructions.setWordWrap(True)
        weekly_instructions.setStyleSheet("color: #3498DB; font-weight: bold;")
        weekly_card_layout.addWidget(weekly_instructions)
        
        weekly_layout.addWidget(weekly_instructions_card)
        
        # Weekly exercises container
        weekly_exercises_container = QFrame()
        weekly_exercises_container.setObjectName("dashboard_widget")
        weekly_exercises_layout = QVBoxLayout(weekly_exercises_container)
        
        weekly_title = QLabel("Weekly Exercises")
        weekly_title.setObjectName("dashboard_title")
        weekly_exercises_layout.addWidget(weekly_title)
        
        weekly_exercises = QListWidget()
        weekly_exercises.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
            }
            QListWidget::item { 
                border-bottom: 1px solid #EEEEEE; 
                padding: 10px;
            }
        """)
        
        weekly_items = [
            "Balance Training: Stand on one foot for 30 seconds, then switch",
            "Coordination Exercise: Touch your nose with alternating fingers",
            "Strength Training: Hold light weights while standing and sitting",
            "Fine Motor Skills: Pick up small objects and place them in a container"
        ]
        
        for item in weekly_items:
            weekly_exercises.addItem(item)
            
        weekly_exercises_layout.addWidget(weekly_exercises)
        weekly_layout.addWidget(weekly_exercises_container)
        
        # Video placeholder with modern design
        video_container = QFrame()
        video_container.setObjectName("dashboard_widget")
        video_layout = QVBoxLayout(video_container)
        
        video_title = QLabel("Exercise Tutorial")
        video_title.setObjectName("dashboard_title")
        video_layout.addWidget(video_title)
        
        video_placeholder = QLabel("Exercise Video will play here when selected")
        video_placeholder.setAlignment(Qt.AlignCenter)
        video_placeholder.setStyleSheet("""
            background-color: #ECEFF1;
            padding: 40px;
            color: #7F8C8D;
            border-radius: 4px;
        """)
        video_placeholder.setMinimumHeight(200)
        video_layout.addWidget(video_placeholder)
        
        weekly_layout.addWidget(video_container)
        
        # Add tabs to tab widget
        exercise_tabs.addTab(daily_tab, "Daily Exercises")
        exercise_tabs.addTab(weekly_tab, "Weekly Exercises")
        
        # Add exercise tabs to content layout
        content_layout.addWidget(exercise_tabs)
        
        # Add all major containers to the main layout
        main_layout.addWidget(header_container)
        main_layout.addWidget(navbar)
        main_layout.addWidget(content_container, 1)  # Give it a stretch factor
        
        # Set the main layout
        self.setLayout(main_layout) 
        
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler 