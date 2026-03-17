from ultralytics import YOLO
import os

checkpoint = r"runs/pothole_model/weights/last.pt"

if os.path.exists(checkpoint):
    print(f"✅ Found checkpoint: {checkpoint}")
    model = YOLO(checkpoint)

    model.train(
        data="datasets/data/data.yaml",
        epochs=25,          # NEW TOTAL
        batch=8,
        imgsz=640,
        device="cpu",
        project="runs",
        name="pothole_model_v2",  # 🔴 IMPORTANT: new run
        exist_ok=True
    )
else:
    print("❌ Checkpoint not found.")
