import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QStackedWidget, QLabel, QPushButton, 
                            QLineEdit, QComboBox, QFormLayout, QMessageBox,
                            QTableWidget, QTableWidgetItem, QFileDialog,
                            QScrollArea, QScroller)
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QPalette, QColor, QIcon

# Import module UIs
from home_ui import HomeUI
from login_ui import LoginUI
from patient_ui import PatientUI
from physio_ui import PhysioUI
from hand_ui import HandUI
from game_ui import GameUI
from result_ui import ResultUI
from rehab_ui import RehabUI
from community_ui import CommunityUI

# Import game UIs
from snake_game_ui import SnakeGameUI
from emoji_game_ui import EmojiGameUI
from ball_game_ui import BallGameUI

class NeuroWellApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set up the main window
        self.setWindowTitle("NeuroWell")
        self.setMinimumSize(1200, 800)
        
        # Set additional window properties to improve rendering
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # Ensure proper cleanup
        
        # Session state (similar to Streamlit's st.session_state)
        self.session_state = {
            "user_info": None,
            "user_type": None
        }
        
        # Initialize the main stacked widget for navigation
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize all UI components
        self.setup_ui()
        
    def setup_ui(self):
        # Create login page
        self.login_page = LoginUI(self)
        self.stacked_widget.addWidget(self.login_page)
        
        # Connect login signals
        self.login_page.login_successful.connect(self.on_login_successful)
        
        # Set initial page to login
        self.stacked_widget.setCurrentWidget(self.login_page)
    
    def on_login_successful(self, email, user_type):
        # Update session state
        self.session_state["user_info"] = email
        self.session_state["user_type"] = user_type
        
        # Initialize appropriate UI based on user type
        if user_type == "Nurse":
            self.init_nurse_ui()
        else:
            self.init_patient_ui()
    
    def init_nurse_ui(self):
        # Create all the nurse UI pages
        self.home_page = HomeUI(self)
        self.physio_page = PhysioUI(self)
        self.hand_page = HandUI(self)
        self.game_page = GameUI(self)
        self.result_page = ResultUI(self)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.physio_page)
        self.stacked_widget.addWidget(self.hand_page)
        self.stacked_widget.addWidget(self.game_page)
        self.stacked_widget.addWidget(self.result_page)
        
        # Set initial page to home
        self.stacked_widget.setCurrentWidget(self.home_page)
        
        # Connect navigation signals
        self.home_page.navigate_to_signal.connect(self.navigate_to)
        self.physio_page.navigate_to_signal.connect(self.navigate_to)
        self.hand_page.navigate_to_signal.connect(self.navigate_to)
        self.game_page.navigate_to_signal.connect(self.navigate_to)
        self.result_page.navigate_to_signal.connect(self.navigate_to)
        
        # Apply QSS styling to all widgets
        self.apply_global_styles()
    
    def init_patient_ui(self):
        # Create all the patient UI pages
        self.patient_home_page = PatientUI(self)
        self.rehab_page = RehabUI(self)
        self.community_page = CommunityUI(self)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.patient_home_page)
        self.stacked_widget.addWidget(self.rehab_page)
        self.stacked_widget.addWidget(self.community_page)
        
        # Set initial page to patient home
        self.stacked_widget.setCurrentWidget(self.patient_home_page)
        
        # Connect navigation signals
        self.patient_home_page.navigate_to_signal.connect(self.navigate_to)
        self.rehab_page.navigate_to_signal.connect(self.navigate_to)
        self.community_page.navigate_to_signal.connect(self.navigate_to)
    
    @pyqtSlot(str)
    def navigate_to(self, page_name):
        # Add debugging output
        print(f"Navigation requested to: {page_name}")
        print(f"Current user type: {self.session_state['user_type']}")
        
        # Navigation logic
        if page_name == "Home" and self.session_state["user_type"] == "Nurse":
            print("Navigating to Nurse Home page")
            self.stacked_widget.setCurrentWidget(self.home_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Physio" and self.session_state["user_type"] == "Nurse":
            print("Navigating to Physio page")
            self.stacked_widget.setCurrentWidget(self.physio_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Hand" and self.session_state["user_type"] == "Nurse":
            print("Navigating to Hand page")
            self.stacked_widget.setCurrentWidget(self.hand_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Game" and self.session_state["user_type"] == "Nurse":
            print("Navigating to Game page")
            self.stacked_widget.setCurrentWidget(self.game_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Result" and self.session_state["user_type"] == "Nurse":
            print("Navigating to Result page")
            self.stacked_widget.setCurrentWidget(self.result_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Home" and self.session_state["user_type"] == "Patient":
            print("Navigating to Patient Home page")
            self.stacked_widget.setCurrentWidget(self.patient_home_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Rehab" and self.session_state["user_type"] == "Patient":
            print("Navigating to Rehab page")
            self.stacked_widget.setCurrentWidget(self.rehab_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Community" and self.session_state["user_type"] == "Patient":
            print("Navigating to Community page")
            self.stacked_widget.setCurrentWidget(self.community_page)
            QApplication.processEvents()  # Force UI update
        elif page_name == "Logout":
            print("Logging out")
            self.logout()
        else:
            print(f"Warning: Unknown navigation target '{page_name}' for user type '{self.session_state['user_type']}'")
            QMessageBox.warning(self, "Navigation Error", f"Unknown navigation target: {page_name}")
            
        # Optional: Print current widget for debugging
        print(f"Current widget is now: {self.stacked_widget.currentWidget().__class__.__name__}")
    
    def logout(self):
        # Reset session state
        self.session_state["user_info"] = None
        self.session_state["user_type"] = None
        
        # Remove all widgets except login
        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Show login page
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.login_page.reset_form()

    def apply_global_styles(self):
        """Apply consistent styling to all UI elements"""
        
        # Apply stylesheet to the application
        style = """
        /* Modern Design System */
        
        /* Base Styles */
        QWidget {
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            font-size: 10pt;
            color: #333333;
        }
        
        /* Typography */
        QLabel {
            color: #333333;
            padding: 2px;
        }
        
        QLabel#title {
            font-size: 24pt;
            font-weight: bold;
            color: #2C3E50;
            padding: 10px 0;
        }
        
        QLabel#subtitle {
            font-size: 14pt;
            color: #3498DB;
            padding: 5px 0;
        }
        
        QLabel#section_title {
            font-size: 12pt;
            font-weight: bold;
            color: #2C3E50;
            padding: 10px 0 5px 0;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #3498DB;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-height: 30px;
        }
        
        QPushButton:hover {
            background-color: #2980B9;
        }
        
        QPushButton:pressed {
            background-color: #1A5276;
        }
        
        QPushButton:disabled {
            background-color: #BDC3C7;
            color: #7F8C8D;
        }
        
        QPushButton#primary {
            background-color: #3498DB;
        }
        
        QPushButton#success {
            background-color: #2ECC71;
        }
        
        QPushButton#warning {
            background-color: #F39C12;
        }
        
        QPushButton#danger {
            background-color: #E74C3C;
        }
        
        /* Cards */
        QGroupBox {
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            margin-top: 16px;
            background-color: white;
            padding: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            background-color: white;
            color: #2C3E50;
            font-weight: bold;
        }
        
        /* Form elements */
        QLineEdit, QTextEdit, QComboBox {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            selection-background-color: #3498DB;
            selection-color: white;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 1px solid #3498DB;
        }
        
        QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {
            background-color: #ECEFF1;
            color: #7F8C8D;
        }
        
        QComboBox {
            padding-right: 20px;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: none;
        }
        
        QComboBox::down-arrow {
            width: 12px;
            height: 12px;
        }
        
        QComboBox QAbstractItemView {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            background-color: white;
            selection-background-color: #3498DB;
            selection-color: white;
        }
        
        /* Tables */
        QTableWidget {
            gridline-color: #ECEFF1;
            background-color: white;
            selection-background-color: #3498DB;
            selection-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        }
        
        QHeaderView::section {
            background-color: #F5F5F5;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #E0E0E0;
            font-weight: bold;
            color: #2C3E50;
        }
        
        QTableWidget::item {
            padding: 6px;
        }
        
        QTableWidget::item:selected {
            background-color: #3498DB;
            color: white;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            top: -1px;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #F5F5F5;
            border: 1px solid #E0E0E0;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 8px 16px;
            margin-right: 2px;
            color: #7F8C8D;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
            color: #2C3E50;
            font-weight: bold;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #ECF0F1;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            border: none;
            background-color: #F5F5F5;
            width: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #BDC3C7;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #95A5A6;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            border: none;
            background-color: #F5F5F5;
            height: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #BDC3C7;
            border-radius: 6px;
            min-width: 30px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #95A5A6;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        /* Scroll area */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        /* Status indicators */
        QProgressBar {
            border: none;
            background-color: #ECEFF1;
            border-radius: 2px;
            text-align: center;
            color: white;
        }
        
        QProgressBar::chunk {
            background-color: #3498DB;
            border-radius: 2px;
        }
        
        /* Modern Nav Bar */
        #navbar {
            background-color: #2C3E50;
            padding: 10px;
            border-radius: 6px;
        }
        
        #navbar QPushButton {
            background-color: transparent;
            color: white;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: normal;
            min-width: 100px;
            text-align: center;
        }
        
        #navbar QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        #navbar QPushButton:checked, #navbar QPushButton:pressed {
            background-color: rgba(255, 255, 255, 0.2);
            font-weight: bold;
        }
        
        /* Card layouts */
        #card_container {
            background-color: #F5F7FA;
            border-radius: 8px;
            padding: 10px;
        }
        
        /* Dashboard widgets */
        #dashboard_widget {
            background-color: white;
            border-radius: 8px;
            border: 1px solid #E0E0E0;
            padding: 15px;
        }
        
        #dashboard_title {
            font-size: 14pt;
            font-weight: bold;
            color: #2C3E50;
        }
        
        #dashboard_value {
            font-size: 24pt;
            font-weight: bold;
            color: #3498DB;
        }
        """
        
        self.setStyleSheet(style)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Enable double buffering to reduce flickering
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    
    # Enable kinetic scrolling for touch interfaces and smoother scroll behavior
    QScroller.grabGesture(app.desktop(), QScroller.LeftMouseButtonGesture)
    
    # Create a custom palette with a modern color theme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 247, 250))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(236, 240, 241))
    palette.setColor(QPalette.Button, QColor(52, 152, 219))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(41, 128, 185))
    palette.setColor(QPalette.LinkVisited, QColor(142, 68, 173))
    app.setPalette(palette)
    
    # Load application icon if available
    try:
        app_icon = QIcon("images/logo.png")
        app.setWindowIcon(app_icon)
    except:
        pass
    
    window = NeuroWellApp()
    
    # Set window attributes to reduce flickering
    window.setMinimumSize(1200, 800)
    window.setWindowTitle("NeuroWell")
    window.setAttribute(Qt.WA_OpaquePaintEvent)
    window.setAttribute(Qt.WA_NoSystemBackground)
    window.show()
    
    sys.exit(app.exec_()) 