from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import json
from typing import Dict, Tuple, Optional

class GeospatialProcessor:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="security_monitoring")
        
    async def get_location_info(self, lat: float, lon: float) -> Dict:
        """Get location information from coordinates"""
        try:
            location = self.geolocator.reverse((lat, lon))
            return {
                'latitude': lat,
                'longitude': lon,
                'address': location.address if location else 'Unknown',
                'raw': location.raw if location else {}
            }
        except GeocoderTimedOut:
            return {
                'latitude': lat,
                'longitude': lon,
                'address': 'Location lookup timed out',
                'raw': {}
            }
    
    async def get_nearby_alerts(self, lat: float, lon: float, radius_km: float = 1) -> list:
        """Get alerts within radius of a point"""
        # This will be used by the API to get clustered alerts
        pass