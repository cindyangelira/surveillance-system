from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    detection_data = Column(JSON)  # YOLO detections
    analysis = Column(JSON)        # Gemma analysis
    location = Column(JSON)        # Geospatial data
    status = Column(String, default='active')
    latitude = Column(Numeric(10, 8))  # For easier geospatial queries
    longitude = Column(Numeric(11, 8))
    location_name = Column(String)     # Human-readable location
    camera_id = Column(String)