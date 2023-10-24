import os
import sys
import cv2
import numpy as np
import pytesseract
import csv
import re
from thefuzz import fuzz

# Constants
SIMILARITY_THRESHOLD = 70
TIME_WINDOW = 5
LOAD_PROGRESS_INCREMENT = 0.05

def create_directory(path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def setup_directories(base_path):
    """Set up data and output directories."""
    data_dir = os.path.join(base_path, "data")
    videos_dir = os.path.join(data_dir, "videos")
    output_dir = os.path.join(data_dir, "output")

    create_directory(data_dir)
    create_directory(videos_dir)
    create_directory(output_dir)
    
    return videos_dir, output_dir

def setup_video_capture(video_path):
    """Initialize video capture."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Could not open video at {video_path}. Please ensure it exists and try again.")
    return cap

def process_frame(frame):
    """Process video frame to improve OCR accuracy."""
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


def remove_noise(text):
    """Remove noise from extracted text."""
    # The regular expression pattern below matches any character that is NOT:
    # - a letter (a-z or A-Z)
    # - a number (0-9)
    # - a period (.)
    # - a comma (,)
    # - an apostrophe (’)
    # - a colon (:)
    # - a quotation mark (" or ')
    text = re.sub(r"[^a-zA-Z0-9.,'’:\"]", " ", text)
    # after previous step, remove cases of single letters which are likely noise (anything except for a/A or i/I)
    text = re.sub(r" (?![aAiI]). ", " ", text)
    # remove extra spaces
    text = re.sub(r" +", " ", text)
    return text

def extract_text(frame):
    """Extract text from a video frame."""
    text = pytesseract.image_to_string(frame)
    text = text.replace("\n", " ")
    text = remove_noise(text)
    text = text.strip()
    return text

def deduplicate_by_proximity(data):
    """Deduplicate text entries based on similarity and proximity."""
    to_remove = set()
    total_entries = len(data)
    for i, (timestamp, current_text) in enumerate(data):
        # remove any empty entries (contained only noise and are now empty after removing noise in previous step)
        if not (isinstance(timestamp, str) and isinstance(current_text, str) and current_text):
            to_remove.add(i)
            continue
        # compare current text with the next few entries
        for j in range(i+1, min(i+1+TIME_WINDOW, total_entries)):
            _, next_text = data[j]
            if fuzz.partial_ratio(current_text, next_text) > SIMILARITY_THRESHOLD:
                to_remove.add(j)

    deduplicated = [entry for i, entry in enumerate(data) if i not in to_remove]
    return deduplicated

def seconds_to_timestamp(seconds):
    """Convert seconds to MM:SS timestamp format."""
    minutes = int(seconds / 60)
    seconds = seconds % 60
    return f"{minutes}:{seconds}"    

def export_to_csv(extracted_texts):
    """Export extracted texts to CSV."""
    print("REQUEST_OUTPUT_PATH", end='\r', flush=True)
    csv_path = input().strip()
    #print(csv_path)
    with open(csv_path, "w") as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        writer.writerow(["Time", "Text in English"])
        for seconds, text in extracted_texts:
            writer.writerow([seconds, text])


def main(video_path):
    """Main function to extract text from video and export to CSV"""
    cwd = os.getcwd()
    print("Extracting text from video, please be patient...", flush=True)
    
    videos_dir, save_dir = setup_directories(cwd)
        
    cap = setup_video_capture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    video_seconds = 0 # to keep track of the seconds elapsed in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Used to inform the user of the progress of the program (how much of the video has been processed)
    load_progress = 0.05
    frame_milestone = int(total_frames/fps * load_progress)
    
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
        text = extract_text(processed_frame)
        extracted_texts.append((seconds_to_timestamp(video_seconds), text))
        
        if video_seconds == frame_milestone:
            print(f"Processed {int(load_progress*100)}%... {frame_number}/{total_frames} frames", flush=True)                
            load_progress += 0.05
            frame_milestone = int(total_frames/fps * load_progress)
        video_seconds += 1
    cap.release()
    
    extracted_texts = deduplicate_by_proximity(extracted_texts)
    #print("Finished extracting text from video. Exporting to csv...", flush=True)
    export_to_csv(extracted_texts)
    print("Complete!\nSelect a new video to get started...", flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        #print("Please provide a video path as an argument.")
        sys.exit(1)
    video_path = sys.argv[1]
    main(video_path)