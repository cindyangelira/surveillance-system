# drone/main.py
import asyncio
from datetime import datetime
import numpy as np
from typing import Dict, Any
from dataclasses import dataclass
import logging
from pathlib import Path

from .video_processor import VideoProcessor
from .geospatial import GeospatialModule
from .llm_processor import GemmaProcessor
from .data_transmitter import DataTransmitter

@dataclass
class DroneConfig:
    yolo_model_path: Path
    gemma_model_path: Path
    api_endpoint: str
    video_source: int = 0
    gps_port: str = '/dev/ttyUSB0'
    update_interval: float = 0.1

class DroneController:
    def __init__(self, config: DroneConfig):
        self.config = config
        self.video_processor = VideoProcessor(
            model_path=str(config.yolo_model_path)
        )
        self.geo_module = GeospatialModule(
            gps_port=config.gps_port
        )
        self.llm_processor = GemmaProcessor(
            model_path=str(config.gemma_model_path)
        )
        self.data_transmitter = DataTransmitter(
            endpoint=config.api_endpoint
        )
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start drone surveillance system"""
        self.running = True
        self.video_processor.start()
        self.geo_module.start()
        
        try:
            while self.running:
                await self.process_frame()
                await asyncio.sleep(self.config.update_interval)
        except Exception as e:
            self.logger.error(f"Error in drone controller: {e}")
            self.stop()

    async def process_frame(self):
        """Process a single frame and associated data"""
        # Get video frame and violence detection
        frame_data = self.video_processor.get_latest_frame()
        if frame_data is None:
            return

        # If violence detected, process the event
        if frame_data.violence_detected:
            await self.process_violence_event(frame_data)

    async def process_violence_event(self, frame_data: Dict[str, Any]):
        """Process and transmit a violence event"""
        # Get geospatial data
        geo_data = self.geo_module.get_current_data()
        
        # Combine frame and geo data
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'frame': frame_data.frame,
            'detections': frame_data.detections,
            'location': {
                'latitude': geo_data.latitude,
                'longitude': geo_data.longitude,
                'altitude': geo_data.altitude,
                'heading': geo_data.heading,
                'terrain_type': geo_data.terrain_type,
                'land_use': geo_data.land_use
            }
        }

        # Process with LLM
        analysis = await self.llm_processor.analyze_event(event_data)
        event_data['analysis'] = analysis

        # Transmit to server
        await self.data_transmitter.send_event(event_data)

    def stop(self):
        """Stop all drone systems"""
        self.running = False
        self.video_processor.stop()
        self.geo_module.stop()

if __name__ == "__main__":
    config = DroneConfig(
        yolo_model_path=Path("models/yolo_model.pt"),
        gemma_model_path=Path("models/gemma"),
        api_endpoint="http://localhost:8000/api/events"
    )
    
    drone = DroneController(config)
    asyncio.run(drone.start())