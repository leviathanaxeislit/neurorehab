from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QLineEdit, QMessageBox, QTabWidget,
                            QListWidget, QComboBox, QProgressBar, QSlider, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont
import pandas as pd
import numpy as np
import os
import random
from patient_dropdown import PatientDropdown

class PhysioUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Initialize assessment state variables
        self.assessment_in_progress = False
        self.rom_scores = {
            "Upper Extremity": 0,
            "Lower Extremity": 0,
            "Trunk/Core": 0
        }
        self.assessment_timer = None
        self.current_stage = 0
        self.total_stages = 5
        self.selected_exercises = []
        
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create header
        header_layout = QVBoxLayout()
        title_label = QLabel("Physiotherapy Assessment")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: #07539e;")
        
        # Add divider
        divider = QLabel()
        try:
            pixmap = QPixmap("divider.png")
            divider.setPixmap(pixmap)
        except:
            divider.setText("----------------------------------------------------")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(divider)
        
        # Add header to main layout
        main_layout.addLayout(header_layout)
        
        # Instructions
        instructions_group = QGroupBox("Test Instructions and Purpose")
        instructions_layout = QVBoxLayout()
        
        instructions = [
            "- This module helps assess and plan physiotherapy exercises for neurological rehabilitation.",
            "- Purpose: To create personalized exercise programs based on the patient's specific needs and abilities.",
            "- Tests include range of motion, balance, coordination, and strength assessments."
        ]
        
        for instruction in instructions:
            instruction_label = QLabel(instruction)
            instruction_label.setWordWrap(True)
            if "Purpose" in instruction:
                instruction_label.setStyleSheet("color: orange;")
            instructions_layout.addWidget(instruction_label)
        
        instructions_group.setLayout(instructions_layout)
        main_layout.addWidget(instructions_group)
        
        # Tabs for different assessments
        assessment_tabs = QTabWidget()
        
        # Range of motion tab
        rom_tab = QWidget()
        rom_layout = QVBoxLayout()
        
        rom_form = QFormLayout()
        
        # Replace patient name input with patient dropdown
        self.patient_dropdown = PatientDropdown(self)
        self.patient_dropdown.patient_selected.connect(self.on_patient_selected)
        rom_form.addRow("", self.patient_dropdown)
        
        self.assessment_type = QComboBox()
        self.assessment_type.addItems(["Upper Extremity", "Lower Extremity", "Trunk/Core", "Comprehensive"])
        rom_form.addRow("Assessment Type:", self.assessment_type)
        
        start_button = QPushButton("Start Assessment")
        start_button.setStyleSheet("background-color: #4682B4; color: white;")
        start_button.clicked.connect(self.start_assessment)
        rom_form.addRow("", start_button)
        
        rom_layout.addLayout(rom_form)
        
        # Assessment area
        self.assessment_area = QFrame()
        self.assessment_area.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")
        self.assessment_area.setMinimumHeight(300)
        assessment_area_layout = QVBoxLayout(self.assessment_area)
        
        # Assessment title
        self.assessment_title = QLabel("Range of Motion Assessment")
        self.assessment_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.assessment_title.setAlignment(Qt.AlignCenter)
        self.assessment_title.setVisible(False)
        assessment_area_layout.addWidget(self.assessment_title)
        
        # Assessment instructions
        self.assessment_instructions = QLabel("Please follow the instructions for each movement.")
        self.assessment_instructions.setWordWrap(True)
        self.assessment_instructions.setStyleSheet("color: #3498DB; font-size: 12pt;")
        self.assessment_instructions.setVisible(False)
        assessment_area_layout.addWidget(self.assessment_instructions)
        
        # Current assessment prompt
        self.current_assessment = QLabel("Not started")
        self.current_assessment.setWordWrap(True)
        self.current_assessment.setStyleSheet("font-size: 14pt; margin: 10px 0;")
        self.current_assessment.setVisible(False)
        assessment_area_layout.addWidget(self.current_assessment)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: #FFFFFF;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2ECC71;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setVisible(False)
        assessment_area_layout.addWidget(self.progress_bar)
        
        # Slider for patient rating
        self.rating_label = QLabel("Rate your range of motion (0-100%):")
        self.rating_label.setVisible(False)
        assessment_area_layout.addWidget(self.rating_label)
        
        self.rating_slider = QSlider(Qt.Horizontal)
        self.rating_slider.setRange(0, 100)
        self.rating_slider.setValue(50)
        self.rating_slider.setTickPosition(QSlider.TicksBelow)
        self.rating_slider.setTickInterval(10)
        self.rating_slider.setVisible(False)
        assessment_area_layout.addWidget(self.rating_slider)
        
        self.rating_value = QLabel("50%")
        self.rating_value.setAlignment(Qt.AlignCenter)
        self.rating_value.setVisible(False)
        assessment_area_layout.addWidget(self.rating_value)
        
        # Connect slider to update label
        self.rating_slider.valueChanged.connect(self.update_rating_label)
        
        # Next button
        self.next_button = QPushButton("Next")
        self.next_button.setStyleSheet("background-color: #2ECC71; color: white; padding: 8px 16px;")
        self.next_button.clicked.connect(self.next_assessment_stage)
        self.next_button.setVisible(False)
        assessment_area_layout.addWidget(self.next_button)
        
        # Results area
        self.results_area = QLabel("Assessment results will appear here")
        self.results_area.setWordWrap(True)
        self.results_area.setAlignment(Qt.AlignCenter)
        self.results_area.setStyleSheet("margin-top: 20px;")
        self.results_area.setVisible(False)
        assessment_area_layout.addWidget(self.results_area)
        
        # Add placeholder text when assessment not started
        self.placeholder_label = QLabel("Assessment interface will appear here when started")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        assessment_area_layout.addWidget(self.placeholder_label)
        
        rom_layout.addWidget(self.assessment_area)
        rom_tab.setLayout(rom_layout)
        
        # Exercise prescription tab
        exercise_tab = QWidget()
        exercise_layout = QVBoxLayout()
        
        exercise_label = QLabel("Select exercises to include in the patient's rehabilitation program:")
        exercise_layout.addWidget(exercise_label)
        
        self.exercise_list = QListWidget()
        self.exercise_list.setSelectionMode(QListWidget.MultiSelection)
        exercises = [
            "Shoulder Flexion and Extension",
            "Knee Strengthening",
            "Ankle Mobility",
            "Coordination Exercises",
            "Balance Training",
            "Gait Training",
            "Fine Motor Skills",
            "Core Stability Exercises"
        ]
        
        for exercise in exercises:
            self.exercise_list.addItem(exercise)
            
        exercise_layout.addWidget(self.exercise_list)
        
        create_program_button = QPushButton("Create Exercise Program")
        create_program_button.setStyleSheet("background-color: #4682B4; color: white;")
        create_program_button.clicked.connect(self.create_program)
        exercise_layout.addWidget(create_program_button)
        
        # Program results area
        self.program_results = QLabel("Your prescribed exercise program will appear here")
        self.program_results.setWordWrap(True)
        self.program_results.setStyleSheet("background-color: #f0f0f0; padding: 15px; margin-top: 10px;")
        self.program_results.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.program_results.setMinimumHeight(200)
        exercise_layout.addWidget(self.program_results)
        
        exercise_tab.setLayout(exercise_layout)
        
        # Progress tracking tab
        progress_tab = QWidget()
        progress_layout = QVBoxLayout()
        
        progress_label = QLabel("This section allows you to track patient progress over time.")
        progress_label.setWordWrap(True)
        progress_layout.addWidget(progress_label)
        
        # Patient selection
        patient_form = QFormLayout()
        
        self.progress_patient_input = QLineEdit()
        patient_form.addRow("Patient Name:", self.progress_patient_input)
        
        load_button = QPushButton("Load Progress Data")
        load_button.setStyleSheet("background-color: #4682B4; color: white;")
        load_button.clicked.connect(self.load_patient_progress)
        patient_form.addRow("", load_button)
        
        progress_layout.addLayout(patient_form)
        
        # Progress visualization
        self.progress_display = QLabel("Patient progress data will be shown here")
        self.progress_display.setAlignment(Qt.AlignCenter)
        self.progress_display.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")
        self.progress_display.setMinimumHeight(300)
        progress_layout.addWidget(self.progress_display)
        
        progress_tab.setLayout(progress_layout)
        
        # Add tabs to tab widget
        assessment_tabs.addTab(rom_tab, "Assessment")
        assessment_tabs.addTab(exercise_tab, "Exercise Prescription")
        assessment_tabs.addTab(progress_tab, "Progress Tracking")
        
        # Add tabs to main layout
        main_layout.addWidget(assessment_tabs)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        # Create buttons for navigation
        sections = ["Home", "Physio", "Hand", "Game", "Result", "Logout"]
        
        for section in sections:
            button = QPushButton(section)
            button.setStyleSheet("background-color: #4682B4; color: white;")
            # Fix lambda by using a custom slot to avoid closure issues
            button.clicked.connect(self.create_navigation_handler(section))
            nav_layout.addWidget(button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def update_rating_label(self, value):
        """Update the rating label when slider changes"""
        self.rating_value.setText(f"{value}%")
    
    def on_patient_selected(self, patient_id, patient_name):
        """Handle when a patient is selected from the dropdown"""
        print(f"Patient selected: {patient_name} (ID: {patient_id})")
        # Store the selected patient ID for later use
        self.selected_patient_id = patient_id
        self.selected_patient_name = patient_name
    
    def start_assessment(self):
        # Get patient ID from dropdown instead of name from input
        if not hasattr(self, 'selected_patient_id') or self.selected_patient_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a patient first.")
            return
        
        patient_name = self.selected_patient_name
        
        # Initialize assessment variables
        self.assessment_type_value = self.assessment_type.currentText()
        self.current_stage = 0
        self.total_stages = 5
        self.assessment_in_progress = True
        
        # Reset scores
        self.rom_scores = {
            "Upper Extremity": 0,
            "Lower Extremity": 0,
            "Trunk/Core": 0
        }
        
        # Show assessment interface
        self.placeholder_label.setVisible(False)
        self.assessment_title.setVisible(True)
        self.assessment_instructions.setVisible(True)
        self.current_assessment.setVisible(True)
        self.progress_bar.setVisible(True)
        self.rating_label.setVisible(True)
        self.rating_slider.setVisible(True)
        self.rating_value.setVisible(True)
        self.next_button.setVisible(True)
        
        # Start the assessment
        self.next_assessment_stage()
    
    def next_assessment_stage(self):
        """Proceed to the next assessment stage"""
        # If not the first stage, record the current rating
        if self.current_stage > 0:
            category = self.get_category_for_stage(self.current_stage - 1)
            if category in self.rom_scores:
                value = self.rating_slider.value()
                self.rom_scores[category] += value
                
        # Check if assessment is complete
        if self.current_stage >= self.total_stages:
            self.complete_assessment()
            return
        
        # Update stage
        self.progress_bar.setValue(int((self.current_stage / self.total_stages) * 100))
        
        # Update prompts based on assessment type
        if self.assessment_type_value == "Upper Extremity":
            prompts = [
                "Raise your arms forward as far as you can",
                "Raise your arms to the side as far as you can",
                "Bend your elbows and touch your shoulders",
                "Rotate your wrists in circular motions",
                "Make a fist and then fully extend your fingers"
            ]
            self.assessment_title.setText("Upper Extremity Range of Motion Assessment")
            
        elif self.assessment_type_value == "Lower Extremity":
            prompts = [
                "Sit on a chair and extend one knee at a time",
                "While seated, point your toes up then down",
                "While standing, rise up on your toes, then lower",
                "While standing, bend your knees as if sitting",
                "Lie down and lift one leg at a time"
            ]
            self.assessment_title.setText("Lower Extremity Range of Motion Assessment")
            
        elif self.assessment_type_value == "Trunk/Core":
            prompts = [
                "Stand and bend forward as far as comfortable",
                "Stand and bend to each side",
                "Stand and rotate your torso to each side",
                "Sit on floor with legs extended and reach for toes",
                "Lie on back and do a partial sit-up"
            ]
            self.assessment_title.setText("Trunk/Core Range of Motion Assessment")
            
        else:  # Comprehensive
            all_prompts = [
                # Upper
                "Raise your arms forward as far as you can",
                "Rotate your shoulders in circular motions",
                # Lower
                "While standing, rise up on your toes, then lower",
                "While standing, bend your knees as if sitting",
                # Trunk
                "Stand and bend to each side"
            ]
            prompts = all_prompts
            self.assessment_title.setText("Comprehensive Range of Motion Assessment")
        
        # Set the current prompt
        self.current_assessment.setText(f"{self.current_stage + 1}. {prompts[self.current_stage]}")
        
        # Update button text for the last stage
        if self.current_stage == self.total_stages - 1:
            self.next_button.setText("Complete Assessment")
        else:
            self.next_button.setText("Next")
            
        # Reset slider to middle position
        self.rating_slider.setValue(50)
        
        # Increment stage counter
        self.current_stage += 1
    
    def get_category_for_stage(self, stage):
        """Determine which category to score based on the assessment type and stage"""
        if self.assessment_type_value == "Upper Extremity":
            return "Upper Extremity"
        elif self.assessment_type_value == "Lower Extremity":
            return "Lower Extremity"
        elif self.assessment_type_value == "Trunk/Core":
            return "Trunk/Core"
        else:  # Comprehensive
            # Map stages to categories for comprehensive assessment
            if stage < 2:
                return "Upper Extremity"
            elif stage < 4:
                return "Lower Extremity"
            else:
                return "Trunk/Core"
    
    def complete_assessment(self):
        """Complete the assessment and display results"""
        # Update UI
        self.assessment_title.setText("Assessment Complete")
        self.current_assessment.setVisible(False)
        self.progress_bar.setValue(100)
        self.rating_label.setVisible(False)
        self.rating_slider.setVisible(False)
        self.rating_value.setVisible(False)
        self.next_button.setVisible(False)
        
        # Calculate average scores and normalize to 0-100 scale
        for category in self.rom_scores:
            # Determine how many assessments were done for this category
            if self.assessment_type_value == category:
                divisor = self.total_stages
            elif self.assessment_type_value == "Comprehensive":
                if category == "Upper Extremity":
                    divisor = 2
                elif category == "Lower Extremity":
                    divisor = 2
                else:
                    divisor = 1
            else:
                divisor = 1
                
            # Calculate average if divisor is not zero
            if divisor > 0:
                self.rom_scores[category] = round(self.rom_scores[category] / divisor)
            
        # Create results text
        results = "Assessment Results:\n\n"
        
        if self.assessment_type_value == "Comprehensive" or self.assessment_type_value == "Upper Extremity":
            results += f"Upper Extremity: {self.rom_scores['Upper Extremity']}%\n"
            
        if self.assessment_type_value == "Comprehensive" or self.assessment_type_value == "Lower Extremity":
            results += f"Lower Extremity: {self.rom_scores['Lower Extremity']}%\n"
            
        if self.assessment_type_value == "Comprehensive" or self.assessment_type_value == "Trunk/Core":
            results += f"Trunk/Core: {self.rom_scores['Trunk/Core']}%\n"
        
        # Add recommendations
        results += "\nRecommendations:\n"
        
        # Upper Extremity recommendations
        if self.assessment_type_value == "Comprehensive" or self.assessment_type_value == "Upper Extremity":
            score = self.rom_scores["Upper Extremity"]
            if score < 30:
                results += "- Focus on passive range of motion exercises for arms and shoulders\n"
                results += "- Consider water therapy for reduced gravity assistance\n"
            elif score < 70:
                results += "- Continue with active-assisted upper body exercises\n"
                results += "- Add light resistance training when comfortable\n"
            else:
                results += "- Progress to functional movement patterns for upper body\n"
                results += "- Consider adding task-specific training\n"
        
        # Lower Extremity recommendations
        if self.assessment_type_value == "Comprehensive" or self.assessment_type_value == "Lower Extremity":
            score = self.rom_scores["Lower Extremity"]
            if score < 30:
                results += "- Begin with seated exercises and passive ankle/knee movements\n"
                results += "- Use assistive devices for weight-bearing activities\n"
            elif score < 70:
                results += "- Incorporate standing exercises with support as tolerated\n"
                results += "- Add balance activities in parallel bars\n"
            else:
                results += "- Progress to functional gait training\n"
                results += "- Add stair climbing and uneven surface training\n"
        
        # Trunk/Core recommendations
        if self.assessment_type_value == "Comprehensive" or self.assessment_type_value == "Trunk/Core":
            score = self.rom_scores["Trunk/Core"]
            if score < 30:
                results += "- Focus on basic core activation exercises in supported positions\n"
                results += "- Include gentle rotation exercises in seated position\n"
            elif score < 70:
                results += "- Add dynamic stability exercises for trunk\n"
                results += "- Include standing weight shifts and gentle bending activities\n"
            else:
                results += "- Progress to more challenging core exercises\n"
                results += "- Add functional movements combining trunk with limb movements\n"
        
        # Show results
        self.results_area.setText(results)
        self.results_area.setVisible(True)
        
        # Save assessment data
        self.save_assessment_data(patient_name)
        
        # Reset assessment state
        self.assessment_in_progress = False
    
    def save_assessment_data(self, patient_name):
        """Save assessment data to the database"""
        try:
            from db_utils import db
            
            # Use patient ID instead of searching by name
            patient_id = self.selected_patient_id
            
            # Calculate total score as average of all category scores
            total_score = sum(self.rom_scores.values()) / len(self.rom_scores)
            
            # Update the patient's physio score in the database
            db.update_assessment_score(patient_id, "Physio", total_score)
            
            # Record details for each category
            for category, score in self.rom_scores.items():
                detail = f"{category} ROM Assessment: {score}%"
                # Add more detailed assessment record
                db.update_detailed_assessment(patient_id, "Physio", score, detail, category)
            
            QMessageBox.information(self, "Success", f"Assessment data saved successfully for {patient_name}")
            
        except Exception as e:
            print(f"Error saving assessment data: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to save assessment data: {str(e)}")
    
    def create_program(self):
        """Create an exercise program based on selected exercises"""
        # Get selected exercises
        selected_items = self.exercise_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Exercises Selected", "Please select at least one exercise.")
            return
        
        self.selected_exercises = [item.text() for item in selected_items]
        
        # Generate exercise program
        program_text = "PERSONALIZED EXERCISE PROGRAM\n\n"
        
        for i, exercise in enumerate(self.selected_exercises, 1):
            program_text += f"{i}. {exercise}\n"
            
            # Add specific instructions for each exercise
            if "Shoulder" in exercise:
                program_text += "   • Stand with feet shoulder-width apart\n"
                program_text += "   • Slowly raise arms forward/sideways as far as comfortable\n"
                program_text += "   • Hold for 5 seconds, then slowly lower\n"
                program_text += "   • Repeat 10 times, 3 sets\n"
            elif "Knee" in exercise:
                program_text += "   • Sit on chair with back supported\n"
                program_text += "   • Slowly extend one knee until leg is straight\n"
                program_text += "   • Hold for 5 seconds, then slowly lower\n"
                program_text += "   • Repeat 10 times for each leg, 3 sets\n"
            elif "Ankle" in exercise:
                program_text += "   • Sit with feet flat on floor\n"
                program_text += "   • Slowly raise toes up while keeping heels on floor\n"
                program_text += "   • Then point toes down\n"
                program_text += "   • Repeat 15 times, 2 sets\n"
            elif "Coordination" in exercise:
                program_text += "   • Seated, place objects of varying sizes on table\n"
                program_text += "   • Practice picking up and placing in a container\n"
                program_text += "   • Practice 5-10 minutes daily\n"
            elif "Balance" in exercise:
                program_text += "   • Stand near countertop for support if needed\n"
                program_text += "   • Practice standing on one foot for 30 seconds\n"
                program_text += "   • Repeat 5 times for each foot\n"
            elif "Gait" in exercise:
                program_text += "   • Walk in a straight line with normal stride length\n"
                program_text += "   • Focus on heel-to-toe pattern\n"
                program_text += "   • Practice for 10 minutes, 3 times daily\n"
            elif "Fine Motor" in exercise:
                program_text += "   • Practice buttoning/unbuttoning a shirt\n"
                program_text += "   • Alternate fingers touching thumb\n"
                program_text += "   • Practice writing or drawing for 5 minutes\n"
            elif "Core" in exercise:
                program_text += "   • Lie on back with knees bent, feet flat\n"
                program_text += "   • Tighten abdominal muscles and lift head/shoulders\n"
                program_text += "   • Hold for 5 seconds, then slowly lower\n"
                program_text += "   • Repeat 10 times, 3 sets\n"
            
            program_text += "\n"
            
        # Add general guidelines
        program_text += "\nGENERAL GUIDELINES:\n"
        program_text += "• Start with 1 set and gradually progress\n"
        program_text += "• Stop if you experience pain (not discomfort)\n"
        program_text += "• Maintain proper breathing throughout exercises\n"
        program_text += "• Perform exercises 3-5 times weekly\n"
        
        # Update program results display
        self.program_results.setText(program_text)
        
        # Show message
        QMessageBox.information(self, "Program Created", 
                            f"Exercise program created with {len(self.selected_exercises)} exercises.")
    
    def load_patient_progress(self):
        """Load and display patient progress data"""
        # Get patient name
        patient_name = self.progress_patient_input.text().strip()
        
        if not patient_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a patient name.")
            return
            
        try:
            # Import the database utility
            from db_utils import db
            
            # Get patient data from database matching the name
            patient_data = db.get_patient_by_name(patient_name)
            
            if patient_data.empty:
                QMessageBox.warning(self, "Patient Not Found", f"No patient found with name containing '{patient_name}'.")
                return
                
            # Get first matching patient
            patient = patient_data.iloc[0]
            
            # Create progress report
            progress_text = f"<h3>Progress Report for {patient['name']}</h3>"
            progress_text += f"<p><b>Age:</b> {patient['age']}</p>"
            progress_text += f"<p><b>Gender:</b> {patient['gender']}</p>"
            
            # Function to generate random progress data
            def generate_progress_data():
                initial = random.randint(30, 50)
                progress = []
                for i in range(5):
                    value = initial + i * random.randint(5, 10)
                    value = min(value, 100)  # Cap at 100
                    progress.append(value)
                return progress
                
            # Example progress data (would be loaded from a database in a real app)
            upper_extremity_progress = generate_progress_data()
            lower_extremity_progress = generate_progress_data()
            trunk_core_progress = generate_progress_data()
            
            # Create progress bars
            progress_text += "<h4>Upper Extremity Progress</h4>"
            for i, value in enumerate(upper_extremity_progress):
                progress_text += f"<p>Week {i+1}: <meter value='{value}' min='0' max='100'></meter> {value}%</p>"
                
            progress_text += "<h4>Lower Extremity Progress</h4>"
            for i, value in enumerate(lower_extremity_progress):
                progress_text += f"<p>Week {i+1}: <meter value='{value}' min='0' max='100'></meter> {value}%</p>"
                
            progress_text += "<h4>Trunk/Core Progress</h4>"
            for i, value in enumerate(trunk_core_progress):
                progress_text += f"<p>Week {i+1}: <meter value='{value}' min='0' max='100'></meter> {value}%</p>"
                
            # Add projected goals
            progress_text += "<h4>Projected Goals</h4>"
            
            # Calculate latest values from progress data
            latest_upper = upper_extremity_progress[-1]
            latest_lower = lower_extremity_progress[-1]
            latest_trunk = trunk_core_progress[-1]
            
            # Calculate goal values (aim for 5-10% improvement)
            goal_upper = min(100, latest_upper + random.randint(5, 10))
            goal_lower = min(100, latest_lower + random.randint(5, 10))
            goal_trunk = min(100, latest_trunk + random.randint(5, 10))
            
            # Add goals with projected timeframe
            weeks_to_goal = random.randint(2, 4)
            progress_text += f"<p>Upper Extremity: {latest_upper}% → {goal_upper}% (in {weeks_to_goal} weeks)</p>"
            progress_text += f"<p>Lower Extremity: {latest_lower}% → {goal_lower}% (in {weeks_to_goal} weeks)</p>"
            progress_text += f"<p>Trunk/Core: {latest_trunk}% → {goal_trunk}% (in {weeks_to_goal} weeks)</p>"
            
            # Set the HTML content
            self.progress_display.setText(progress_text)
            self.progress_display.setTextFormat(Qt.RichText)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading progress data: {str(e)}")
    
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler 