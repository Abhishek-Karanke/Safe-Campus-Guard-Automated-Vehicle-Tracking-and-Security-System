import os
import re
import csv
import cv2
import numpy as np
from datetime import datetime
from sort.sort import Sort  
import easyocr
from ultralytics import YOLO

def run_anpr():
    # Initialize results and tracker
    results = {}
    license_plate_info = []
    mot_tracker = Sort()
    detected_plates = set()  # Unique license plates

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])

    # Output directory for cropped images
    output_dir = 'cropped_img'
    os.makedirs(output_dir, exist_ok=True)

    # Load models
    try:
        vehicle_model = YOLO('yolov8n.pt')  # Model for vehicle detection
        license_plate_model1 = YOLO('models/best.pt')  # First model for license plate detection
        license_plate_model2 = YOLO('models/license_plate_detector.pt')  # Second model for license plate detection
    except Exception as e:
        print(f"Error loading models: {e}")
        return

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
                    writer.writerow([frame_nmr, car_id, car_bbox, license_plate_bbox, license_plate_text, bbox_score, detection_score])

    # Function to assign car IDs to license plates
    def get_car(track_ids):
        return int(track_ids[0][-1]) if len(track_ids) > 0 else -1

    # Function to clean license plate text
    def clean_license_plate_text(text_segments):
        combined_text = ''.join(text_segments)
        cleaned_text = re.sub(r'[^A-Za-z0-9]', '', combined_text).replace('IND', '')
        corrections = {'O': '0', 'Z': '2', 'I': '1', 'B': '8', 'S': '5', 'G': '6', 'L': '4', 'U': '11'}
        if len(cleaned_text) >= 4:
            state_code, district_code, vehicle_code = cleaned_text[:2], cleaned_text[2:4], cleaned_text[4:]
            for wrong_char, correct_char in corrections.items():
                if district_code[0] == wrong_char:
                    district_code = correct_char + district_code[1:]
                if district_code[1] == wrong_char:
                    district_code = district_code[0] + correct_char
            cleaned_text = (state_code + district_code + vehicle_code).upper()
            print(cleaned_text)
        return cleaned_text

    # Check if plate format is valid
    def is_plate_format_valid(plate_text):
        pattern = r'^[A-Z]{2}\d{2}[A-Z]{0,2}\d{4}$'
        return re.match(pattern, plate_text) is not None

    # Combine detections from both models
    def combine_license_plate_detections(detections1, detections2):
        combined_detections = detections1 + detections2
        best_detections = {}
        for detection in combined_detections:
            x1, y1, x2, y2, score, class_id = detection
            bbox_key = (int(x1), int(y1), int(x2), int(y2))
            if bbox_key not in best_detections or score > best_detections[bbox_key][1]:
                best_detections[bbox_key] = (detection, score)
        return [det[0] for det in best_detections.values()]

    # Load video
    cap = cv2.VideoCapture('Uploads/test.mp4')
    if not cap.isOpened():
        print("Error opening video file.")
        return

    # Define vehicle class IDs to track
    vehicles = [2, 3, 5, 7]
    frame_nmr = -1

    # Main loop
    while True:
        frame_nmr += 1
        ret, frame = cap.read()
        if not ret:
            break

        results[frame_nmr] = {}

        # Detect vehicles
        vehicle_detections = vehicle_model(frame)[0]
        detections_ = [
            [x1, y1, x2, y2, score] 
            for x1, y1, x2, y2, score, class_id in vehicle_detections.boxes.data.tolist()
            if int(class_id) in vehicles
        ]

        # Track vehicles
        if detections_:
            track_ids = mot_tracker.update(np.asarray(detections_))

            # Detect license plates using both models
            license_plate_detections1 = license_plate_model1(frame)[0].boxes.data.tolist()
            license_plate_detections2 = license_plate_model2(frame)[0].boxes.data.tolist()
            combined_license_plate_detections = combine_license_plate_detections(license_plate_detections1, license_plate_detections2)

            for license_plate in combined_license_plate_detections:
                x1, y1, x2, y2, score, class_id = license_plate
                car_id = get_car(track_ids)

                if car_id != -1:
                    # Crop and save license plate image
                    license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                    cropped_image_path = os.path.join(output_dir, f'license_plate_frame_{frame_nmr}_car_{car_id}.jpg')
                    # cv2.imwrite(cropped_image_path, license_plate_crop)

                    # Read license plate number
                    license_plate_text = reader.readtext(license_plate_crop, detail=0)
                    ocr_score = len(' '.join(license_plate_text))

                    # Clean and validate plate text
                    formatted_license_plate = clean_license_plate_text(license_plate_text)
                    if is_plate_format_valid(formatted_license_plate) and formatted_license_plate not in detected_plates and ocr_score > 0.8:
                        license_plate_info.append({
                            'license_number': formatted_license_plate,
                            'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        detected_plates.add(formatted_license_plate)

                    # Store results with high OCR score
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

    # Release video capture
    cap.release()

    # Write results to CSV
    if results:
        write_csv(results, './test.csv')
    else:
        print("No results to write to CSV.")

    print(license_plate_info)
