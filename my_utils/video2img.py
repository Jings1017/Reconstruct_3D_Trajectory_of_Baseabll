import os
import cv2

def extract_frames(video_path):
    if not os.path.isfile(video_path):
        print("file not found ")
        return
    
    file_name, ext = os.path.splitext(video_path)
    output_folder = f"{file_name}_frames"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    video = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        frame_path = os.path.join(output_folder, f"{file_name.split('/')[-1]}_frame_{frame_count}.png")
        cv2.imwrite(frame_path, frame)
        
        frame_count += 1
    
    video.release()
    
    print(f"Extract {frame_count} frames to the  Folder ：{output_folder}。")



video_path = "../sample/wu/TRAJ-LEFT-PITCHER.mp4"  
extract_frames(video_path)

