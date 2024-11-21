import cv2
import numpy as np
from ..config import settings

class VideoProcessor:
    def __init__(self):
        self.process_every_n_frames = settings.PROCESS_EVERY_N_FRAMES
        
    async def process_stream(self, stream_source):
        """Process video stream and yield frames for analysis"""
        cap = cv2.VideoCapture(stream_source)
        frame_count = 0
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                if frame_count % self.process_every_n_frames == 0:
                    yield {
                        'frame': frame,
                        'frame_number': frame_count,
                        'timestamp': frame_count / cap.get(cv2.CAP_PROP_FPS)
                    }
        
        finally:
            cap.release()