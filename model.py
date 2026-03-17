import os
import cv2
from ultralytics import YOLO
from tkinter import Tk, filedialog

# =========================
# BASE DIR & MODEL PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "runs", "pothole_model", "weights", "best.pt")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("❌ best.pt not found! Train your model first.")

# =========================
# PICK VIDEO
# =========================
Tk().withdraw()
VIDEO_PATH = filedialog.askopenfilename(
    title="Select a video",
    filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
)

if not VIDEO_PATH:
    raise RuntimeError("❌ No video selected!")

# =========================
# LOAD MODEL
# =========================
device = "0" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
model = YOLO(MODEL_PATH)

# =========================
# SETUP VIDEO CAPTURE & SAVE
# =========================
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise RuntimeError(f"❌ Cannot open video: {VIDEO_PATH}")

fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

output_path = os.path.join(BASE_DIR, "outputs")
os.makedirs(output_path, exist_ok=True)
save_video_path = os.path.join(output_path, f"detected_{os.path.basename(VIDEO_PATH)}")
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(save_video_path, fourcc, fps, (width, height))

print(f"🎬 Processing video: {VIDEO_PATH}")
print(f"💾 Output will be saved to: {save_video_path}")

# =========================
# PROCESS FRAMES
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(
        source=frame,
        conf=0.3,     # confidence threshold
        imgsz=640,
        device=device,
        save=False,
        verbose=False
    )

    annotated = results[0].plot()
    out.write(annotated)               # save frame to output video
    cv2.imshow("Pothole Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("⏹ Stopped by user")
        break

# =========================
# CLEANUP
# =========================
cap.release()
out.release()
cv2.destroyAllWindows()
print("🎯 Video processing complete!")
print(f"✅ Saved detected video to: {save_video_path}")
