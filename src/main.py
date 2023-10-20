import os
import cv2
import numpy as np
import pytesseract
import csv

def setup_directories(base_path):
    videos_dir = os.path.join(base_path, "data", "videos")
    if not os.path.exists(videos_dir):
        raise Exception("Videos directory not found.")
    os.chdir(videos_dir)
    output_dir = os.path.join(base_path, "data", "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return videos_dir, output_dir

def setup_video_capture(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video.")
    return cap

def process_frame(frame):
    # 1. Convert to Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 2. Resize Image
    resized = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    # 3. Noise Removal
    denoised = cv2.medianBlur(resized, 3)
    # 4. Absolute Thresholding
    _, thresh1 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 5. Hole filling: Erode followed by Dilate to close holes outside of text
    kernel = np.ones((5, 5), np.uint8)
    closed = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
    return closed

def process_text(img):
    text = pytesseract.image_to_string(img)
    text = text.replace("\n", " ")
    text = text.strip()
    return text

def export_to_csv(extracted_texts, output_dir):
    csv_path = os.path.join(output_dir, "output.csv")
    with open(csv_path, "w") as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        writer.writerow(["seconds", "text"])
        for seconds, text in extracted_texts:
            writer.writerow([seconds, text])
    print("Finished exporting to csv at ", csv_path)

def main():
    cwd = os.getcwd()
    print("Starting text extraction from video, please be patient...")
    
    videos_dir, save_dir = setup_directories(cwd)
    video_path = os.path.join(videos_dir, "1.mp4")
    
    cap = setup_video_capture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    video_seconds = 0 # to keep track of the seconds elapsed in the video
    
    # A list to store tuples of (seconds_elapsed, extracted text)
    extracted_texts = []  
    
    # Loop through the video and extract text from 1 frame each second
    while True:
        frame_number = int(video_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if not ret: 
            break
        
        processed_frame = process_frame(frame)
        text = process_text(processed_frame)
        extracted_texts.append((video_seconds, text))
        video_seconds += 1 

    cap.release()
    print("Finished extracting text from video.")
    print("Exporting to csv...")
    export_to_csv(extracted_texts, save_dir)

if __name__ == "__main__":
    main()
