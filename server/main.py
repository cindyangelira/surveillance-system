# server/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point
import json
from pathlib import Path
import asyncio
import logging
import base64

# Models
class Location(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    heading: float
    terrain_type: str
    land_use: str

class Analysis(BaseModel):
    num_people: int
    violence_type: str
    weapons_present: bool
    weapon_types: Optional[List[str]]
    risk_level: str
    terrain_context: str
    recommended_actions: List[str]

class Event(BaseModel):
    id: Optional[str]
    timestamp: datetime
    location: Location
    analysis: Analysis
    image_data: str  # Base64 encoded image

# Initialize FastAPI
app = FastAPI(title="Drone Surveillance API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize GeoDataFrame for events
events_gdf = gpd.GeoDataFrame(
    columns=['id', 'timestamp', 'location', 'analysis', 'geometry'],
    geometry='geometry'
)

@app.post("/api/events")
async def create_event(event: Event):
    """Record a new violence detection event"""
    try:
        # Create geometry point
        point = Point(event.location.longitude, event.location.latitude)
        
        # Add to GeoDataFrame
        new_row = {
            'id': str(len(events_gdf)),
            'timestamp': event.timestamp,
            'location': event.location.dict(),
            'analysis': event.analysis.dict(),
            'geometry': point
        }
        
        events_gdf.loc[len(events_gdf)] = new_row
        
        # Save image
        image_path = Path(f"data/images/{new_row['id']}.jpg")
        save_image(event.image_data, image_path)
        
        return {"id": new_row['id']}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def get_events(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    risk_level: Optional[str] = None
):
    """Get filtered events"""
    filtered_gdf = events_gdf.copy()
    
    if start_time:
        filtered_gdf = filtered_gdf[filtered_gdf['timestamp'] >= start_time]
    if end_time:
        filtered_gdf = filtered_gdf[filtered_gdf['timestamp'] <= end_time]
    if risk_level:
        filtered_gdf = filtered_gdf[
            filtered_gdf['analysis'].apply(lambda x: x['risk_level'] == risk_level)
        ]
    
    # Convert to GeoJSON
    geojson = filtered_gdf.to_crs(epsg=4326).__geo_interface__
    
    return {
        "type": "FeatureCollection",
        "features": geojson['features']
    }

@app.get("/api/events/{event_id}")
async def get_event(event_id: str):
    """Get details for a specific event"""
    event = events_gdf[events_gdf['id'] == event_id]
    if event.empty:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get image data
    image_path = Path(f"data/images/{event_id}.jpg")
    image_data = None
    if image_path.exists():
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
    
    return {
        "event": event.iloc[0].to_dict(),
        "image": image_data
    }

@app.get("/api/heatmap")
async def get_heatmap(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Generate heatmap data for events"""
    filtered_gdf = events_gdf.copy()
    
    if start_time:
        filtered_gdf = filtered_gdf[filtered_gdf['timestamp'] >= start_time]
    if end_time:
        filtered_gdf = filtered_gdf[filtered_gdf['timestamp'] <= end_time]
    
    # Create heatmap data
    heatmap_data = []
    for _, row in filtered_gdf.iterrows():
        point = row['geometry']
        intensity = 1 if row['analysis']['risk_level'] == 'low' else \
                   2 if row['analysis']['risk_level'] == 'medium' else 3
        
        heatmap_data.append({
            'lat': point.y,
            'lng': point.x,
            'intensity': intensity
        })
    
    return heatmap_data

def save_image(image_data: str, path: Path):
    """Save base64 encoded image to file"""
    try:
        image_bytes = base64.b64decode(image_data)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(image_bytes)
    except Exception as e:
        logging.error(f"Error saving image: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)