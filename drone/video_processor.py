# drone/video_processor.py
import cv2
import torch
import numpy as np
from PIL import Image
import threading
from queue import Queue
from typing import Optional, Dict, Any, List, Tuple
import time
from dataclasses import dataclass
import logging

@dataclass
class ProcessedFrame:
    frame: np.ndarray
    detections: Dict[str, Any]
    timestamp: float
    violence_detected: bool

class VideoProcessor:
    def __init__(self, model_path: str, device: str = 'cpu', 
                 confidence_threshold: float = 0.5,
                 violence_threshold: float = 0.7):
        self.model = torch.jit.load(model_path)
        self.model.to(device)
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.violence_threshold = violence_threshold
        
        self.frame_queue = Queue(maxsize=10)
        self.result_queue = Queue(maxsize=10)
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # define class mappings for your violence detection model
        self.classes = {
            0: 'person',
            1: 'fighting',
            2: 'punching',
            3: 'kicking',
            4: 'weapon',
            5: 'knife',
            6: 'gun',
            7: 'aggressive_gesture',
            8: 'fallen_person',
            9: 'group_violence'
        }
        
        # define violence-related classes
        self.violence_classes = {1, 2, 3, 7, 9}  
        self.weapon_classes = {4, 5, 6}         

    def start(self, video_source=0):
        """Start video processing"""
        self.running = True
        self.capture = cv2.VideoCapture(video_source)
        

        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.process_thread = threading.Thread(target=self._process_frames)
        
        self.capture_thread.start()
        self.process_thread.start()
        
        self.logger.info("Video processor started")

    def _capture_frames(self):
        """Continuously capture frames from the video source"""
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                self.logger.warning("Failed to capture frame")
                continue
                
            if not self.frame_queue.full():
                self.frame_queue.put((frame, time.time()))
            else:
                self.logger.debug("Frame queue full, skipping frame")
            
            time.sleep(0.01)  # prevent excessive CPU usage

    def _process_frames(self):
        """Process frames with YOLO model"""
        while self.running:
            if self.frame_queue.empty():
                time.sleep(0.01)
                continue
            
            frame, timestamp = self.frame_queue.get()
            
            try:
                input_tensor = self._preprocess_frame(frame)
                
                with torch.no_grad():
                    predictions = self.model(input_tensor)
                
                detections = self._process_predictions(predictions, frame)
                
                violence_detected = self._analyze_violence(detections)
                
                result = ProcessedFrame(
                    frame=frame,
                    detections=detections,
                    timestamp=timestamp,
                    violence_detected=violence_detected
                )
                
                if not self.result_queue.full():
                    self.result_queue.put(result)
                
            except Exception as e:
                self.logger.error(f"Error processing frame: {e}")
                continue

    def _preprocess_frame(self, frame: np.ndarray) -> torch.Tensor:
        """Preprocess frame for YOLO model"""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        input_size = (640, 640)  
        image = cv2.resize(image, input_size)
        image = image.transpose(2, 0, 1)  # HWC to CHW
        image = torch.from_numpy(image).float()
        image /= 255.0  # Normalize to [0,1]
        
        image = image.unsqueeze(0)
        image = image.to(self.device)
        
        return image

    def _process_predictions(self, predictions: torch.Tensor, 
                           original_frame: np.ndarray) -> Dict[str, Any]:
        """Process YOLO predictions into structured format"""
        height, width = original_frame.shape[:2]
        
        predictions = predictions[0].cpu().numpy()
        
        confident_preds = predictions[predictions[:, 4] > self.confidence_threshold]
        
        objects = []
        for pred in confident_preds:
            x1, y1, x2, y2, conf, class_id = pred[:6]
            
            # convert to original frame coordinates
            x1 = int(x1 * width)
            y1 = int(y1 * height)
            x2 = int(x2 * width)
            y2 = int(y2 * height)
            
            class_id = int(class_id)
            class_name = self.classes.get(class_id, 'unknown')
            
            objects.append({
                'class_name': class_name,
                'confidence': float(conf),
                'bbox': [x1, y1, x2, y2],
                'class_id': class_id
            })
        
        return {
            'objects': objects,
            'frame_info': {
                'width': width,
                'height': height,
                'timestamp': time.time()
            }
        }

    def _analyze_violence(self, detections: Dict[str, Any]) -> bool:
        """Analyze detections for signs of violence"""
        if not detections['objects']:
            return False

        violence_scores = []
        has_weapons = False
        
        for obj in detections['objects']:
            class_id = obj['class_id']
            confidence = obj['confidence']
            
            if class_id in self.violence_classes:
                violence_scores.append(confidence)
            
            if class_id in self.weapon_classes:
                has_weapons = True
                violence_scores.append(confidence)
            
            if obj['class_name'] == 'person':
                for other_obj in detections['objects']:
                    if (other_obj['class_name'] == 'person' and 
                        other_obj != obj):
                        distance = self._calculate_box_distance(
                            obj['bbox'],
                            other_obj['bbox']
                        )
                        if distance < 0.2:  # Close proximity threshold
                            violence_scores.append(0.6)  # Base suspicion score
        
        if violence_scores:
            max_score = max(violence_scores)
            return max_score > self.violence_threshold or has_weapons
        
        return False

    def _calculate_box_distance(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate normalized distance between two bounding boxes"""
        center1 = [(bbox1[0] + bbox1[2])/2, (bbox1[1] + bbox1[3])/2]
        center2 = [(bbox2[0] + bbox2[2])/2, (bbox2[1] + bbox2[3])/2]
        
        frame_width = abs(bbox1[2] - bbox1[0])
        frame_height = abs(bbox1[3] - bbox1[1])
        
        distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
        normalized_distance = distance / np.sqrt(frame_width**2 + frame_height**2)
        
        return normalized_distance

    def get_latest_result(self) -> Optional[ProcessedFrame]:
        """Get the latest processed frame result"""
        if self.result_queue.empty():
            return None
        return self.result_queue.get()

    def stop(self):
        """Stop video processing"""
        self.running = False
        if hasattr(self, 'capture'):
            self.capture.release()
        
        # wait for threads to finish
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join()
        if hasattr(self, 'process_thread'):
            self.process_thread.join()
        
        self.logger.info("Video processor stopped")

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()