from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(Geometry('POINT', srid=4326))
    terrain_type = Column(String)
    land_use = Column(String)
    
    # Analysis data
    num_people = Column(Integer)
    violence_type = Column(String)
    weapons_present = Column(Boolean, default=False)
    weapon_types = Column(JSON)  # Array of weapon types
    risk_level = Column(String)  # 'low', 'medium', 'high'
    terrain_context = Column(String)
    recommended_actions = Column(JSON)  # Array of actions
    
    # Detection data
    detection_confidence = Column(Float)
    detection_data = Column(JSON)  # Raw detection data
    
    # Image data (stored as path or URL)
    image_path = Column(String)
    
    # Relationships
    analytics = relationship("EventAnalytics", back_populates="event", uselist=False)

class EventAnalytics(Base):
    __tablename__ = "event_analytics"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Time-based metrics
    response_time = Column(Float)  # Time between detection and response
    event_duration = Column(Float)  # Duration of the event
    
    # Location-based metrics
    zone_risk_level = Column(String)
    nearby_events_count = Column(Integer)
    
    # Analysis metrics
    severity_score = Column(Float)
    confidence_score = Column(Float)
    
    # Relationship
    event = relationship("Event", back_populates="analytics")

# Create tables
def init_db(engine):
    Base.metadata.create_all(bind=engine)