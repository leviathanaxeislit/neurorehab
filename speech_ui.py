import os
import pandas as pd
import time
import numpy as np
import sounddevice as sd
import wave
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import speech_recognition as sr
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QGroupBox, QFormLayout, QLineEdit, QMessageBox, QFrame, 
                            QScrollArea, QSizePolicy, QProgressBar, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont
import re

# Constants
SAMPLE_RATE = 44100  # Hz
RECORD_DURATION = 5  # seconds

class AudioRecorder(threading.Thread):
    def __init__(self, duration=RECORD_DURATION, sample_rate=SAMPLE_RATE):
        super().__init__()
        self.duration = duration
        self.sample_rate = sample_rate
        self.recording = None
        self._stop_event = threading.Event()
        self.callback_finished = None
        self.filepath = None
        
    def run(self):
        try:
            # Validate filepath before recording
            if not self.filepath:
                print("Error: No filepath specified before starting recording")
                return
                
            # Ensure directory exists
            dir_path = os.path.dirname(self.filepath)
            if not os.path.exists(dir_path):
                print(f"Creating directory: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
            
            # Print audio device info for debugging
            print("Audio device info:")
            try:
                devices = sd.query_devices()
                print(f"Available audio devices: {devices}")
                print(f"Default input device: {sd.default.device[0]}")
            except Exception as e:
                print(f"Error querying audio devices: {e}")
            
            print(f"Starting recording to {self.filepath}...")
            print(f"Duration: {self.duration}s, Sample rate: {self.sample_rate}Hz")
            
            # Create a blocking stream for more reliable recording
            try:
                frames = []
                # Calculate total frames needed
                total_frames = int(self.duration * self.sample_rate)
                
                # Define callback function for the stream
                def callback(indata, frames_to_record, time_info, status):
                    if status:
                        print(f"Audio input status: {status}")
                    if self._stop_event.is_set():
                        raise sd.CallbackAbort
                    frames.append(indata.copy())
                
                # Open the stream
                with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                                   callback=callback, dtype='int16'):
                    print("Recording in progress...")
                    # Wait for the specified duration
                    sd.sleep(int(self.duration * 1000))
                    print("Recording sleep period completed")
                
                # Skip saving if stopped manually
                if self._stop_event.is_set():
                    print("Recording stopped manually")
                    return
                
                # Convert frames to a single array
                if frames:
                    self.recording = np.concatenate(frames, axis=0)
                    print(f"Captured audio data: shape={self.recording.shape}, type={type(self.recording)}")
                    
                    if len(self.recording) == 0:
                        print("Error: No audio data captured")
                        return
                    
                    # Save to WAV file
                    try:
                        with wave.open(self.filepath, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)  # 16-bit
                            wf.setframerate(self.sample_rate)
                            wf.writeframes(self.recording.tobytes())
                        print(f"Audio saved to {self.filepath}")
                        
                        # Call callback when finished
                        if self.callback_finished and not self._stop_event.is_set():
                            self.callback_finished(self.filepath)
                    except Exception as e:
                        print(f"Error saving audio file: {e}")
                else:
                    print("Error: No audio frames were captured")
            except Exception as e:
                print(f"Error during recording stream: {e}")
                        
        except Exception as e:
            print(f"Error in recording thread: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self):
        print("Stopping audio recorder...")
        self._stop_event.set()
        # Try to force stop recording if it's still going
        try:
            sd.stop()
        except Exception as e:
            print(f"Error stopping sounddevice: {e}")

class WaveformCanvas(FigureCanvas):
    """Canvas to display audio waveform"""
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Amplitude')
        self.axes.set_title('Audio Waveform')
        self.fig.tight_layout()
        
    def plot_waveform(self, audio_data=None, sample_rate=SAMPLE_RATE):
        self.axes.clear()
        
        if audio_data is not None:
            time_array = np.arange(0, len(audio_data)) / sample_rate
            self.axes.plot(time_array, audio_data, color='blue')
            self.axes.set_xlim(0, len(audio_data) / sample_rate)
            
            # Set y limits with some padding
            max_amp = max(abs(audio_data.max()), abs(audio_data.min()))
            self.axes.set_ylim(-max_amp * 1.1, max_amp * 1.1)
        else:
            # Empty plot
            self.axes.text(0.5, 0.5, "No recorded audio", 
                          horizontalalignment='center', verticalalignment='center', 
                          transform=self.axes.transAxes)
        
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Amplitude')
        self.axes.set_title('Audio Waveform')
        self.fig.tight_layout()
        self.draw()

class SpeechUI(QWidget):
    # Signal for navigation
    navigate_to_signal = pyqtSignal(str)
    
    # Signal for speech recognition updates
    recognition_signal = pyqtSignal(str)
    recognition_complete_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize attributes first before UI setup
        self.parent = parent
        self.audio_recorder = None
        self.recognition_thread = None
        self.recording_in_progress = False
        self.patient_name = ""
        self.score = 0
        self.recorded_audio_path = None
        self.recording_timer = None
        self.speech_prompts = [
            "The quick brown fox jumps over the lazy dog",
            "She sells seashells by the seashore",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood",
            "Peter Piper picked a peck of pickled peppers",
            "Red lorry, yellow lorry"
        ]
        self.current_prompt = ""
        self.start_button = None
        self.record_button = None
        
        # Connect signals to slots
        self.recognition_signal.connect(self.update_recognition_result)
        self.recognition_complete_signal.connect(self.on_recognition_complete)
        
        # Now initialize the UI
        self.init_ui()
    
    def init_ui(self):
        # Debug print to track initialization
        print("Initializing SpeechUI interface...")
        
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
        user_info = QLabel("Speech Assessment")
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
        
        # Setup area
        setup_container = QFrame()
        setup_container.setObjectName("dashboard_widget")
        setup_layout = QVBoxLayout(setup_container)
        
        setup_title = QLabel("Speech Assessment Setup")
        setup_title.setObjectName("dashboard_title")
        setup_layout.addWidget(setup_title)
        
        # Form for patient name and difficulty
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Enter patient name")
        form_layout.addRow("Patient Name:", self.patient_name_input)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.currentIndexChanged.connect(self.update_prompt)
        form_layout.addRow("Difficulty:", self.difficulty_combo)
        
        setup_layout.addLayout(form_layout)
        
        # Start button
        print("Creating start button...")
        self.start_button = QPushButton("Start Assessment")
        self.start_button.setObjectName("success")
        self.start_button.setStyleSheet("""
            background-color: #2ECC71;
            font-size: 12pt;
            padding: 10px;
        """)
        self.start_button.clicked.connect(self.start_assessment)
        setup_layout.addWidget(self.start_button)
        print(f"Start button created and configured: {self.start_button}")
        
        content_layout.addWidget(setup_container)
        
        # Speech assessment display area (initially hidden)
        self.assessment_container = QFrame()
        self.assessment_container.setObjectName("dashboard_widget")
        assessment_layout = QVBoxLayout(self.assessment_container)
        
        # Status label
        self.status_label = QLabel("Status: Waiting to start")
        self.status_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        assessment_layout.addWidget(self.status_label)
        
        # Score label
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        assessment_layout.addWidget(self.score_label)
        
        # Speech prompt area
        prompt_group = QGroupBox("Read the following text:")
        prompt_layout = QVBoxLayout()
        
        self.prompt_label = QLabel("Press Start to begin the assessment")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setStyleSheet("""
            font-size: 16pt;
            padding: 20px;
            background-color: #ECF0F1;
            border-radius: 5px;
        """)
        self.prompt_label.setAlignment(Qt.AlignCenter)
        
        prompt_layout.addWidget(self.prompt_label)
        prompt_group.setLayout(prompt_layout)
        assessment_layout.addWidget(prompt_group)
        
        # Recording controls
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        
        # Timer progress
        self.timer_progress = QProgressBar()
        self.timer_progress.setRange(0, 100)
        self.timer_progress.setValue(0)
        recording_layout.addWidget(self.timer_progress)
        
        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setStyleSheet("""
            background-color: #E74C3C;
            color: white;
            font-size: 12pt;
            padding: 10px;
        """)
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setEnabled(False)
        recording_layout.addWidget(self.record_button)
        
        recording_group.setLayout(recording_layout)
        assessment_layout.addWidget(recording_group)
        
        # Waveform display
        waveform_group = QGroupBox("Audio Waveform")
        waveform_layout = QVBoxLayout()
        
        self.waveform_canvas = WaveformCanvas(self, width=5, height=3)
        waveform_layout.addWidget(self.waveform_canvas)
        
        waveform_group.setLayout(waveform_layout)
        assessment_layout.addWidget(waveform_group)
        
        # Recognition result
        result_group = QGroupBox("Recognition Result")
        result_layout = QVBoxLayout()
        
        self.recognition_label = QLabel("No speech recognized yet")
        self.recognition_label.setWordWrap(True)
        self.recognition_label.setStyleSheet("""
            padding: 10px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            min-height: 60px;
        """)
        
        result_layout.addWidget(self.recognition_label)
        
        # Similarity score display
        self.similarity_label = QLabel("Similarity: 0%")
        self.similarity_label.setAlignment(Qt.AlignCenter)
        self.similarity_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-top: 10px;")
        result_layout.addWidget(self.similarity_label)
        
        # Next prompt button
        self.next_prompt_button = QPushButton("Next Prompt")
        self.next_prompt_button.setStyleSheet("""
            background-color: #3498DB;
            color: white;
            font-size: 12pt;
            padding: 10px;
        """)
        self.next_prompt_button.clicked.connect(self.next_prompt)
        self.next_prompt_button.setEnabled(False)
        result_layout.addWidget(self.next_prompt_button)
        
        result_group.setLayout(result_layout)
        assessment_layout.addWidget(result_group)
        
        # Hide assessment container initially
        self.assessment_container.setVisible(False)
        content_layout.addWidget(self.assessment_container)
        
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
    
    def update_prompt(self):
        """Update the current prompt based on the selected difficulty"""
        difficulty = self.difficulty_combo.currentText()
        
        if difficulty == "Easy":
            # Shorter, simpler phrases
            self.speech_prompts = [
                "The quick brown fox jumps over the lazy dog",
                "She sells seashells by the seashore",
                "Today is a beautiful day",
                "Hello, how are you doing today?",
                "I would like a glass of water please"
            ]
        elif difficulty == "Medium":
            # Medium complexity
            self.speech_prompts = [
                "How much wood would a woodchuck chuck if a woodchuck could chuck wood",
                "Peter Piper picked a peck of pickled peppers",
                "Red lorry, yellow lorry",
                "The rain in Spain stays mainly in the plain",
                "Unique New York, unique New York, you know you need unique New York"
            ]
        else:  # Hard
            # Complex phrases and sentences
            self.speech_prompts = [
                "Six slick slim sycamore saplings",
                "The sixth sick sheikh's sixth sheep is sick",
                "To sit in solemn silence in a dull, dark dock in a pestilential prison with a lifelong lock",
                "Round the rugged rock, the ragged rascal ran",
                "Three free throws for the three free throwers"
            ]
        
        # Shuffle prompts order to avoid predictability
        import random
        random.shuffle(self.speech_prompts)
        
        # Update the display if assessment is running
        if hasattr(self, 'prompt_label') and self.assessment_container.isVisible():
            self.current_prompt = self.speech_prompts[0]
            self.prompt_label.setText(self.current_prompt)
    
    def start_assessment(self):
        """Start or restart the speech assessment"""
        # Debug information
        print(f"Start assessment called. Button state: {self.start_button}")
        
        # Get patient name
        self.patient_name = self.patient_name_input.text().strip()
        
        # Validate input
        if not self.patient_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a patient name.")
            return
        
        # More debug info
        print(f"Patient name: {self.patient_name}")
        
        # Reset assessment state
        self.score = 0
        self.score_label.setText(f"Score: {self.score}")
        self.status_label.setText("Status: Assessment in progress")
        
        # Reset recognition results
        self.recognition_label.setText("No speech recognized yet")
        self.similarity_label.setText("Similarity: 0%")
        
        # Reset waveform
        self.waveform_canvas.plot_waveform()
        
        # Update prompt
        self.update_prompt()
        self.current_prompt = self.speech_prompts[0]
        self.prompt_label.setText(self.current_prompt)
        
        # Show assessment container
        self.assessment_container.setVisible(True)
        
        # Update button states
        self.start_button.setEnabled(False)
        self.record_button.setEnabled(True)
        self.next_prompt_button.setEnabled(False)
        
        # Clean up any previous audio recorder
        if self.audio_recorder and self.audio_recorder.is_alive():
            self.audio_recorder.stop()
    
    def toggle_recording(self):
        """Start or stop recording audio"""
        if not self.recording_in_progress:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio"""
        try:
            # Check if patient name is set
            self.patient_name = self.patient_name_input.text().strip()
            if not self.patient_name:
                QMessageBox.warning(self, "Input Error", "Please enter a patient name before recording.")
                return
                
            print("Starting audio recording process...")
            self.recording_in_progress = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Status: Recording in progress...")
            
            # Create recordings directory if it doesn't exist
            recordings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
            if not os.path.exists(recordings_dir):
                print(f"Creating recordings directory: {recordings_dir}")
                os.makedirs(recordings_dir, exist_ok=True)
            
            # Generate filename with timestamp and sanitize patient name
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', self.patient_name)
            filename = f"{safe_name}_{timestamp}.wav"
            self.recorded_audio_path = os.path.join(recordings_dir, filename)
            
            print(f"Recording will be saved to: {self.recorded_audio_path}")
            
            # Stop any existing audio recorder
            if self.audio_recorder and self.audio_recorder.is_alive():
                self.audio_recorder.stop()
                time.sleep(0.5)  # Allow time for cleanup
            
            # Initialize and start recorder with retry mechanism
            max_retries = 3
            for retry in range(1, max_retries + 1):
                try:
                    self.audio_recorder = AudioRecorder(duration=RECORD_DURATION)
                    self.audio_recorder.filepath = self.recorded_audio_path
                    self.audio_recorder.callback_finished = self.on_recording_finished
                    self.audio_recorder.start()
                    print(f"Audio recorder started (attempt {retry})")
                    break
                except Exception as e:
                    print(f"Error starting recorder (attempt {retry}): {e}")
                    if retry == max_retries:
                        raise
                    time.sleep(1)  # Wait before retrying
            
            # Start timer for progress bar
            self.timer_progress.setValue(0)
            if hasattr(self, 'recording_timer') and self.recording_timer is not None:
                if self.recording_timer.isActive():
                    self.recording_timer.stop()
            
            self.recording_timer = QTimer(self)
            self.recording_timer.timeout.connect(self.update_recording_progress)
            self.recording_timer.start(50)  # Update every 50ms
            
            # Start time for progress calculation
            self.recording_start_time = time.time()
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Recording Error", 
                               f"Could not start recording: {str(e)}\nPlease check your microphone settings.")
            self.recording_in_progress = False
            self.record_button.setText("Start Recording")
    
    def stop_recording(self):
        """Stop recording audio"""
        print("User initiated stop recording")
        
        try:
            # Stop the audio recorder
            if self.audio_recorder and self.audio_recorder.is_alive():
                print("Stopping active audio recorder thread")
                self.audio_recorder.stop()
                # Don't join here as it might block the UI
            else:
                print("No active audio recorder thread to stop")
                
            # Stop the timer
            if hasattr(self, 'recording_timer') and self.recording_timer is not None:
                if self.recording_timer.isActive():
                    print("Stopping recording timer")
                    self.recording_timer.stop()
                else:
                    print("Recording timer not active")
            else:
                print("No recording timer to stop")
            
            # Update UI
            self.timer_progress.setValue(100)
            self.recording_in_progress = False
            self.record_button.setText("Start Recording")
            self.status_label.setText("Status: Processing recording...")
            
        except Exception as e:
            print(f"Error in stop_recording: {e}")
            import traceback
            traceback.print_exc()
    
    def update_recording_progress(self):
        """Update recording progress bar"""
        if not self.recording_in_progress:
            return
            
        elapsed = time.time() - self.recording_start_time
        progress = min(int((elapsed / RECORD_DURATION) * 100), 100)
        self.timer_progress.setValue(progress)
        
        # Auto-stop at the end of duration
        if elapsed >= RECORD_DURATION and self.recording_in_progress:
            self.stop_recording()
    
    def on_recording_finished(self, filepath):
        """Handle completion of audio recording"""
        print(f"Recording finished callback received for: {filepath}")
        
        # Check if file was created successfully
        if not os.path.exists(filepath):
            print(f"Error: Recorded file not found at {filepath}")
            self.status_label.setText("Status: Recording failed - file not created")
            
            # Try to create a simple test file to verify directory permissions
            try:
                test_file_path = os.path.join(os.path.dirname(filepath), "test_permissions.txt")
                with open(test_file_path, 'w') as f:
                    f.write("Test file to check write permissions")
                print(f"Test file created successfully at: {test_file_path}")
                if os.path.exists(test_file_path):
                    os.remove(test_file_path)
            except Exception as e:
                print(f"Error creating test file: {e}")
                QMessageBox.warning(self, "Recording Error", 
                                   f"Could not write to the recordings directory. Please check permissions.")
                
            # Enable record button for retry
            self.record_button.setEnabled(True)
            QMessageBox.warning(self, "Recording Error", 
                               "No audio file was created. Please check your microphone settings and try again.")
            return
            
        # Check file size to ensure it contains meaningful data
        file_size = os.path.getsize(filepath)
        print(f"Recorded file size: {file_size} bytes")
        
        if file_size < 1000:  # Less than 1KB is probably empty/corrupt
            print(f"Warning: Audio file is too small ({file_size} bytes), may contain no data")
            self.status_label.setText("Status: Recording may be empty - please try again")
            self.record_button.setEnabled(True)
            
            # Continue anyway for debugging but warn user
            QMessageBox.warning(self, "Recording Warning", 
                               "The recorded audio file is unusually small. Audio may be silent or corrupted.")
            
        try:
            # Read the audio file to display waveform
            with wave.open(filepath, 'rb') as wf:
                # Get basic info
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                
                print(f"Wave file info: channels={n_channels}, width={sample_width}, " + 
                      f"rate={sample_rate}, frames={n_frames}")
                
                # Read frames
                pcm_data = wf.readframes(n_frames)
                
                # Convert to numpy array
                if sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    dtype = np.uint8
                
                audio_data = np.frombuffer(pcm_data, dtype=dtype)
                
                # If stereo, convert to mono by averaging channels
                if n_channels == 2:
                    audio_data = audio_data.reshape(-1, 2).mean(axis=1)
                
                # Check for silent audio
                audio_max = np.max(np.abs(audio_data))
                print(f"Audio max amplitude: {audio_max}")
                if audio_max < 100:  # Very low amplitude
                    print("Warning: Audio appears to be silent or very quiet")
                    self.status_label.setText("Status: Audio is silent - check microphone")
                
                # Update waveform display
                self.waveform_canvas.plot_waveform(audio_data, sample_rate)
                print("Waveform display updated successfully")
        except Exception as e:
            print(f"Error displaying waveform: {e}")
            import traceback
            traceback.print_exc()
            # Continue with recognition even if waveform display fails
            
        # Start speech recognition in a separate thread
        self.status_label.setText("Status: Recognizing speech...")
        self.recognize_speech(filepath)
    
    def on_recognition_complete(self):
        """Handle completion of speech recognition (called from main thread)"""
        print("Recognition complete signal received")
        self.status_label.setText("Status: Recognition complete")
        self.record_button.setEnabled(True)
        self.next_prompt_button.setEnabled(True)
        
    def recognize_speech(self, audio_file):
        """Recognize speech from recorded audio file"""
        def recognition_worker():
            try:
                print(f"Starting speech recognition for file: {audio_file}")
                
                # Check if file exists
                if not os.path.exists(audio_file):
                    print(f"Error: Audio file not found: {audio_file}")
                    self.recognition_signal.emit("[Error: Audio file not found]")
                    return
                
                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_file) as source:
                    print("Reading audio file...")
                    audio_data = recognizer.record(source)
                    
                    print("Sending to Google Speech Recognition...")
                    # Try to recognize using Google Speech Recognition
                    text = recognizer.recognize_google(audio_data, language='en-US')
                    print(f"Recognition result: {text}")
                    
                    # Update UI from main thread using signal
                    self.recognition_signal.emit(text)
            except sr.UnknownValueError:
                print("Speech not recognized by Google API")
                self.recognition_signal.emit("[Speech not recognized]")
            except sr.RequestError as e:
                print(f"Google Speech API request error: {e}")
                self.recognition_signal.emit(f"[Recognition error: {str(e)}]")
            except Exception as e:
                print(f"Recognition error: {e}")
                self.recognition_signal.emit(f"[Error: {str(e)}]")
            finally:
                # Ensure we always update the UI status even if there's an error
                print("Recognition worker finished")
                self.recognition_complete_signal.emit()
        
        # Start recognition in a separate thread
        print("Starting recognition thread...")
        self.recognition_thread = threading.Thread(target=recognition_worker)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
    
    @pyqtSlot(str)
    def update_recognition_result(self, recognized_text):
        """Update the UI with speech recognition result and calculate similarity score"""
        try:
            # Display recognized text
            self.recognition_label.setText(recognized_text)
            
            # Calculate similarity between prompt and recognized text
            from difflib import SequenceMatcher
            
            # Convert both to lowercase for better comparison
            prompt_lower = self.current_prompt.lower()
            recognized_lower = recognized_text.lower()
            
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, prompt_lower, recognized_lower).ratio()
            similarity_percent = int(similarity * 100)
            
            # Update similarity display
            self.similarity_label.setText(f"Similarity: {similarity_percent}%")
            
            # Update score based on similarity
            prompt_score = int(similarity_percent / 5)  # Max 20 points per prompt
            self.score += prompt_score
            self.score_label.setText(f"Score: {self.score}")
            
            # Update status
            self.status_label.setText("Status: Recognition complete")
            
            # Enable next prompt button
            self.next_prompt_button.setEnabled(True)
            
        except Exception as e:
            print(f"Error updating recognition result: {e}")
            self.status_label.setText("Status: Error in recognition processing")
    
    def next_prompt(self):
        """Move to the next speech prompt"""
        # Get the current index
        try:
            current_index = self.speech_prompts.index(self.current_prompt)
            next_index = (current_index + 1) % len(self.speech_prompts)
            
            # Update prompt
            self.current_prompt = self.speech_prompts[next_index]
            self.prompt_label.setText(self.current_prompt)
            
            # Reset recognition results
            self.recognition_label.setText("No speech recognized yet")
            self.similarity_label.setText("Similarity: 0%")
            
            # Reset waveform
            self.waveform_canvas.plot_waveform()
            
            # Reset buttons
            self.record_button.setEnabled(True)
            self.next_prompt_button.setEnabled(False)
            
            # Check if we've completed all prompts
            if next_index == 0:
                self.complete_assessment()
                
        except ValueError:
            # If current_prompt isn't in the list (shouldn't happen)
            self.current_prompt = self.speech_prompts[0]
            self.prompt_label.setText(self.current_prompt)
    
    def complete_assessment(self):
        """Complete the speech assessment"""
        try:
            # Update UI state
            self.status_label.setText("Status: Assessment complete")
            self.record_button.setEnabled(False)
            self.next_prompt_button.setEnabled(False)
            self.start_button.setEnabled(True)
            
            # Save score to CSV
            self.update_speech_score(self.patient_name, self.score)
            
            # Show completion message
            QMessageBox.information(self, "Assessment Complete", 
                                  f"Speech assessment completed!\nFinal score: {self.score}")
            
        except Exception as e:
            print(f"Error completing assessment: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error completing assessment: {str(e)}")
    
    def update_speech_score(self, patient_name, score):
        """Update the speech score in the CSV file"""
        try:
            patients_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "patients_data.csv")
            df = pd.read_csv(patients_data_path)
            # Find patient by name (case-insensitive partial match)
            patient_idx = df[df['name'].str.contains(patient_name, case=False, na=False)].index
            if len(patient_idx) > 0:
                df.loc[patient_idx[0], 'Speech Score'] = score
                df.to_csv(patients_data_path, index=False)
                return True
            return False
        except Exception as e:
            print(f"Error updating speech score: {e}")
            return False
    
    def closeEvent(self, event):
        """Handle cleanup when window is closed"""
        try:
            # Stop recording if in progress
            if self.audio_recorder and self.audio_recorder.is_alive():
                self.audio_recorder.stop()
                
            # Stop timer if active
            if hasattr(self, 'recording_timer') and self.recording_timer and self.recording_timer.isActive():
                self.recording_timer.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
        event.accept() 