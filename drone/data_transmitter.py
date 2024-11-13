# drone/data_transmitter.py
import aiohttp
import base64
import cv2
import numpy as np
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime

class DataTransmitter:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.retry_delay = 1  # seconds
        self.max_retries = 3

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def send_event(self, event_data: Dict[str, Any]) -> bool:
        """Send event data to server"""
        await self._ensure_session()
        
        try:
            # Prepare image data
            image_data = self._prepare_image(event_data['frame'])
            
            # Prepare payload
            payload = {
                "timestamp": event_data['timestamp'],
                "location": {
                    "latitude": event_data['location']['latitude'],
                    "longitude": event_data['location']['longitude'],
                    "altitude": event_data['location']['altitude'],
                    "heading": event_data['location']['heading'],
                    "terrain_type": event_data['location']['terrain_type'],
                    "land_use": event_data['location']['land_use']
                },
                "analysis": event_data['analysis'],
                "image_data": image_data
            }

            # Send data with retries
            for attempt in range(self.max_retries):
                try:
                    async with self.session.post(self.endpoint, json=payload) as response:
                        if response.status == 200:
                            return True
                        else:
                            self.logger.error(
                                f"Failed to send event (attempt {attempt + 1}/{self.max_retries}): "
                                f"Status {response.status}"
                            )
                except aiohttp.ClientError as e:
                    self.logger.error(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            
            return False

        except Exception as e:
            self.logger.error(f"Error sending event: {e}")
            return False

    def _prepare_image(self, frame: np.ndarray) -> str:
        """Convert frame to base64 encoded string"""
        try:
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            # Convert to base64
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error preparing image: {e}")
            return ""

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None