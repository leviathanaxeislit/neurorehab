import os
import pandas as pd
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSplitter, QFileDialog, QMessageBox, 
                            QProgressBar, QFrame, QScrollArea, QCalendarWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QPixmap, QFont, QIcon, QColor

class PatientUI(QWidget):
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
        
        # Create navigation buttons with modern style
        sections = [
            {"name": "Home", "icon": "home"},
            {"name": "Rehab", "icon": "fitness"},
            {"name": "Community", "icon": "people"},
            {"name": "Logout", "icon": "logout"}
        ]
        
        for section in sections:
            button = QPushButton(section["name"])
            button.setObjectName(f"nav_{section['name'].lower()}")
            
            # Highlight current page
            if section["name"] == "Home":
                button.setStyleSheet("""
                    background-color: rgba(255, 255, 255, 0.2);
                    font-weight: bold;
                """)
                button.setChecked(True)
            
            # Connect the navigation handler
            button.clicked.connect(self.create_navigation_handler(section["name"]))
            navbar_layout.addWidget(button)
        
        # Content area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
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
        
        # Patient welcome card
        welcome_card = QFrame()
        welcome_card.setObjectName("dashboard_widget")
        welcome_layout = QVBoxLayout(welcome_card)
        
        # Create welcome message
        if self.parent and hasattr(self.parent, 'session_state'):
            user_email = self.parent.session_state.get("user_info", "User")
            welcome_label = QLabel(f"Welcome back, {user_email}!")
            welcome_label.setObjectName("title")
        else:
            welcome_label = QLabel("Welcome back!")
            welcome_label.setObjectName("title")
            
        welcome_layout.addWidget(welcome_label)
        
        # Add current date
        current_date = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        current_date.setStyleSheet("color: #7F8C8D; font-size: 12pt;")
        welcome_layout.addWidget(current_date)
        
        content_layout.addWidget(welcome_card)
        
        # Create content layout
        dashboard_layout = QHBoxLayout()
        
        # Left panel - Patient info
        left_panel = QFrame()
        left_panel.setObjectName("dashboard_widget")
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # Patient profile title
        profile_title = QLabel("Your Profile")
        profile_title.setObjectName("dashboard_title")
        left_layout.addWidget(profile_title)
        
        # Add profile picture
        profile_image = QLabel()
        profile_image.setAlignment(Qt.AlignCenter)
        profile_image.setMinimumSize(150, 150)
        profile_image.setMaximumSize(150, 150)
        
        # Try to load profile image, use placeholder if not found
        try:
            # Generate a colored circle with text as avatar
            avatar_size = 150
            if self.parent and hasattr(self.parent, 'session_state'):
                initials = ''.join([name[0].upper() for name in self.parent.session_state.get("user_info", "User").split('@')[0].split('.')[:2]])
            else:
                initials = "U"
                
            pixmap = QPixmap(avatar_size, avatar_size)
            pixmap.fill(Qt.transparent)
            
            # Choose color based on first letter
            colors = [
                QColor(52, 152, 219),  # Blue
                QColor(46, 204, 113),  # Green
                QColor(155, 89, 182),  # Purple
                QColor(231, 76, 60),   # Red
                QColor(241, 196, 15)   # Yellow
            ]
            if len(initials) > 0:
                color_index = ord(initials[0].upper()) % len(colors)
            else:
                color_index = 0
                
            from PyQt5.QtGui import QPainter, QBrush, QPen, QFont
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw circle
            painter.setBrush(QBrush(colors[color_index]))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, avatar_size, avatar_size)
            
            # Draw text
            painter.setPen(QPen(Qt.white))
            painter.setFont(QFont("Arial", int(avatar_size/3), QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)
            painter.end()
            
            profile_image.setPixmap(pixmap)
            profile_image.setStyleSheet("""
                border-radius: 75px;
                background-color: white;
                border: 2px solid #E0E0E0;
            """)
        except Exception as e:
            print(f"Error creating avatar: {e}")
            profile_image.setText("Profile Picture")
            profile_image.setStyleSheet("""
                background-color: #f0f0f0;
                border-radius: 75px;
                border: 2px solid #E0E0E0;
                color: #7F8C8D;
            """)
            
        profile_image.setFixedSize(150, 150)
        left_layout.addWidget(profile_image, 0, Qt.AlignCenter)
        
        # Add patient information
        info_layout = QFormLayout()
        info_layout.setVerticalSpacing(10)
        info_layout.setContentsMargins(0, 20, 0, 0)
        
        # Display patient details
        email_label = QLabel("Email:")
        email_label.setStyleSheet("font-weight: bold;")
        if self.parent and hasattr(self.parent, 'session_state'):
            email_value = QLabel(self.parent.session_state.get("user_info", "Not available"))
        else:
            email_value = QLabel("Not available")
        
        account_type_label = QLabel("Account Type:")
        account_type_label.setStyleSheet("font-weight: bold;")
        account_type_value = QLabel("Patient")
        
        status_label = QLabel("Rehab Status:")
        status_label.setStyleSheet("font-weight: bold;")
        status_value = QLabel("Active")
        status_value.setStyleSheet("color: #2ECC71; font-weight: bold;")
        
        since_label = QLabel("Member Since:")
        since_label.setStyleSheet("font-weight: bold;")
        # Generate a random date 1-12 months ago
        join_date = datetime.now() - timedelta(days=random.randint(30, 365))
        since_value = QLabel(join_date.strftime("%B %d, %Y"))
        
        therapist_label = QLabel("Assigned Therapist:")
        therapist_label.setStyleSheet("font-weight: bold;")
        therapist_value = QLabel("Dr. Smith")
        
        next_appt_label = QLabel("Next Appointment:")
        next_appt_label.setStyleSheet("font-weight: bold;")
        # Generate a future date
        next_appt = datetime.now() + timedelta(days=random.randint(1, 14))
        next_appt_value = QLabel(next_appt.strftime("%B %d, %Y - %I:%M %p"))
        next_appt_value.setStyleSheet("color: #E74C3C; font-weight: bold;")
        
        info_layout.addRow(email_label, email_value)
        info_layout.addRow(account_type_label, account_type_value)
        info_layout.addRow(status_label, status_value)
        info_layout.addRow(since_label, since_value)
        info_layout.addRow(therapist_label, therapist_value)
        info_layout.addRow(next_appt_label, next_appt_value)
        
        left_layout.addLayout(info_layout)
        
        # Add edit profile button
        edit_profile_button = QPushButton("Edit Profile")
        edit_profile_button.setStyleSheet("""
            background-color: #3498DB;
            color: white;
            padding: 8px;
            border-radius: 4px;
            margin-top: 15px;
        """)
        left_layout.addWidget(edit_profile_button)
        left_layout.addStretch()
        
        # Right panel - Dashboard
        right_panel = QFrame()
        right_panel.setObjectName("dashboard_widget")
        right_layout = QVBoxLayout(right_panel)
        
        # Dashboard title
        dashboard_title = QLabel("Your Rehabilitation Progress")
        dashboard_title.setObjectName("dashboard_title")
        right_layout.addWidget(dashboard_title)
        
        # Progress summary
        progress_summary = QLabel("You've made significant progress in the past month. Keep up the good work!")
        progress_summary.setWordWrap(True)
        progress_summary.setStyleSheet("""
            color: #3498DB;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 10px;
        """)
        right_layout.addWidget(progress_summary)
        
        # Progress bars
        progress_container = QFrame()
        progress_container.setObjectName("card_container")
        progress_container.setStyleSheet("""
            #card_container {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
                padding: 15px;
            }
        """)
        
        progress_grid = QVBoxLayout(progress_container)
        progress_grid.setSpacing(15)
        
        # Create progress categories
        progress_categories = [
            {"name": "Speech Therapy", "progress": random.randint(65, 85), "color": "#3498DB"},
            {"name": "Hand Coordination", "progress": random.randint(50, 75), "color": "#2ECC71"},
            {"name": "Cognitive Function", "progress": random.randint(70, 90), "color": "#F39C12"},
            {"name": "Physical Mobility", "progress": random.randint(60, 80), "color": "#9B59B6"}
        ]
        
        for category in progress_categories:
            category_layout = QVBoxLayout()
            
            # Add header with value
            header_layout = QHBoxLayout()
            
            category_label = QLabel(category["name"])
            category_label.setStyleSheet("font-weight: bold;")
            
            value_label = QLabel(f"{category['progress']}%")
            value_label.setAlignment(Qt.AlignRight)
            
            header_layout.addWidget(category_label)
            header_layout.addWidget(value_label)
            
            # Add progress bar
            progress_bar = QProgressBar()
            progress_bar.setValue(category["progress"])
            progress_bar.setTextVisible(False)
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #ECEFF1;
                    border-radius: 4px;
                    height: 10px;
                }}
                QProgressBar::chunk {{
                    background-color: {category["color"]};
                    border-radius: 4px;
                }}
            """)
            
            category_layout.addLayout(header_layout)
            category_layout.addWidget(progress_bar)
            
            progress_grid.addLayout(category_layout)
        
        right_layout.addWidget(progress_container)
        
        # Add recent scores table
        scores_title = QLabel("Your Recent Test Scores")
        scores_title.setObjectName("dashboard_title")
        scores_title.setContentsMargins(0, 15, 0, 5)
        right_layout.addWidget(scores_title)
        
        scores_table = QTableWidget(5, 2)
        scores_table.setHorizontalHeaderLabels(["Test Type", "Score"])
        scores_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        scores_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #EEEEEE;
            }
        """)
        
        # Sample data (would normally be loaded from database)
        test_data = [
            ("Speech Analysis", f"{random.randint(70, 85)}%"),
            ("Emoji Matching", f"{random.randint(75, 90)}%"),
            ("Snake Game", f"{random.randint(60, 80)}%"),
            ("Ball Tracking", f"{random.randint(65, 85)}%"),
            ("Overall Progress", f"{random.randint(65, 85)}%")
        ]
        
        for i, (test, score) in enumerate(test_data):
            scores_table.setItem(i, 0, QTableWidgetItem(test))
            scores_table.setItem(i, 1, QTableWidgetItem(score))
            
            # Highlight overall score
            if test == "Overall Progress":
                scores_table.item(i, 0).setBackground(Qt.lightGray)
                scores_table.item(i, 1).setBackground(Qt.lightGray)
        
        right_layout.addWidget(scores_table)
        
        # Add panels to dashboard layout
        dashboard_layout.addWidget(left_panel)
        dashboard_layout.addWidget(right_panel, 1)  # Give it a stretch factor
        
        # Add dashboard layout to content layout
        content_layout.addLayout(dashboard_layout)
        
        # Add message from doctor section
        message_group = QFrame()
        message_group.setObjectName("dashboard_widget")
        message_layout = QVBoxLayout(message_group)
        
        message_header = QLabel("Message from your Doctor")
        message_header.setObjectName("dashboard_title")
        message_layout.addWidget(message_header)
        
        message_text = QLabel("Your rehabilitation progress is going well. Please continue with your daily exercises and make sure to complete all the assigned tasks. Remember to take short breaks when needed and stay hydrated. We'll discuss your progress in detail during your next appointment. I've noticed significant improvement in your hand coordination exercises - keep up the good work!")
        message_text.setWordWrap(True)
        message_text.setStyleSheet("""
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            line-height: 1.5;
        """)
        
        message_from = QLabel("- Dr. Smith")
        message_from.setAlignment(Qt.AlignRight)
        message_from.setStyleSheet("font-style: italic; margin-top: 5px;")
        
        message_date = QLabel("Sent: Yesterday at 2:34 PM")
        message_date.setAlignment(Qt.AlignRight)
        message_date.setStyleSheet("color: #7F8C8D; font-size: 9pt;")
        
        message_layout.addWidget(message_text)
        message_layout.addWidget(message_from)
        message_layout.addWidget(message_date)
        
        content_layout.addWidget(message_group)
        
        # Upcoming appointments section
        appointments_group = QFrame()
        appointments_group.setObjectName("dashboard_widget")
        appointments_layout = QVBoxLayout(appointments_group)
        
        appointments_header = QLabel("Upcoming Appointments")
        appointments_header.setObjectName("dashboard_title")
        appointments_layout.addWidget(appointments_header)
        
        # Add calendar view
        appointments_container = QHBoxLayout()
        
        # Calendar widget
        calendar = QCalendarWidget()
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        calendar.setGridVisible(True)
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
            }
            QCalendarWidget QToolButton {
                color: #2C3E50;
                background-color: white;
                padding: 5px;
            }
            QCalendarWidget QMenu {
                width: 150px;
                left: 20px;
                color: #2C3E50;
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                color: #2C3E50;
                background-color: white;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2C3E50;
                background-color: white;
                selection-background-color: #3498DB;
                selection-color: white;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #F5F5F5;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        
        # Mark upcoming appointments on calendar
        appt_dates = [
            datetime.now() + timedelta(days=random.randint(1, 7)),
            datetime.now() + timedelta(days=random.randint(8, 14)),
            datetime.now() + timedelta(days=random.randint(15, 21))
        ]
        
        for appt_date in appt_dates:
            calendar.setDateTextFormat(
                QDate(appt_date.year, appt_date.month, appt_date.day),
                calendar.dateTextFormat(QDate(appt_date.year, appt_date.month, appt_date.day))
            )
        
        # Upcoming appointments list
        appointments_table = QTableWidget(3, 3)
        appointments_table.setHorizontalHeaderLabels(["Date", "Time", "Type"])
        appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        appointments_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #EEEEEE;
            }
        """)
        
        # Sample appointments
        appointment_types = ["Physio Session", "Progress Review", "Cognitive Assessment"]
        appointment_times = ["9:00 AM", "11:30 AM", "2:15 PM"]
        
        for i, appt_date in enumerate(appt_dates):
            appointments_table.setItem(i, 0, QTableWidgetItem(appt_date.strftime("%b %d, %Y")))
            appointments_table.setItem(i, 1, QTableWidgetItem(appointment_times[i]))
            appointments_table.setItem(i, 2, QTableWidgetItem(appointment_types[i]))
        
        appointments_container.addWidget(calendar)
        appointments_container.addWidget(appointments_table)
        
        appointments_layout.addLayout(appointments_container)
        
        content_layout.addWidget(appointments_group)
        
        # Add scroll content
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
        
    def load_patient_data(self, patient_email):
        # This would normally load patient data from a database
        # For this demo, we'll just use placeholder data
        pass 