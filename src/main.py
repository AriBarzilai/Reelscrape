import os
import cv2

cwd = os.getcwd()
print(cwd)

videos_dir = os.path.join(cwd, "data", "videos")
video_path = os.path.join(videos_dir, "1.mp4")
cap = cv2.VideoCapture(video_path)

os.chdir(videos_dir)
save_dir = "frames"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
if not cap.isOpened():
    raise Exception("Could not open video.")

fps = int(cap.get(cv2.CAP_PROP_FPS))
ret, frame = cap.read()

frame_count = 0
while True:
        # Compute frame number to capture based on 0.5 seconds
        frame_number = int(frame_count * fps)
        
        # Set the position in terms of frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        
        if not ret:
            break  # Exit the loop if no more frames to read
        
        #IMAGE PROCESSING for tesseract:
        # 1. Convert to Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 2. Resize Image
        resized = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
        # 3. Noise Removal
        denoised = cv2.medianBlur(resized, 3)
        
        # Save the frame
        frame_filename = os.path.join(save_dir, f"frame_{frame_count}.jpg")
        
        cv2.imwrite(frame_filename, denoised)
        
        frame_count += 1

cap.release()
print("Finished")