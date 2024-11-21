# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import os
from pathlib import Path
from datetime import datetime
import asyncio
import logging
from typing import Dict, Optional

from .detection.video_processor import VideoProcessor
from .detection.yolo_detector import ViolenceDetector
from .analysis.gemma_analyzer import analyze_image_for_violence
from .utils.alert_manager import AlertManager
from .utils.geospatial import GeospatialProcessor
from .config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Security Monitoring System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
video_processor = VideoProcessor()
violence_detector = ViolenceDetector()
alert_manager = AlertManager()
geospatial_processor = GeospatialProcessor()

# Create directory for temporary image storage
TEMP_DIR = Path("temp_frames")
TEMP_DIR.mkdir(exist_ok=True)

class StreamManager:
    def __init__(self):
        self.active_streams: Dict[str, dict] = {}
        
    async def add_stream(self, camera_id: str, stream_data: dict):
        self.active_streams[camera_id] = stream_data
        
    async def remove_stream(self, camera_id: str):
        if camera_id in self.active_streams:
            del self.active_streams[camera_id]
            
    def get_stream_data(self, camera_id: str) -> Optional[dict]:
        return self.active_streams.get(camera_id)

stream_manager = StreamManager()

async def save_frame_for_analysis(frame, detection_id: int) -> Optional[Path]:
    """Save frame as temporary image for Gemma analysis"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = TEMP_DIR / f"frame_{detection_id}_{timestamp}.jpg"
    
    try:
        cv2.imwrite(str(image_path), frame)
        return image_path
    except Exception as e:
        logger.error(f"Error saving frame: {e}")
        return None

async def cleanup_temp_image(image_path: Path):
    """Remove temporary image after analysis"""
    try:
        if image_path.exists():
            os.remove(image_path)
    except Exception as e:
        logger.error(f"Error cleaning up temp image: {e}")

async def process_detection(frame, frame_data: dict, stream_data: dict, detection_counter: int):
    """Process a single frame detection"""
    try:
        # Run YOLO detection
        detections = await violence_detector.detect(frame)
        
        if violence_detector.should_trigger_alert(detections):
            # Save frame for Gemma analysis
            image_path = await save_frame_for_analysis(frame, detection_counter)
            
            if image_path:
                try:
                    # Get Gemma analysis
                    analysis = analyze_image_for_violence(str(image_path.relative_to(Path.cwd())))
                    
                    # Get location info
                    location_info = await geospatial_processor.get_location_info(
                        stream_data.get('latitude'),
                        stream_data.get('longitude')
                    )
                    
                    # Create alert
                    alert = await alert_manager.create_alert(
                        detection_data={
                            'frame_number': frame_data['frame_number'],
                            'timestamp': frame_data['timestamp'],
                            'detections': detections,
                            'camera_id': stream_data.get('camera_id')
                        },
                        analysis=analysis,
                        location=location_info
                    )
                    
                    return alert
                    
                finally:
                    await cleanup_temp_image(image_path)
    
    except Exception as e:
        logger.error(f"Error processing detection: {e}")
        return None

@app.websocket("/ws/stream/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for video stream processing"""
    await websocket.accept()
    alert_manager.register_client(websocket)
    
    try:
        # Get initial stream configuration
        stream_data = await websocket.receive_json()
        await stream_manager.add_stream(camera_id, stream_data)
        
        detection_counter = 0
        stream_source = stream_data.get('stream_source')
        
        if not stream_source:
            raise ValueError("No stream source provided")
        
        async for frame_data in video_processor.process_stream(stream_source):
            frame = frame_data['frame']
            detection_counter += 1
            
            alert = await process_detection(
                frame, 
                frame_data, 
                stream_data, 
                detection_counter
            )
            
            if alert:
                # Alert will be automatically sent to all clients by alert_manager
                logger.info(f"Alert created: {alert.id}")
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await stream_manager.remove_stream(camera_id)
        alert_manager.remove_client(websocket)
        await websocket.close()

@app.get("/api/alerts/recent")
async def get_recent_alerts(limit: int = 100):
    """Get recent alerts for initial dashboard load"""
    try:
        alerts = await alert_manager.get_recent_alerts(limit)
        return alerts
    except Exception as e:
        logger.error(f"Error fetching recent alerts: {e}")
        raise HTTPException(status_code=500, detail="Error fetching alerts")

@app.get("/api/alerts/nearby")
async def get_nearby_alerts(lat: float, lon: float, radius_km: float = 1.0, limit: int = 100):
    """Get alerts within specified radius of a location"""
    try:
        alerts = await alert_manager.get_alerts_by_location(lat, lon, radius_km, limit)
        return alerts
    except Exception as e:
        logger.error(f"Error fetching nearby alerts: {e}")
        raise HTTPException(status_code=500, detail="Error fetching nearby alerts")

@app.get("/api/streams/active")
async def get_active_streams():
    """Get list of active camera streams"""
    return {"active_streams": list(stream_manager.active_streams.keys())}

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("Starting Security Monitoring System")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Cleanup temporary files
        for file in TEMP_DIR.glob("frame_*.jpg"):
            os.remove(file)
        TEMP_DIR.rmdir()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )