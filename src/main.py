import os
import cv2
import numpy as np
import pytesseract
import csv
import re
from thefuzz import fuzz
from thefuzz import process

#sets up the directories for the data and output
def setup_directories(base_path):
    data_dir = os.path.join(base_path, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    videos_dir = os.path.join(data_dir, "videos")
    if not os.path.exists(videos_dir):
         os.makedirs(videos_dir)
    os.chdir(videos_dir)
    output_dir = os.path.join(base_path, "data", "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return videos_dir, output_dir

# loads the video for processing
def setup_video_capture(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video. Please ensure there is a video at " + video_path + " and try again.")
    return cap

# follows standard image processing steps to increase OCR accuracy
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

# a helper function to remove likely noise from extracted text
def remove_noise(text):
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

# extracts text from the processed frame and processes it for easier deduplication
def extract_text(frame):
    text = pytesseract.image_to_string(frame)
    text = text.replace("\n", " ")
    text = remove_noise(text)
    text = text.strip()
    return text

# removes duplicate text entries (in a tuple list of (seconds, text)) in a neighborhood (of seconds) by comparing the similarity of the text
def deduplicate_by_proximity(data, time_window=5, similarity_threshold=70):
    to_remove = set()
    total_entries = len(data)
    for i, (timestamp, current_text) in enumerate(data):
        #remove any empty entries (contained only noise and are now empty after removing noise in previous step)
        if not (isinstance(timestamp, str) and isinstance(current_text, str) and current_text):
            to_remove.add(i)
            continue
        # compare current text with the next few entries
        for j in range(i+1, min(i+1+time_window, total_entries)):
            _, next_text = data[j]
            if fuzz.partial_ratio(current_text, next_text) > similarity_threshold:
                to_remove.add(j)

    deduplicated = [entry for i, entry in enumerate(data) if i not in to_remove]
    return deduplicated

def seconds_to_timestamp(seconds):
    minutes = int(seconds / 60)
    seconds = seconds % 60
    return f"{minutes}:{seconds}"    

def export_to_csv(extracted_texts, output_dir):
    csv_path = os.path.join(output_dir, "output.csv")
    with open(csv_path, "w") as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        writer.writerow(["Time", "Text in English"])
        for seconds, text in extracted_texts:
            writer.writerow([seconds, text])
    print("Finished exporting to csv at ", csv_path)

def main():
    cwd = os.getcwd()
    print("Extracting text from video, please be patient...")
    
    videos_dir, save_dir = setup_directories(cwd)
    video_path = os.path.join(videos_dir, "1.mp4")
    
    cap = setup_video_capture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    video_seconds = 0 # to keep track of the seconds elapsed in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Used to keep track of loading progress
    loading_milestones = {
        int(total_frames/fps * 0.25): "25%",
        int(total_frames/fps * 0.5): "50%",
        int(total_frames/fps * 0.75): "75%"
    }
    
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
        
        if video_seconds in loading_milestones:
            print(f"Processed {loading_milestones[video_seconds]}... {frame_number}/{total_frames} frames")    
        video_seconds += 1
    cap.release()
    
    extracted_texts = deduplicate_by_proximity(extracted_texts)
    print("Finished extracting text from video.")
    print("Exporting to csv...")
    export_to_csv(extracted_texts, save_dir)

if __name__ == "__main__":
    main()
