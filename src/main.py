import os
import cv2
import numpy as np
import pytesseract

def setup_directories(base_path, relative_path="data/videos"):
    videos_dir = os.path.join(base_path, relative_path)
    if not os.path.exists(videos_dir):
        raise Exception("Videos directory not found.")
    os.chdir(videos_dir)
    save_dir = "frames"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return videos_dir, save_dir

def setup_video_capture(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video.")
    return cap

def process_frame_for_ocr(frame):
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

def extract_text_from_image(img):
    text = pytesseract.image_to_string(img)
    return text.strip()  # removing any leading or trailing whitespaces

def main():
    cwd = os.getcwd()
    print(cwd)
    
    videos_dir, save_dir = setup_directories(cwd)
    video_path = os.path.join(videos_dir, "1.mp4")
    
    cap = setup_video_capture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = 0
    
    while True:
        frame_number = int(frame_count * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if not ret:
            break
        
        processed_frame = process_frame_for_ocr(frame)
        frame_filename = os.path.join(save_dir, f"frame_{frame_count}.jpg")
        cv2.imwrite(frame_filename, processed_frame)
        
        frame_count += 1

    cap.release()
    print("Finished")

if __name__ == "__main__":
    main()
