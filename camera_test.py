import cv2
import numpy as np
import time
import sys
import os

try:
    from cvzone.HandTrackingModule import HandDetector
    HAND_DETECTOR_AVAILABLE = True
except ImportError:
    print("Hand detector module not available. Only testing camera.")
    HAND_DETECTOR_AVAILABLE = False

def main():
    print("NeuroWell Camera and Hand Detection Test")
    print("========================================")
    print("This tool will help diagnose camera and hand detection issues.")
    print("Press 'q' to quit, 'r' to reset settings.")
    
    # Try different camera backends
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_ANY, "Default"),
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_MSMF, "Microsoft Media Foundation")
    ]
    
    camera = None
    
    # Try each backend until one works
    for backend, name in backends:
        print(f"\nTrying {name} backend...")
        try:
            camera = cv2.VideoCapture(0, backend)
            if camera.isOpened():
                print(f"Success! Camera opened with {name} backend.")
                break
        except Exception as e:
            print(f"Error with {name} backend: {e}")
    
    # If no backend worked, try basic approach
    if camera is None or not camera.isOpened():
        print("\nTrying basic camera open...")
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("ERROR: Could not open camera with any method.")
            print("Please check your camera connection and permissions.")
            return
    
    # Set camera properties
    width, height = 640, 480
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Initialize hand detector if available
    detector = None
    if HAND_DETECTOR_AVAILABLE:
        try:
            print("Initializing hand detector...")
            detector = HandDetector(detectionCon=0.5, maxHands=2)
            print("Hand detector initialized!")
        except Exception as e:
            print(f"Error initializing hand detector: {e}")
    
    # Settings
    brightness = 0
    contrast = 1.0
    
    while True:
        # Read frame
        ret, frame = camera.read()
        
        if not ret:
            print("Failed to get frame. Trying again...")
            time.sleep(0.5)
            continue
        
        # Mirror image
        frame = cv2.flip(frame, 1)
        
        # Apply current brightness/contrast settings
        adjusted = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
        
        # Process hands if detector is available
        if detector:
            try:
                hands, adjusted = detector.findHands(adjusted, flipType=False, draw=True)
                
                if hands:
                    hand_count = len(hands)
                    cv2.putText(adjusted, f"{hand_count} hand{'s' if hand_count > 1 else ''} detected!", 
                              (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Draw circles on fingertips for better visibility
                    for hand in hands:
                        if 'lmList' in hand and len(hand['lmList']) > 8:
                            for i in [4, 8, 12, 16, 20]:  # Thumb and fingertips
                                if i < len(hand['lmList']):
                                    finger_tip = hand['lmList'][i][:2]
                                    cv2.circle(adjusted, tuple(finger_tip), 10, (0, 255, 255), cv2.FILLED)
                else:
                    cv2.putText(adjusted, "No hands detected - Show hands to camera", 
                              (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            except Exception as e:
                print(f"Error detecting hands: {e}")
                cv2.putText(adjusted, f"Hand detection error: {str(e)[:50]}", 
                          (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Add instructions
        cv2.putText(adjusted, "Press 'q': Quit  'r': Reset  '+/-': Brightness  '[/]': Contrast", 
                  (10, height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add current settings display
        cv2.putText(adjusted, f"Brightness: {brightness}  Contrast: {contrast:.1f}", 
                  (10, height-40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                  
        # Display frame
        cv2.imshow("Camera & Hand Detection Test", adjusted)
        
        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            brightness = 0
            contrast = 1.0
            print("Settings reset to defaults")
        elif key == ord('+'):
            brightness = min(brightness + 10, 100)
        elif key == ord('-'):
            brightness = max(brightness - 10, -100)
        elif key == ord(']'):
            contrast = min(contrast + 0.1, 3.0)
        elif key == ord('['):
            contrast = max(contrast - 0.1, 0.1)
    
    # Clean up
    camera.release()
    cv2.destroyAllWindows()
    print("Test completed. Exiting.")

if __name__ == "__main__":
    main() 