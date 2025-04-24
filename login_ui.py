import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QComboBox, QFormLayout,
                            QStackedWidget, QMessageBox, QGroupBox, QRadioButton,
                            QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette, QIcon
import os

class LoginUI(QWidget):
    # Signal to notify main app when login is successful
    login_successful = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel - Welcome and info
        left_panel = QFrame()
        left_panel.setObjectName("left_panel")
        left_panel.setStyleSheet("""
            #left_panel {
                background-color: #2C3E50;
                color: white;
            }
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(20)
        
        # Logo and welcome text
        logo_label = QLabel()
        try:
            pixmap = QPixmap("images/logo.png")
            logo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            # Create a text-based logo as fallback
            logo_label.setText("NeuroWell")
            logo_label.setStyleSheet("font-size: 32pt; font-weight: bold; color: white;")
        
        logo_label.setAlignment(Qt.AlignCenter)
        
        # Welcome text
        welcome_label = QLabel("Welcome to NeuroWell")
        welcome_label.setObjectName("title")
        welcome_label.setStyleSheet("""
            #title {
                font-size: 24pt;
                font-weight: bold;
                color: white;
            }
        """)
        welcome_label.setAlignment(Qt.AlignCenter)
        
        # Description
        desc_label = QLabel("Your comprehensive neuro-rehabilitation platform")
        desc_label.setObjectName("subtitle")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            #subtitle {
                font-size: 14pt;
                color: #3498DB;
            }
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        
        # Add a horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); min-height: 1px;")
        
        # Features in a modern card layout
        features_container = QFrame()
        features_container.setObjectName("features_container")
        features_container.setStyleSheet("""
            #features_container {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        features_layout = QVBoxLayout(features_container)
        
        features_title = QLabel("Key Features")
        features_title.setObjectName("section_title")
        features_title.setStyleSheet("""
            #section_title {
                font-size: 16pt;
                font-weight: bold;
                color: white;
            }
        """)
        features_layout.addWidget(features_title)
        
        features = [
            ("✓ Comprehensive Assessment", "Using computer vision, speech analysis, and cognitive tests"),
            ("✓ Patient Management", "Create and manage detailed patient profiles"),
            ("✓ Personalized Rehab", "Tailored rehabilitation plans based on assessment results"),
            ("✓ Progress Tracking", "Monitor and visualize recovery over time")
        ]
        
        for title, description in features:
            feature_item = QFrame()
            feature_item.setObjectName("feature_item")
            item_layout = QVBoxLayout(feature_item)
            item_layout.setContentsMargins(0, 10, 0, 10)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold; color: white; font-size: 12pt;")
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 10pt;")
            desc_label.setWordWrap(True)
            
            item_layout.addWidget(title_label)
            item_layout.addWidget(desc_label)
            
            features_layout.addWidget(feature_item)
        
        # Add components to left layout
        left_layout.addWidget(logo_label)
        left_layout.addWidget(welcome_label)
        left_layout.addWidget(desc_label)
        left_layout.addWidget(line)
        left_layout.addWidget(features_container)
        left_layout.addStretch()
        
        # Right panel - Login form
        right_panel = QFrame()
        right_panel.setObjectName("right_panel")
        right_panel.setStyleSheet("""
            #right_panel {
                background-color: white;
            }
        """)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(20)
        
        # Login form header
        login_header = QLabel("Sign In")
        login_header.setObjectName("login_header")
        login_header.setStyleSheet("""
            #login_header {
                font-size: 24pt;
                font-weight: bold;
                color: #2C3E50;
            }
        """)
        
        login_subtitle = QLabel("Please enter your credentials")
        login_subtitle.setStyleSheet("color: #7F8C8D; margin-bottom: 15px;")
        
        # Form container
        form_container = QFrame()
        form_container.setObjectName("form_container")
        form_container.setStyleSheet("""
            #form_container {
                background-color: #F5F7FA;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        # User type selection
        user_type_label = QLabel("I am a:")
        user_type_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.user_type_combo = QComboBox()
        self.user_type_combo.addItems(["Nurse", "Patient"])
        self.user_type_combo.setStyleSheet("""
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
        """)
        
        # Account status
        account_label = QLabel("Account Status:")
        account_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.account_status_combo = QComboBox()
        self.account_status_combo.addItems(["Yes (I have an account)", "No (Create new account)", "I forgot my password"])
        self.account_status_combo.currentIndexChanged.connect(self.on_account_status_changed)
        self.account_status_combo.setStyleSheet("""
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
        """)
        
        # Email field with icon
        email_label = QLabel("Email Address:")
        email_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet("""
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            padding-left: 10px;
            background-color: white;
        """)
        
        # Password field with icon
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setStyleSheet("""
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            padding-left: 10px;
            background-color: white;
        """)
        
        # Sign in button
        self.auth_button = QPushButton("Sign In")
        self.auth_button.setObjectName("auth_button")
        self.auth_button.setCursor(Qt.PointingHandCursor)
        self.auth_button.setStyleSheet("""
            #auth_button {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
                font-size: 12pt;
            }
            #auth_button:hover {
                background-color: #2980B9;
            }
        """)
        self.auth_button.clicked.connect(self.authenticate)
        
        # Add form fields to layout
        form_layout.addWidget(user_type_label)
        form_layout.addWidget(self.user_type_combo)
        form_layout.addWidget(account_label)
        form_layout.addWidget(self.account_status_combo)
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Create space between fields and button
        vspacer = QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
        form_layout.addItem(vspacer)
        
        form_layout.addWidget(self.auth_button)
        
        # Add components to right layout
        right_layout.addWidget(login_header)
        right_layout.addWidget(login_subtitle)
        right_layout.addWidget(form_container)
        right_layout.addStretch()
        
        # Add version info at bottom
        version_label = QLabel("NeuroWell v1.0 - Developed by ByteBuddies")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #95A5A6; font-size: 9pt;")
        right_layout.addWidget(version_label)
        
        # Add panels to main layout with proper proportions
        main_layout.addWidget(left_panel, 4)
        main_layout.addWidget(right_panel, 3)
        
        # Set main layout
        self.setLayout(main_layout)
    
    def on_account_status_changed(self, index):
        # Update UI based on account status selection
        if index == 0:  # Yes
            self.auth_button.setText("Sign In")
            self.password_input.setEnabled(True)
            self.password_input.setVisible(True)
        elif index == 1:  # No
            self.auth_button.setText("Create Account")
            self.password_input.setEnabled(True)
            self.password_input.setVisible(True)
        else:  # Forgot password
            self.auth_button.setText("Send Password Reset Email")
            self.password_input.setEnabled(False)
            self.password_input.setVisible(False)
    
    def is_valid_email(self, email):
        # Validate email format
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
    
    def authenticate(self):
        # Get form values
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        account_status = self.account_status_combo.currentText()
        user_type = self.user_type_combo.currentText()
        
        # Basic form validation
        if account_status.startswith("Yes") or account_status.startswith("No"):
            if not email or not password:
                QMessageBox.warning(self, "Validation Error", "Both email and password fields must be filled.")
                return
        else:  # Forgot password
            if not email:
                QMessageBox.warning(self, "Validation Error", "Email field must be filled.")
                return
        
        # Validate email format
        if not self.is_valid_email(email):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address.")
            return
        
        # Handle authentication based on account status
        if account_status.startswith("Yes"):
            # In a real app, this would verify credentials against a database
            # For demo, we'll just accept any valid email
            self.login_successful.emit(email, user_type)
        
        elif account_status.startswith("No"):
            # In a real app, this would create a new account
            # For demo, we'll just accept any valid email
            QMessageBox.information(self, "Account Created", f"Account for {email} has been created successfully.")
            self.login_successful.emit(email, user_type)
        
        else:  # Forgot password
            # In a real app, this would send a reset email
            QMessageBox.information(self, "Password Reset", f"Password reset link has been sent to {email}.")
    
    def reset_form(self):
        self.email_input.clear()
        self.password_input.clear()
        self.user_type_combo.setCurrentIndex(0)
        self.account_status_combo.setCurrentIndex(0) 