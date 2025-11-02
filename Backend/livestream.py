#version GPT  - Better RESULTS
import csv
import os
import re
import easyocr
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime
from sort.sort import Sort

# Initialize results and tracker
results = {}
license_plate_info = []
mot_tracker = Sort()
detected_plates = set()

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Output directory for cropped images
output_dir = 'cropped_img'
os.makedirs(output_dir, exist_ok=True)

# Load models
try:
    vehicle_model = YOLO('Backend/models/yolov8n.pt')  # Vehicle detection model
    license_plate_model1 = YOLO('../Backend/models/best.pt')  # License plate model 1
    license_plate_model2 = YOLO('../Backend/models/license_plate_detector.pt')  # License plate model 2
except Exception as e:
    print(f"Error loading models: {e}")
    exit(1)

# Function to draw bounding boxes and text on frame
def draw_license_plate(frame, bbox, license_plate_text):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green bounding box
    cv2.putText(frame, license_plate_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# Clean up license plate text function
def clean_license_plate_text(text_segments):
    combined_text = ''.join(text_segments)
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '', combined_text)
    cleaned_text = cleaned_text.replace('IND', '')

    corrections = {
        'O': '0', 'Z': '2', 'I': '1', 'B': '8', 'S': '5', 'G': '6', 'L': '4'
    }

    if len(cleaned_text) >= 4:
        state_code = cleaned_text[:2]
        district_code = cleaned_text[2:4]
        vehicle_code = cleaned_text[4:]

        for wrong_char, correct_char in corrections.items():
            if district_code[0] == wrong_char:
                district_code = correct_char + district_code[1:]
            if district_code[1] == wrong_char:
                district_code = district_code[0] + correct_char

        cleaned_text = state_code + district_code + vehicle_code

    return cleaned_text

# Define function for license plate format validation
def is_plate_format_valid(plate_text):
    pattern = r'^[A-Z]{2}\d{2}[A-Z]{0,2}\d{4}$'
    return re.match(pattern, plate_text) is not None

# Load IP camera feed
ip_camera_url = 'http://192.168.4.104:8080/video?ffmpeg:buffer_size=32768'
cap = cv2.VideoCapture(ip_camera_url)

if not cap.isOpened():
    print("Error opening IP camera.")
    exit(1)

# Resize settings for the feed
frame_width = 640
frame_height = 480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

yolo_input_size = 640

# Define vehicle class IDs to track
vehicles = [2, 3, 5, 7]
frame_nmr = -1

# Main loop for IP camera feed
while True:
    frame_nmr += 1
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from IP camera.")
        break

    results[frame_nmr] = {}

    # Run vehicle detection with YOLO model
    vehicle_detections = vehicle_model(frame, verbose=False)[0]  # Disable verbose logging
    detections_ = []
    
    for detection in vehicle_detections.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = detection
        if int(class_id) in vehicles:
            detections_.append([x1, y1, x2, y2, score])

    if detections_:
        track_ids = mot_tracker.update(np.asarray(detections_))

        # Detect license plates using both models
        license_plate_detections1 = license_plate_model1(frame, verbose=False)[0]
        license_plate_detections2 = license_plate_model2(frame, verbose=False)[0]

        # Combine results from both models
        combined_license_plate_detections = license_plate_detections1.boxes.data.tolist() + license_plate_detections2.boxes.data.tolist()

        for license_plate in combined_license_plate_detections:
            x1, y1, x2, y2, score, class_id = license_plate
            license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]

            # Perform OCR on cropped license plate image
            license_plate_text = reader.readtext(license_plate_crop, detail=0)
            formatted_license_plate = clean_license_plate_text(license_plate_text)
            
            if is_plate_format_valid(formatted_license_plate) and formatted_license_plate not in detected_plates:
                detected_plates.add(formatted_license_plate)
                license_plate_info.append({
                    'license_number': formatted_license_plate,
                    'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"License Plate: {formatted_license_plate}, Date-Time: {license_plate_info[-1]['date_time']}")

                # Draw bounding box and text on frame
                draw_license_plate(frame, [x1, y1, x2, y2], formatted_license_plate)

    # Display the frame
    cv2.imshow('IP Camera ANPR', frame)

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
