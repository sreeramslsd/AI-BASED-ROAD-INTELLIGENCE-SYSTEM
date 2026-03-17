import cv2
import os
import sys
from ultralytics import YOLO
import yt_dlp

# Load model
MODEL_PATH = "runs/pothole_model/weights/best.pt"
model = YOLO(MODEL_PATH)

def run_yolo_on_youtube(youtube_url):
    ydl_opts = {'format': 'best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        stream_url = info['url']

    cap = cv2.VideoCapture(stream_url)
    window_name = "Pothole Detection - HIGH TECH MONITOR"
    
    # --- FORCE BIG SCREEN START ---
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    # This line forces the window to occupy the entire monitor
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # --- FORCE BIG SCREEN END ---

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Inference
        results = model.predict(frame, conf=0.3, verbose=False)
        annotated = results[0].plot()

        # Display
        cv2.imshow(window_name, annotated)

        # UI Controls
        # Check if the window was closed via the 'X' button
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break  
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27: # 'q' or ESC to quit
            break
        # Toggle 'f' to escape full screen if you need to access other apps
        elif key == ord('f'):
            prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN)
            if prop == cv2.WINDOW_FULLSCREEN:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            else:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_yolo_on_youtube(sys.argv[1])
    else:
        # Fallback for testing
        test_link = "https://www.youtube.com/watch?v=Uuaemo4RwFU"
        run_yolo_on_youtube(test_link)