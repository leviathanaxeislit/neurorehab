from PyQt5.QtWidgets import QComboBox, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt

class PatientDropdown(QWidget):
    """
    A reusable patient dropdown component for the NeuroWell application.
    Emits a signal when a patient is selected.
    """
    patient_selected = pyqtSignal(int, str)  # patientId, patientName
    
    def __init__(self, parent=None, label_text="Select Patient:", show_label=True):
        super().__init__(parent)
        self.init_ui(label_text, show_label)
        self.load_patients()
        
    def init_ui(self, label_text, show_label):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if show_label:
            self.label = QLabel(label_text)
            layout.addWidget(self.label)
        
        self.patient_combo = QComboBox()
        self.patient_combo.setMinimumWidth(200)
        self.patient_combo.setStyleSheet("""
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
        """)
        self.patient_combo.currentIndexChanged.connect(self.on_patient_selected)
        
        layout.addWidget(self.patient_combo)
        layout.setStretch(1 if show_label else 0, 1)  # Make the combobox stretch
    
    def load_patients(self):
        """Load patients from the database"""
        try:
            from db_utils import db
            
            # Get all patients
            df = db.get_all_patients()
            
            # Clear current items
            self.patient_combo.clear()
            
            # Add a default option
            self.patient_combo.addItem("-- Select Patient --", -1)
            
            # Add each patient to the dropdown
            for _, row in df.iterrows():
                self.patient_combo.addItem(f"{row['name']} (ID: {row['id']})", row['id'])
            
        except Exception as e:
            print(f"Error loading patients into dropdown: {str(e)}")
    
    def on_patient_selected(self, index):
        """Handle patient selection"""
        if index <= 0:  # Skip the default option
            return
            
        # Get the patient ID from the selected item's data
        patient_id = self.patient_combo.itemData(index)
        
        # Get the patient name from the selected item's text
        patient_text = self.patient_combo.itemText(index)
        patient_name = patient_text.split(" (ID:")[0]  # Extract just the name part
        
        # Emit the signal with the patient ID and name
        self.patient_selected.emit(patient_id, patient_name)
    
    def set_patient(self, patient_id):
        """Set the dropdown to a specific patient by ID"""
        for i in range(self.patient_combo.count()):
            if self.patient_combo.itemData(i) == patient_id:
                self.patient_combo.setCurrentIndex(i)
                break
    
    def get_selected_patient_id(self):
        """Get the currently selected patient ID"""
        index = self.patient_combo.currentIndex()
        if index <= 0:
            return None
        return self.patient_combo.itemData(index)
    
    def refresh(self):
        """Refresh the patient list"""
        current_id = self.get_selected_patient_id()
        self.load_patients()
        if current_id is not None:
            self.set_patient(current_id) 