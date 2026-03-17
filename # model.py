# model.py
from ultralytics import YOLO
import cv2

class PotholeDetector:
    def __init__(self, model_path):
        # Initialize the YOLO model with your trained weights
        self.model = YOLO(model_path)
        self.classes = [0]  # Focus only on Potholes

    def detect_and_draw(self, frame):
        # Run inference
        results = self.model.predict(source=frame, conf=0.3, classes=self.classes, verbose=False)
        
        # Process results
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                
                # DRAWING THE LOGIC: Yellow for tracking, Red for critical
                # In the future, we can add the Pinhole math here
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 3) # Yellow Box
                cv2.putText(frame, "POTHOLE DETECTED", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return frame