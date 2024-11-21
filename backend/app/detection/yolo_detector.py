# backend/app/detection/yolo_detector.py
from ultralytics import YOLO
from ..config import settings

class ViolenceDetector:
    def __init__(self):
        """Initialize YOLO model for violence detection"""
        self.model = YOLO(settings.YOLO_MODEL_PATH)
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        
        # Map class indices to labels
        self.classes = {
            0: "NonViolence",
            1: "Violence"
        }
    
    async def detect(self, frame):
        """
        Run violence detection on a frame
        Returns only Violence detections above threshold
        """
        results = self.model(frame, conf=self.confidence_threshold)
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                class_name = self.classes[class_id]
                
                # Only process Violence detections
                if class_name == "Violence":
                    detection = {
                        'confidence': float(box.conf[0]),
                        'class': class_name,
                        'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2] format
                    }
                    detections.append(detection)
        
        return detections

    def should_trigger_alert(self, detections):
        """
        Determine if detections should trigger an alert
        Returns True if any Violence detection above threshold
        """
        return len(detections) > 0

# Example usage in main.py:

# async def process_frame(frame_data):
#     # Run detection
#     detections = await violence_detector.detect(frame)
    
#     # If violence detected, trigger analysis
#     if violence_detector.should_trigger_alert(detections):
#         analysis = await gemma_analyzer.analyze_incident(frame, detections)
#         alert = await alert_manager.create_alert(detections, analysis)
#         return alert
    
#     return None
