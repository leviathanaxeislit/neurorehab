import os
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QComboBox, QGroupBox, QFormLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QSplitter, QFileDialog, 
                            QMessageBox, QTabWidget, QFrame, QGridLayout, QSpacerItem,
                            QSizePolicy, QDialog, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon, QIntValidator
from db_utils import db  # Import the database utility

class HomeUI(QWidget):
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
        user_info = QLabel("Nurse Dashboard")
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
            
            # Add icon if we had a proper icon set
            # button.setIcon(QIcon(f"images/icons/{section['icon']}.png"))
            # button.setIconSize(QSize(24, 24))
            
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
        
        # Content area
        content_container = QFrame()
        content_container.setObjectName("content_container")
        content_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_container.setStyleSheet("""
            #content_container {
                background-color: #F5F7FA;
            }
        """)
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Dashboard title
        dashboard_title = QLabel("Patient Management Dashboard")
        dashboard_title.setObjectName("title")
        
        # Dashboard summary cards
        metrics_container = QFrame()
        metrics_container.setObjectName("card_container")
        
        metrics_layout = QHBoxLayout(metrics_container)
        metrics_layout.setSpacing(20)
        
        # Create dashboard metrics cards
        metrics = [
            {"title": "Total Patients", "value": "Loading...", "color": "#3498DB"},
            {"title": "Assessments Today", "value": "0", "color": "#2ECC71"},
            {"title": "Pending Results", "value": "0", "color": "#F39C12"}
        ]
        
        for metric in metrics:
            card = QFrame()
            card.setObjectName("dashboard_widget")
            
            card_layout = QVBoxLayout(card)
            
            title_label = QLabel(metric["title"])
            title_label.setObjectName("dashboard_title")
            
            value_label = QLabel(metric["value"])
            value_label.setObjectName("dashboard_value")
            value_label.setStyleSheet(f"color: {metric['color']};")
            
            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            card_layout.addStretch()
            
            metrics_layout.addWidget(card)
        
        # Create patient management area
        patient_container = QFrame()
        patient_container.setObjectName("dashboard_widget")
        patient_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow it to expand
        
        patient_layout = QVBoxLayout(patient_container)
        patient_layout.setSpacing(10)  # Add some space between elements
        
        # Add search and filter controls
        controls_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patients...")
        self.search_input.setStyleSheet("""
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #BDC3C7;
            background-color: white;
        """)
        # Connect Enter/Return key to trigger search
        self.search_input.returnPressed.connect(self.search_patient)
        
        search_button = QPushButton("Search")
        search_button.setObjectName("primary")
        search_button.clicked.connect(self.search_patient)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondary")
        refresh_button.clicked.connect(self.load_data)
        
        add_patient_button = QPushButton("Add New Patient")
        add_patient_button.setObjectName("success")
        add_patient_button.setStyleSheet("""
            background-color: #2ECC71;
        """)
        add_patient_button.clicked.connect(self.show_add_patient_dialog)
        
        controls_layout.addWidget(self.search_input, 3)
        controls_layout.addWidget(search_button, 1)
        controls_layout.addWidget(refresh_button, 1)
        controls_layout.addStretch(1)
        controls_layout.addWidget(add_patient_button, 2)
        
        patient_layout.addLayout(controls_layout)
        
        # Create a scroll area for the table
        table_scroll_area = QScrollArea()
        table_scroll_area.setWidgetResizable(True)  # Important for proper scrolling
        table_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_scroll_area.setMinimumHeight(450)  # Ensure scroll area has minimum height
        table_scroll_area.setFrameShape(QFrame.NoFrame)  # Remove border
        table_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Create container for the table
        table_container = QWidget()
        table_container.setObjectName("table_container")
        table_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)

        # Patient table with modern styling
        self.all_patients_table = QTableWidget(0, 7)
        self.all_patients_table.setHorizontalHeaderLabels([
            "Name", "Age", "Gender", "Speech Score", "Emoji Score", "Snake Score", "Ball Score"
        ])
        self.all_patients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_patients_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.all_patients_table.setMinimumHeight(400)  # Increase minimum height
        self.all_patients_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow table to expand
        self.all_patients_table.setAlternatingRowColors(True)
        self.all_patients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.all_patients_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.all_patients_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #EEEEEE;
            }
            QTableWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #F9F9F9;
            }
            
            /* Scrollbar styling */
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 14px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #BCBCBC;
                min-height: 30px;
                border-radius: 7px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #3498DB;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        # Connect double-click event
        self.all_patients_table.cellDoubleClicked.connect(self.show_patient_details)

        # Add table to the scroll area's container
        table_container_layout.addWidget(self.all_patients_table)
        table_scroll_area.setWidget(table_container)

        # Add the scroll area to the patient layout
        patient_layout.addWidget(table_scroll_area, 1)  # Give it a stretch factor of 1
        
        # Add export options
        export_layout = QHBoxLayout()
        export_layout.setAlignment(Qt.AlignRight)
        
        export_csv_button = QPushButton("Export to CSV")
        export_csv_button.setObjectName("primary")
        export_csv_button.clicked.connect(self.download_csv)
        
        export_layout.addWidget(export_csv_button)
        
        patient_layout.addLayout(export_layout)
        
        # Build the content layout
        content_layout.addWidget(dashboard_title)
        content_layout.addWidget(metrics_container)
        content_layout.addWidget(patient_container, 10)  # Give it a much larger stretch factor
        
        # Add instructions card at the bottom, but with less prominence
        instructions_container = QFrame()
        instructions_container.setObjectName("dashboard_widget")
        instructions_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)  # Take minimum vertical space
        
        instructions_layout = QVBoxLayout(instructions_container)
        
        instructions_title = QLabel("Quick Guide")
        instructions_title.setObjectName("dashboard_title")
        instructions_layout.addWidget(instructions_title)
        
        instructions_grid = QGridLayout()
        instructions_grid.setColumnStretch(0, 1)
        instructions_grid.setColumnStretch(1, 1)
        
        tips = [
            "Add new patients using the 'Add New Patient' button above",
            "Run assessment tests by navigating to specific test pages",
            "View and export results using the Results page",
            "Contact support for assistance"
        ]
        
        row = 0
        col = 0
        for tip in tips:
            tip_label = QLabel(f"• {tip}")
            tip_label.setWordWrap(True)
            instructions_grid.addWidget(tip_label, row, col)
            
            # Move to next column or row
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        instructions_layout.addLayout(instructions_grid)
        content_layout.addWidget(instructions_container, 0)  # No stretch factor
        
        # Add all major containers to the main layout
        main_layout.addWidget(header_container, 0)  # Fixed height
        main_layout.addWidget(navbar, 0)  # Fixed height
        main_layout.addWidget(content_container, 1)  # Give it a stretch factor
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Load data from CSV
        self.load_data()
    
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler
    
    def load_data(self):
        try:
            # Get data from database instead of CSV
            from db_utils import db
            
            print("Attempting to load patients from database...")
            
            # Get all patients from database
            df = db.get_all_patients()
            
            print(f"Retrieved {len(df)} patients from database")
            print(f"DataFrame columns: {df.columns.tolist()}")
            
            if df.empty:
                print("Warning: No patients found in database")
                # Create a sample patient if database is empty
                print("Adding a sample patient...")
                sample_id = db.add_patient("Sample Patient", 65, "Male")
                if sample_id:
                    print(f"Added sample patient with ID: {sample_id}")
                    # Fetch patients again after adding sample
                    df = db.get_all_patients()
            
            # If we still have very few rows, add some test patients to demonstrate scrolling
            if len(df) < 10:
                print("Adding test patients to demonstrate scrolling...")
                for i in range(1, 15):  # Add several test patients
                    test_id = db.add_patient(f"Test Patient {i}", 30 + i, "Female" if i % 2 else "Male")
                    if test_id:
                        print(f"Added test patient with ID: {test_id}")
                
                # Reload patients
                df = db.get_all_patients()
            
            # Update metrics
            self.update_metrics(df)
            
            # Clear existing table data
            self.all_patients_table.setRowCount(0)
            
            # Define columns to display and their order
            display_columns = ['name', 'age', 'gender', 'speech_score', 'emoji_score', 'snake_score', 'ball_score']
            
            # Show the actual row count for debugging
            print(f"Setting table to show {len(df)} rows")
            
            # Ensure the table has enough rows allocated
            self.all_patients_table.setRowCount(len(df))
            
            # Populate table with data
            for i, row in df.iterrows():
                row_position = i  # Use the index directly since we pre-allocated rows
                
                # Add each column value in the right order
                for j, col_name in enumerate(display_columns):
                    if col_name in row:
                        # Get value and handle None/NaN values
                        value = row[col_name]
                        
                        if pd.isna(value) or value is None:
                            display_value = ""
                        elif col_name.endswith('_score') and pd.notna(value):
                            try:
                                if value == int(value):
                                    display_value = str(int(value))
                                else:
                                    display_value = f"{value:.1f}"
                            except:
                                display_value = str(value)
                        else:
                            display_value = str(value)
                        
                        # Create table item
                        item = QTableWidgetItem(display_value)
                        
                        # Center numeric columns
                        if col_name in ['age'] or col_name.endswith('_score'):
                            item.setTextAlignment(Qt.AlignCenter)
                        
                        self.all_patients_table.setItem(row_position, j, item)
                
                # Debug print each row as it's added
                print(f"Added row {row_position}: {row['name']}")
            
            # Ensure the table updates its display
            self.all_patients_table.resizeRowsToContents()
            self.all_patients_table.viewport().update()
            
            # Display final row count
            print(f"Final table row count: {self.all_patients_table.rowCount()}")
            
            # Update first metric card with actual patient count
            for widget in self.findChildren(QLabel):
                if widget.objectName() == "dashboard_value" and widget.text() == "Loading...":
                    widget.setText(str(len(df)))
                    break
        
        except Exception as e:
            print(f"Error loading patient data: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Error loading data: {str(e)}")
    
    def update_metrics(self, df):
        """Update the dashboard metrics based on data"""
        # Find top-level widgets in the UI
        for widget in self.findChildren(QLabel):
            if widget.objectName() == "dashboard_value" and widget.text() == "Loading...":
                widget.setText(str(len(df)))
                break
    
    def show_add_patient_dialog(self):
        """Show dialog to add a new patient"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Patient")
        dialog.setMinimumWidth(300)
        
        # Create layout for the dialog
        layout = QVBoxLayout(dialog)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Add input fields
        name_input = QLineEdit()
        age_input = QLineEdit()
        age_input.setValidator(QIntValidator(0, 120))  # Age between 0-120
        
        gender_combo = QComboBox()
        gender_combo.addItems(["Male", "Female", "Other"])
        
        form_layout.addRow("Name:", name_input)
        form_layout.addRow("Age:", age_input)
        form_layout.addRow("Gender:", gender_combo)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Add Patient")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(lambda: self.process_add_patient(dialog, name_input.text(), age_input.text(), gender_combo.currentText()))
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Show the dialog
        dialog.exec_()
    
    def process_add_patient(self, dialog, name, age_text, gender):
        """Process the add patient form data"""
        # Validate inputs
        if not name.strip():
            QMessageBox.warning(self, "Validation Error", "Patient name is required.")
            return
        
        if not age_text.strip():
            QMessageBox.warning(self, "Validation Error", "Patient age is required.")
            return
        
        try:
            age = int(age_text)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Age must be a valid number.")
            return
        
        # Close the dialog
        dialog.accept()
        
        # Add patient to database
        self.add_patient(name, age, gender)
    
    def add_patient(self, name, age, gender):
        """Add a new patient to the database"""
        try:
            # Add patient to database
            patient_id = db.add_patient(name, age, gender)
            
            if patient_id:
                QMessageBox.information(self, "Success", f"Patient {name} added successfully.")
                # Refresh the data display
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to add patient.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error adding patient: {str(e)}")
    
    def search_patient(self):
        """Search for a patient in the database"""
        search_text = self.search_input.text().strip()
        
        if not search_text:
            # If search text is empty, load all patients
            self.load_data()
            return
        
        try:
            # Get patient data matching the search text
            patient_data = db.get_patient_by_name(search_text)
            
            if patient_data.empty:
                QMessageBox.information(self, "Search Results", f"No patients found matching '{search_text}'.")
                return
            
            # Clear existing table data
            self.all_patients_table.setRowCount(0)
            
            # Define columns to display and their order
            display_columns = ['name', 'age', 'gender', 'speech_score', 'emoji_score', 'snake_score', 'ball_score']
            
            print(f"Search found {len(patient_data)} matching patients")
            
            # Ensure the table has enough rows allocated
            self.all_patients_table.setRowCount(len(patient_data))
            
            # Populate table with filtered data
            for i, row in patient_data.iterrows():
                row_position = i  # Use the index directly since we pre-allocated rows
                
                # Add each column value in the right order
                for j, col_name in enumerate(display_columns):
                    if col_name in row:
                        # Get value and handle None/NaN values
                        value = row[col_name]
                        
                        if pd.isna(value) or value is None:
                            display_value = ""
                        elif col_name.endswith('_score') and pd.notna(value):
                            try:
                                if value == int(value):
                                    display_value = str(int(value))
                                else:
                                    display_value = f"{value:.1f}"
                            except:
                                display_value = str(value)
                        else:
                            display_value = str(value)
                        
                        # Create table item
                        item = QTableWidgetItem(display_value)
                        
                        # Center numeric columns
                        if col_name in ['age'] or col_name.endswith('_score'):
                            item.setTextAlignment(Qt.AlignCenter)
                        
                        self.all_patients_table.setItem(row_position, j, item)
            
            # Ensure the table updates its display
            self.all_patients_table.resizeRowsToContents()
            self.all_patients_table.viewport().update()
            
            # Update message
            QMessageBox.information(self, "Search Results", f"Found {len(patient_data)} patient(s) matching '{search_text}'.")
            
        except Exception as e:
            print(f"Error searching for patients: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Error searching for patients: {str(e)}")
    
    def download_csv(self):
        try:
            # Open file dialog to select save location
            file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
            
            if file_path:
                # Export from database to CSV
                db.export_patient_data_to_csv(file_path)
                QMessageBox.information(self, "Success", f"CSV file saved to {file_path}")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving CSV file: {str(e)}")
    
    def show_patient_details(self, row, column):
        """Show detailed information for a patient when their row is double-clicked"""
        # Get the patient name from the first column
        patient_name = self.all_patients_table.item(row, 0).text()
        
        try:
            # Get patient data
            patient_data = db.get_patient_by_name(patient_name)
            
            if patient_data.empty:
                QMessageBox.warning(self, "Error", f"Could not find patient details for {patient_name}.")
                return
            
            # Get the first matching patient
            patient = patient_data.iloc[0]
            
            # Create a detail dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Patient Details: {patient_name}")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # Patient info section
            info_group = QGroupBox("Patient Information")
            info_layout = QFormLayout()
            
            info_layout.addRow("ID:", QLabel(str(patient['id'])))
            info_layout.addRow("Name:", QLabel(patient['name']))
            info_layout.addRow("Age:", QLabel(str(patient['age'])))
            info_layout.addRow("Gender:", QLabel(patient['gender']))
            
            info_group.setLayout(info_layout)
            layout.addWidget(info_group)
            
            # Assessment scores section
            scores_group = QGroupBox("Assessment Scores")
            scores_layout = QFormLayout()
            
            scores_layout.addRow("Speech Score:", QLabel(str(patient['speech_score'])))
            scores_layout.addRow("Emoji Score:", QLabel(str(patient['emoji_score'])))
            scores_layout.addRow("Snake Score:", QLabel(str(patient['snake_score'])))
            scores_layout.addRow("Ball Score:", QLabel(str(patient['ball_score'])))
            
            # Calculate average score
            scores = [
                patient['speech_score'], 
                patient['emoji_score'], 
                patient['snake_score'], 
                patient['ball_score']
            ]
            valid_scores = [s for s in scores if pd.notna(s) and s > 0]
            
            if valid_scores:
                avg_score = sum(valid_scores) / len(valid_scores)
                scores_layout.addRow("Average Score:", QLabel(f"{avg_score:.1f}"))
            
            scores_group.setLayout(scores_layout)
            layout.addWidget(scores_group)
            
            # Action buttons
            button_layout = QHBoxLayout()
            
            edit_button = QPushButton("Edit Patient")
            edit_button.clicked.connect(lambda: QMessageBox.information(dialog, "Not Implemented", "Edit patient functionality is not yet implemented."))
            
            delete_button = QPushButton("Delete Patient")
            delete_button.setStyleSheet("background-color: #E74C3C; color: white;")
            delete_button.clicked.connect(lambda: self.delete_patient_confirmation(dialog, patient))
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            
            button_layout.addWidget(edit_button)
            button_layout.addWidget(delete_button)
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            
            # Show dialog
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error showing patient details: {str(e)}")
            
    def delete_patient_confirmation(self, parent_dialog, patient):
        """Show confirmation dialog before deleting a patient"""
        reply = QMessageBox.question(
            parent_dialog,
            "Confirm Deletion",
            f"Are you sure you want to delete patient {patient['name']}?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete the patient
                if db.delete_patient(patient['id']):
                    QMessageBox.information(parent_dialog, "Success", f"Patient {patient['name']} has been deleted.")
                    parent_dialog.accept()  # Close the details dialog
                    self.load_data()  # Refresh the table
                else:
                    QMessageBox.warning(parent_dialog, "Error", "Failed to delete patient.")
            except Exception as e:
                QMessageBox.warning(parent_dialog, "Error", f"Error deleting patient: {str(e)}") 