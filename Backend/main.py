#TRY--------------LIve Stream of Video Sucess
import csv
import os
import re
import easyocr
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime, timedelta
from sort.sort import Sort
from db_operations import insert_vehicle_logs, update_suspicious_status,get_email_for_license_plate, vehicle_permissions_status
from mail import send_notification


# Initialize results and tracker
results = {}
license_plate_info = []
mot_tracker = Sort()
# Initialize a set to store unique license plates
detected_plates = set()

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Output directory for cropped images
output_dir = 'cropped_img'
os.makedirs(output_dir, exist_ok=True)

# Load models
try:
    vehicle_model = YOLO('Backend/models/yolov8n.pt')  # Model for vehicle detection
    license_plate_model1 = YOLO('../Backend/models/best.pt')  # First model for license plate detection
    license_plate_model2 = YOLO('../Backend/models/license_plate_detector.pt')  # Second model for license plate detection
except Exception as e:
    print(f"Error loading models: {e}")
    exit(1)

# Function to write results to CSV
def write_csv(results, csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Frame Number', 'Car ID', 'Car BBox', 'License Plate BBox', 'License Plate Text', 'BBox Score', 'Detection Score'])

        for frame_nmr, cars in results.items():
            for car_id, data in cars.items():
                car_bbox = data['car']['bbox']
                license_plate_bbox = data['license_plate']['bbox']
                license_plate_text = data['license_plate']['text']
                bbox_score = data['license_plate']['bbox_score']
                detection_score = data['license_plate'].get('detection_score', 0)

                writer.writerow([
                    frame_nmr,
                    car_id,
                    car_bbox,
                    license_plate_bbox,
                    license_plate_text,
                    bbox_score,
                    detection_score
                ])


# Last detection time for each license plate
last_detection_time = {}
license_plate_state = {}
time_window = timedelta(minutes=5)  # Time window for sending emails (5 minutes)



# Function to assign car IDs to license plates
def get_car(track_ids):
    if len(track_ids) > 0:
        return int(track_ids[0][-1])  # Assuming the last value in track_ids is the car ID
    return -1  # Return -1 if no car is assigned


def clean_license_plate_text(text_segments):
    # Join text segments and clean them
    combined_text = ''.join(text_segments)
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '', combined_text)
    cleaned_text = cleaned_text.replace('IND', '')  # Remove 'IND' if present

    corrections = {
        'O': '0', 'Z': '2', 'I': '1', 'B': '8', 'S': '5', 'G': '6', 'L': '4', 'U': '11'
    }

    # Correct common OCR issues
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
        cleaned_text = cleaned_text.upper()

    return cleaned_text


def is_plate_format_valid(plate_text):
    pattern = r'^[A-Z]{2}\d{1,2}[A-Z]{0,2}\d{4}$'
    return re.match(pattern, plate_text) is not None


def combine_license_plate_detections(detections1, detections2):
    combined_detections = detections1 + detections2
    best_detections = {}

    for detection in combined_detections:
        x1, y1, x2, y2, score, class_id = detection
        bbox_key = (int(x1), int(y1), int(x2), int(y2))
        
        if bbox_key not in best_detections or score > best_detections[bbox_key][1]:
            best_detections[bbox_key] = (detection, score)
    
    return [det[0] for det in best_detections.values()]


# Function to send email 
def send_email(license_plate):
    email = get_email_for_license_plate(formatted_license_plate)
    print("licence plate is",license_plate,"email is sent on",email)
    send_notification(license_plate,email)
    insert_vehicle_logs(license_plate, "rcpit_admin")
    print(f"Sending email on { email} , for license plate: {license_plate}")
    # Add email sending logic here (e.g., using SMTP, Mailgun, etc.)

# Load video
cap = cv2.VideoCapture('../Backend/Uploads/UserUploadedVideo.mp4')
if not cap.isOpened():
    print("Error opening video file.")
    exit(1)

vehicles = [2, 3, 5, 7]
frame_nmr = -1
ret = True

while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret:
        results[frame_nmr] = {}

        # Detect vehicles
        vehicle_detections = vehicle_model(frame)[0]
        detections_ = []

        for detection in vehicle_detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])

        if detections_:
            # Track vehicles
            track_ids = mot_tracker.update(np.asarray(detections_))

            # Detect license plates
            license_plate_detections1 = license_plate_model1(frame)[0]
            license_plate_detections2 = license_plate_model2(frame)[0]
            license_plate_detections1 = license_plate_detections1.boxes.data.tolist()
            license_plate_detections2 = license_plate_detections2.boxes.data.tolist()
            combined_license_plate_detections = combine_license_plate_detections(license_plate_detections1, license_plate_detections2)

            for license_plate in combined_license_plate_detections:
                x1, y1, x2, y2, score, class_id = license_plate
                car_id = get_car(track_ids)

                if car_id != -1:
                    license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                    cropped_image_path = os.path.join(output_dir, f'license_plate_frame_{frame_nmr}_car_{car_id}.jpg')

                    # OCR for license plate number
                    license_plate_text = reader.readtext(license_plate_crop, detail=0)
                    ocr_score = len(' '.join(license_plate_text))

                    # Clean the license plate text
                    formatted_license_plate = clean_license_plate_text(license_plate_text)

                    if is_plate_format_valid(formatted_license_plate) and formatted_license_plate not in detected_plates and ocr_score > 0.8:
                        license_plate_info.append({
                            'license_number': formatted_license_plate,
                            'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        detected_plates.add(formatted_license_plate)

                        current_time = datetime.now()

                        # Check if the license plate was detected recently
                        if formatted_license_plate not in last_detection_time or current_time - last_detection_time[formatted_license_plate] > time_window:
                            print("Vehicle Number: ",formatted_license_plate,"  Detected At:",datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            # Send email if it's a new detection or past the time window
                            send_email(formatted_license_plate)
                            last_detection_time[formatted_license_plate] = current_time
                            license_plate_state[formatted_license_plate] = "waiting"
                            cv2.putText(frame, "Waiting for Permission", (int(x1), int(y1) - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            # vehicle_permissions_status(formatted_license_plate)
                            

                            


                    # Store results if OCR score is high
                    if ocr_score > 0.8 and license_plate_text:
                        results[frame_nmr][car_id] = {
                            'car': {'bbox': [x1, y1, x2, y2]},
                            'license_plate': {
                                'bbox': [x1, y1, x2, y2],
                                'text': ' '.join(license_plate_text),
                                'bbox_score': score,
                                'detection_score': ocr_score
                            }
                        }
                    # Display the frame with labels
                    cv2.imshow('License Plate Detection', frame)

                   # Wait for key press to exit (press 'q' to exit)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                      break

                    # Draw bounding boxes and label on the frame
                    print("Vehicle Number: ",formatted_license_plate,"  Detected At:",datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)  # License plate bbox
                    cv2.putText(frame, formatted_license_plate, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Show "Waiting for Permission" label if the state is "waiting"
                    if license_plate_state.get(formatted_license_plate) == "waiting":
                        cv2.putText(frame, "Licence Plate Detected", (int(x1), int(y1) - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    

        # # Display the frame with labels
        # cv2.imshow('License Plate Detection', frame)

        # Wait for key press to exit (press 'q' to exit)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()