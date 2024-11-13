import serial
import pynmea2
import threading
from dataclasses import dataclass
from typing import Optional, Tuple
import rasterio
import geopandas as gpd
from shapely.geometry import Point
import time
import numpy as np
from enum import Enum

class TerrainType(Enum):
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    WATER = "water"
    GRASSLAND = "grassland"
    DESERT = "desert"

@dataclass
class GeospatialData:
    latitude: float
    longitude: float
    altitude: float
    heading: float
    terrain_type: str
    land_use: str
    terrain_confidence: float
    terrain_description: str
    timestamp: float

class GeospatialModule:
    def __init__(self, gps_port: str):
        self.gps_port = gps_port
        self.current_data: Optional[GeospatialData] = None
        self.running = False
        self._lock = threading.Lock()
        
        # Load terrain and land use data
        self.terrain_data = rasterio.open('data/terrain.tif')
        self.land_use_data = gpd.read_file('data/land_use.gpkg')

        # Classification thresholds
        self.ELEVATION_THRESHOLDS = {
            'low': 0,
            'medium': 500,
            'high': 1500,
            'mountain': 2500
        }
        
        self.SLOPE_THRESHOLDS = {
            'flat': 2,
            'gentle': 5,
            'moderate': 15,
            'steep': 30
        }

    def start(self):
        """Start geospatial data collection"""
        self.running = True
        self.gps_thread = threading.Thread(target=self._gps_loop)
        self.gps_thread.start()

    def _gps_loop(self):
        """Main GPS reading loop"""
        with serial.Serial(self.gps_port, 9600, timeout=1) as ser:
            while self.running:
                try:
                    line = ser.readline().decode('ascii', errors='replace')
                    if line.startswith('$GNGGA'):
                        msg = pynmea2.parse(line)
                        self._update_location(msg)
                except Exception as e:
                    print(f"GPS error: {e}")
                time.sleep(0.1)

    def _get_elevation_matrix(self, lon: float, lat: float, window_size: int = 3) -> np.ndarray:
        """Get elevation matrix centered on the point"""
        matrix = np.zeros((window_size, window_size))
        cell_size = abs(self.terrain_data.transform[0])  # Get cell size from transform
        
        for i in range(window_size):
            for j in range(window_size):
                x_offset = (i - window_size//2) * cell_size
                y_offset = (j - window_size//2) * cell_size
                sample_lon = lon + x_offset
                sample_lat = lat + y_offset
                
                try:
                    elevation = list(self.terrain_data.sample([(sample_lon, sample_lat)]))[0]
                    matrix[i, j] = elevation
                except Exception:
                    matrix[i, j] = matrix[i-1, j] if i > 0 else 0  # Use nearby value or 0
                    
        return matrix

    def _calculate_slope(self, elevation_matrix: np.ndarray, cell_size: float) -> float:
        """Calculate slope from elevation matrix"""
        dy, dx = np.gradient(elevation_matrix, cell_size)
        slope = np.arctan(np.sqrt(dx**2 + dy**2))
        return float(np.degrees(slope).mean())

    def _classify_terrain(self, terrain_data: dict) -> Tuple[str, float, str]:
        """
        Classify terrain based on elevation and slope data
        Returns terrain type, confidence score, and description
        """
        elevation = terrain_data['elevation']
        slope = terrain_data['slope']
        
        # initialize scores for each terrain type
        scores = {terrain_type: 0.0 for terrain_type in TerrainType}
        
        # urban classification
        if (elevation < self.ELEVATION_THRESHOLDS['medium'] and 
            slope < self.SLOPE_THRESHOLDS['gentle']):
            scores[TerrainType.URBAN] += 0.8
            scores[TerrainType.SUBURBAN] += 0.4
        
        # mountain classification
        if (elevation > self.ELEVATION_THRESHOLDS['mountain'] or 
            slope > self.SLOPE_THRESHOLDS['steep']):
            scores[TerrainType.MOUNTAIN] += 0.8
        
        # suburban/rural classification
        if (elevation < self.ELEVATION_THRESHOLDS['medium'] and 
            slope < self.SLOPE_THRESHOLDS['moderate']):
            scores[TerrainType.SUBURBAN] += 0.6
            scores[TerrainType.RURAL] += 0.4
        
        # default to rural if no strong matches
        if all(score < 0.4 for score in scores.values()):
            scores[TerrainType.RURAL] += 0.5

        # get terrain type with highest score
        terrain_type = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[terrain_type]
        
        # generate description
        description = self._generate_terrain_description(
            terrain_type,
            elevation,
            slope
        )
        
        return terrain_type.value, confidence, description

    def _generate_terrain_description(self, terrain_type: TerrainType, 
                                   elevation: float, slope: float) -> str:
        """Generate a detailed description of the terrain"""
        descriptions = {
            TerrainType.URBAN: (
                f"Urban area at {elevation:.1f}m elevation. "
                f"Relatively flat terrain with {slope:.1f}° slope."
            ),
            TerrainType.SUBURBAN: (
                f"Suburban region at {elevation:.1f}m elevation. "
                f"Gentle slopes of {slope:.1f}°."
            ),
            TerrainType.RURAL: (
                f"Rural area at {elevation:.1f}m elevation. "
                f"Mixed terrain with {slope:.1f}° slope."
            ),
            TerrainType.MOUNTAIN: (
                f"Mountainous terrain at {elevation:.1f}m elevation. "
                f"Steep slopes of {slope:.1f}°."
            ),
            TerrainType.WATER: (
                f"Water body at {elevation:.1f}m elevation."
            ),
            TerrainType.GRASSLAND: (
                f"Grassland at {elevation:.1f}m elevation. "
                f"Gentle terrain with {slope:.1f}° slope."
            ),
            TerrainType.FOREST: (
                f"Forested area at {elevation:.1f}m elevation. "
                f"Variable terrain with {slope:.1f}° slope."
            ),
            TerrainType.DESERT: (
                f"Desert region at {elevation:.1f}m elevation. "
                f"Terrain slope: {slope:.1f}°."
            )
        }
        return descriptions.get(terrain_type, "Undefined terrain type")

    def _update_location(self, msg):
        """Update location data with terrain analysis"""
        point = Point(msg.longitude, msg.latitude)
        
        # get elevation matrix and calculate slope
        elevation_matrix = self._get_elevation_matrix(msg.longitude, msg.latitude)
        cell_size = abs(self.terrain_data.transform[0])
        elevation = float(elevation_matrix[1, 1])  # Center point elevation
        slope = self._calculate_slope(elevation_matrix, cell_size)
        
        # prepare terrain data for classification
        terrain_data = {
            'elevation': elevation,
            'slope': slope,
            'matrix': elevation_matrix,
            'cell_size': cell_size
        }
        
        # classify terrain
        terrain_type, confidence, description = self._classify_terrain(terrain_data)
        
        # get land use from vector data
        land_use = self.land_use_data[self.land_use_data.contains(point)]
        land_use_type = land_use.iloc[0]['type'] if not land_use.empty else 'unknown'
        
        with self._lock:
            self.current_data = GeospatialData(
                latitude=msg.latitude,
                longitude=msg.longitude,
                altitude=msg.altitude,
                heading=msg.true_heading if hasattr(msg, 'true_heading') else 0.0,
                terrain_type=terrain_type,
                land_use=land_use_type,
                terrain_confidence=confidence,
                terrain_description=description,
                timestamp=time.time()
            )

    def get_current_data(self) -> Optional[GeospatialData]:
        """Get the current geospatial data"""
        with self._lock:
            return self.current_data

    def stop(self):
        """Stop geospatial data collection"""
        self.running = False
        if hasattr(self, 'gps_thread'):
            self.gps_thread.join()