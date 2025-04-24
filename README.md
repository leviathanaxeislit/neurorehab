# NeuroWell - Native Windows Application

This is the native Windows application version of the NeuroWell neuro-rehabilitation platform. It provides the same functionality as the Streamlit web application but packaged as a standalone Windows application.

## Features

- **Patient Management**: Create and manage patient profiles with detailed medical histories and previous assessments
- **Comprehensive Assessments**: Conduct assessments using computer vision games, speech analysis, and hand tracking
- **Results Analysis**: Get detailed analysis of patient performance with graphical representations
- **Personalized Rehab Plans**: Create tailored rehabilitation plans based on assessment results
- **Community Support**: Connect patients with support groups and resources

## Installation

### Prerequisites

- Windows 10 or later
- Python 3.8 or later
- Webcam (required for hand tracking and vision-based assessments)

### Setup Instructions

1. Clone or download this repository
2. Open a command prompt in the `native app` directory
3. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python main.py
   ```

## Usage

### For Nurses/Healthcare Providers

1. Launch the application and log in with your credentials
2. Use the "Home" section to manage patient profiles
3. Navigate to specific assessment modules:
   - **Physio**: Conduct physiotherapy assessments
   - **Hand**: Test hand mobility and fine motor skills
   - **Game**: Use the snake game to assess hand-eye coordination
   - **Result**: View assessment results and generate reports

### For Patients

1. Launch the application and log in with your credentials
2. Use the "Home" section to view your rehabilitation progress
3. Navigate to specific modules:
   - **Rehab**: Access your personalized rehabilitation exercises
   - **Community**: Connect with support groups and resources

## Development

This application is built using:
- PyQt5 for the user interface
- OpenCV and cvzone for computer vision and hand tracking
- Pandas for data management
- Matplotlib for data visualization

## Troubleshooting

### Camera Access Issues

- Ensure your webcam is properly connected and not in use by another application
- On Windows, try running with Administrator privileges
- If you see a permissions prompt for camera access, be sure to approve it
- If using an external webcam, try a different USB port

### Hand Detection Issues

- **Hand Not Detected**: 
  - Make sure your hand is clearly visible in the camera feed
  - Ensure your hand is well-lit - try adding more light to the room
  - Hold your hand 12-24 inches (30-60 cm) from the camera
  - Keep your hand in front of a plain background if possible
  - Make slow, deliberate movements rather than quick ones
  - Try using the diagnostic tool: `python camera_test.py`

- **Performance Issues**:
  - Close other resource-intensive applications while using hand tracking features
  - If your computer has integrated and dedicated graphics cards, make sure the application is using the dedicated GPU
  - Consider lowering your webcam resolution in your operating system settings

### MediaPipe/cvzone Issues

If you're encountering errors related to the hand tracking modules:

1. Try reinstalling the dependencies:
   ```
   pip uninstall mediapipe cvzone
   pip install mediapipe==0.10.5 cvzone==1
   ```

2. For Windows-specific issues, use the launcher script which sets helpful environment variables:
   ```
   python run_neurowell.py
   ```
   
3. For advanced users on Windows, you can try installing an older version of mediapipe which might have better compatibility:
   ```
   pip install mediapipe==0.8.10
   ```

### Data Loading Errors

- Make sure the CSV files are not open in other applications
- Check file permissions to ensure the application can read and write to the data files

If problems persist, please contact support at bytebuddies@gmail.com with details about your system configuration and the specific issue you're experiencing.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Developed by ByteBuddies Team
- Built based on the Streamlit version of NeuroWell

## User Interface Design

The NeuroWell application features a modern, responsive user interface designed with the following principles:

### Design System Features

- **Consistent Color Palette**: A carefully selected color palette with primary (#3498DB), secondary, and accent colors that maintain proper contrast ratios
- **Modern Typography**: Clean, readable font stack with consistent type scale and hierarchy
- **Card-Based UI**: Modern card-based layout that organizes information into digestible chunks
- **Responsive Components**: UI elements that adapt to different screen sizes and resolutions
- **Visual Hierarchy**: Clear visual hierarchy that guides users through the interface
- **Modern Navigation**: Streamlined navigation with clear indication of current location
- **Accessibility Focus**: High-contrast text, clear focus states, and proper labeling
- **Dashboard Widgets**: Informative dashboard components with visual data representations
- **Reduced Visual Noise**: Clean layouts with proper spacing and alignment
- **Standardized Controls**: Consistent styling of buttons, forms, and interactive elements

### Design Color Palette

- Primary Blue: #3498DB (Button backgrounds, highlights, links)
- Dark Blue: #2C3E50 (Headers, navigation bar)
- Success Green: #2ECC71 (Success indicators, progress)
- Warning Orange: #F39C12 (Warnings, important notes)
- Danger Red: #E74C3C (Errors, critical actions)
- Gray Palette: #ECF0F1, #BDC3C7, #95A5A6, #7F8C8D (Backgrounds, borders, secondary text)

### UI Components

- **Modern Header**: Dark-themed header with app branding and user context
- **Navigation Bar**: Modern navbar with visual indication of current section
- **Dashboard Cards**: Clean, card-based design for displaying information
- **Data Tables**: Modern tables with improved styling for better readability
- **Form Controls**: Redesigned form elements with clear focus states and validation
- **Progress Indicators**: Visual progress bars and status indicators
- **Responsive Layouts**: Grid-based layouts that adapt to different screen sizes

### Screenshots

*Coming soon* 