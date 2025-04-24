from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QLineEdit, QMessageBox, QTabWidget,
                            QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os

class ResultsChartCanvas(FigureCanvas):
    """Simple canvas with a matplotlib figure for displaying score charts"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(ResultsChartCanvas, self).__init__(self.fig)

class ResultUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create header
        header_layout = QVBoxLayout()
        title_label = QLabel("Assessment Results")
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
        
        # Patient selection form
        selection_group = QGroupBox("Select Patient")
        selection_layout = QFormLayout()
        
        # Patient name input
        self.patient_name_input = QLineEdit()
        selection_layout.addRow("Patient Name:", self.patient_name_input)
        
        # View results button
        view_button = QPushButton("View Results")
        view_button.setStyleSheet("background-color: #4682B4; color: white;")
        view_button.clicked.connect(self.load_results)
        selection_layout.addRow("", view_button)
        
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        
        # Summary tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout()
        
        # Patient info
        self.patient_info_label = QLabel("Select a patient to view their information")
        self.patient_info_label.setWordWrap(True)
        self.patient_info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.patient_info_label)
        
        # Summary scores table
        self.scores_table = QTableWidget(4, 2)
        self.scores_table.setHorizontalHeaderLabels(["Test Type", "Score"])
        self.scores_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scores_table.setRowCount(0)  # Clear table initially
        
        summary_layout.addWidget(self.scores_table)
        
        # Overall assessment
        assessment_group = QGroupBox("Overall Assessment")
        assessment_layout = QVBoxLayout()
        
        self.assessment_label = QLabel("Select a patient to view their assessment")
        self.assessment_label.setWordWrap(True)
        self.assessment_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        
        assessment_layout.addWidget(self.assessment_label)
        assessment_group.setLayout(assessment_layout)
        summary_layout.addWidget(assessment_group)
        
        summary_tab.setLayout(summary_layout)
        
        # Visualizations tab
        viz_tab = QWidget()
        viz_layout = QVBoxLayout()
        
        # Add chart canvas
        self.chart_canvas = ResultsChartCanvas(self, width=5, height=4)
        viz_layout.addWidget(self.chart_canvas)
        
        # Add chart type selector
        chart_selector_layout = QHBoxLayout()
        chart_selector_layout.addWidget(QLabel("Chart Type:"))
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Bar Chart", "Line Chart", "Radar Chart"])
        self.chart_type_combo.currentIndexChanged.connect(self.update_chart)
        chart_selector_layout.addWidget(self.chart_type_combo)
        
        viz_layout.addLayout(chart_selector_layout)
        
        viz_tab.setLayout(viz_layout)
        
        # Progress History tab
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        history_label = QLabel("Patient's progress history over time")
        history_layout.addWidget(history_label)
        
        # History table
        self.history_table = QTableWidget(0, 5)  # 0 rows initially, 5 columns
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Speech Score", "Emoji Score", "Snake Score", "Ball Score"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        history_layout.addWidget(self.history_table)
        
        history_tab.setLayout(history_layout)
        
        # Recommendations tab
        recommend_tab = QWidget()
        recommend_layout = QVBoxLayout()
        
        # Recommendations based on results
        self.recommendations_label = QLabel("Select a patient to view their recommendations")
        self.recommendations_label.setWordWrap(True)
        
        recommend_layout.addWidget(self.recommendations_label)
        
        # Placeholder for recommendations content
        recommendations_content = QLabel("Detailed recommendations will appear here")
        recommendations_content.setAlignment(Qt.AlignCenter)
        recommendations_content.setStyleSheet("background-color: #f0f0f0; padding: 20px;")
        recommendations_content.setMinimumHeight(300)
        
        recommend_layout.addWidget(recommendations_content)
        
        recommend_tab.setLayout(recommend_layout)
        
        # Add tabs to tab widget
        self.results_tabs.addTab(summary_tab, "Summary")
        self.results_tabs.addTab(viz_tab, "Visualizations")
        self.results_tabs.addTab(history_tab, "Progress History")
        self.results_tabs.addTab(recommend_tab, "Recommendations")
        
        # Add tabs to main layout
        main_layout.addWidget(self.results_tabs)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        # Create buttons for navigation
        sections = ["Home", "Physio", "Hand", "Game", "Result", "Logout"]
        
        for section in sections:
            button = QPushButton(section)
            button.setStyleSheet("background-color: #4682B4; color: white;")
            # Use a lambda with a default argument to capture the current value of section
            button.clicked.connect(self.create_navigation_handler(section))
            nav_layout.addWidget(button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Initialize with empty chart
        self.update_chart()
    
    def create_navigation_handler(self, section):
        """Create a handler function for navigation buttons to avoid lambda issues"""
        def handler():
            print(f"Navigation button clicked: {section}")
            self.navigate_to_signal.emit(section)
        return handler
    
    def load_results(self):
        # Get patient name
        patient_name = self.patient_name_input.text().strip()
        
        # Validate input
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
            
            # Extract the first matching patient
            patient = patient_data.iloc[0]
            
            # Update patient info label
            self.patient_info_label.setText(
                f"Patient: {patient['name']}\n"
                f"Age: {patient['age']}\n"
                f"Gender: {patient['gender']}"
            )
            
            # Update scores table
            self.scores_table.setRowCount(4)
            
            test_types = ["speech_score", "emoji_score", "snake_score", "ball_score"]
            test_display_names = ["Speech Score", "Emoji Score", "Snake Score", "Ball Score"]
            for i, test in enumerate(test_types):
                self.scores_table.setItem(i, 0, QTableWidgetItem(test_display_names[i]))
                self.scores_table.setItem(i, 1, QTableWidgetItem(str(patient[test])))
            
            # Update assessment
            # Calculate overall score (average of available scores)
            scores = []
            for test in test_types:
                if test in patient and patient[test] is not None and pd.notna(patient[test]):
                    try:
                        scores.append(float(patient[test]))
                    except:
                        pass
            
            if scores:
                avg_score = sum(scores) / len(scores)
                
                # Determine assessment based on average score
                if avg_score >= 80:
                    assessment = "Excellent: Patient shows strong neurological function across all tests."
                elif avg_score >= 60:
                    assessment = "Good: Patient demonstrates adequate neurological function with some areas for improvement."
                elif avg_score >= 40:
                    assessment = "Fair: Patient shows moderate impairment that would benefit from targeted rehabilitation."
                else:
                    assessment = "Needs Improvement: Patient shows significant impairment requiring comprehensive rehabilitation."
                
                self.assessment_label.setText(
                    f"Overall Score: {avg_score:.1f}/100\n\n{assessment}"
                )
            else:
                self.assessment_label.setText("No scores available for assessment")
            
            # Update the chart
            self.update_chart(patient=patient)
            
            # Update recommendations
            self.update_recommendations(patient, scores, test_types)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading results: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_chart(self, patient=None):
        # Clear the plot
        self.chart_canvas.axes.clear()
        
        # If no patient data, show empty chart
        if patient is None:
            self.chart_canvas.axes.text(0.5, 0.5, "No data to display", 
                                     horizontalalignment='center',
                                     verticalalignment='center',
                                     transform=self.chart_canvas.axes.transAxes)
            self.chart_canvas.draw()
            return
        
        # Get test types and scores
        test_types = ["Speech", "Emoji", "Snake", "Ball"]
        db_column_names = ["speech_score", "emoji_score", "snake_score", "ball_score"]
        scores = []
        
        for test in db_column_names:
            if test in patient and pd.notna(patient[test]):
                try:
                    scores.append(float(patient[test]))
                except:
                    scores.append(0)
            else:
                scores.append(0)
        
        # Get chart type
        chart_type = self.chart_type_combo.currentText()
        
        if chart_type == "Bar Chart":
            # Create bar chart
            bars = self.chart_canvas.axes.bar(test_types, scores, color='#3498DB')
            self.chart_canvas.axes.set_ylim(0, 100)
            self.chart_canvas.axes.set_ylabel('Score')
            self.chart_canvas.axes.set_title('Assessment Scores by Test Type')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                self.chart_canvas.axes.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom')
                
        elif chart_type == "Line Chart":
            # Create line chart (with connected points)
            self.chart_canvas.axes.plot(test_types, scores, 'o-', color='#3498DB', linewidth=2, markersize=8)
            self.chart_canvas.axes.set_ylim(0, 100)
            self.chart_canvas.axes.set_ylabel('Score')
            self.chart_canvas.axes.set_title('Assessment Scores Progression')
            
            # Add value labels at points
            for i, score in enumerate(scores):
                self.chart_canvas.axes.text(i, score, f'{score:.0f}', ha='center', va='bottom')
                
        elif chart_type == "Radar Chart":
            # Create radar chart
            # Add first point again to close the polygon
            values = scores + [scores[0]]
            angles = np.linspace(0, 2*np.pi, len(test_types), endpoint=False).tolist()
            angles += angles[:1]  # Close the loop
            
            test_labels = test_types + [test_types[0]]  # Close the loop for labels too
            
            self.chart_canvas.axes.plot(angles, values, 'o-', linewidth=2, color='#3498DB')
            self.chart_canvas.axes.fill(angles, values, alpha=0.25, color='#3498DB')
            self.chart_canvas.axes.set_thetagrids(angles[:-1] * 180/np.pi, test_labels[:-1])
            self.chart_canvas.axes.set_ylim(0, 100)
            self.chart_canvas.axes.set_title('Assessment Scores Radar')
            self.chart_canvas.axes.grid(True)
        
        # Redraw the canvas
        self.chart_canvas.draw()
    
    def update_recommendations(self, patient, scores, test_types):
        # Generate recommendations based on scores
        if not scores:
            self.recommendations_label.setText("No scores available for recommendations")
            return
            
        avg_score = sum(scores) / len(scores)
        
        general_recs = f"Based on the overall assessment score of {avg_score:.1f}, we recommend:\n\n"
        
        if avg_score >= 80:
            general_recs += "- Maintain current abilities with regular practice exercises\n"
            general_recs += "- Continue with preventative exercises to maintain neurological health\n"
            general_recs += "- Periodically reassess to track any changes"
        elif avg_score >= 60:
            general_recs += "- Regular rehabilitation exercises focused on weaker areas\n"
            general_recs += "- Consider increasing frequency of therapy sessions\n"
            general_recs += "- Reassess in 4-6 weeks to track progress"
        elif avg_score >= 40:
            general_recs += "- Implement structured daily rehabilitation exercises\n"
            general_recs += "- Schedule weekly therapy sessions with a specialist\n"
            general_recs += "- Focus on gradual improvement of key motor skills\n"
            general_recs += "- Reassess in 2-3 weeks"
        else:
            general_recs += "- Intensive rehabilitation program with professional supervision\n"
            general_recs += "- Daily guided therapy sessions\n"
            general_recs += "- Consider assistive devices for daily activities\n"
            general_recs += "- Weekly reassessment to monitor progress"
            
        # Add specific recommendations based on individual test scores
        specific_recs = "\n\nSpecific Recommendations by Test:\n\n"
        
        for i, test in enumerate(test_types):
            if i < len(scores):
                score = scores[i]
                if test == "speech_score":
                    if score < 50:
                        specific_recs += "Speech: Focus on speech exercises, consider consultation with speech therapist\n"
                elif test == "emoji_score":
                    if score < 50:
                        specific_recs += "Cognitive: Practice memory and pattern recognition exercises daily\n"
                elif test == "snake_score":
                    if score < 50:
                        specific_recs += "Hand-Eye Coordination: Regular hand-eye coordination exercises recommended\n"
                elif test == "ball_score":
                    if score < 50:
                        specific_recs += "Motor Skills: Focus on fine motor control exercises for hands\n"
        
        self.recommendations_label.setText(general_recs + specific_recs) 