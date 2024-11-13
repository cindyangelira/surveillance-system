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
    
    # analysis data
    num_people = Column(Integer)
    violence_type = Column(String)
    weapons_present = Column(Boolean, default=False)
    weapon_types = Column(JSON)  # array of weapon types
    risk_level = Column(String)  # 'low', 'medium', 'high'
    terrain_context = Column(String)
    recommended_actions = Column(JSON)  # array of actions
    
    # detection data
    detection_confidence = Column(Float)
    detection_data = Column(JSON)  # raw detection data
    
    # image data (stored as path or URL)
    image_path = Column(String)
    
    # relationships
    analytics = relationship("EventAnalytics", back_populates="event", uselist=False)

class EventAnalytics(Base):
    __tablename__ = "event_analytics"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    response_time = Column(Float) 
    event_duration = Column(Float) 
    
    zone_risk_level = Column(String)
    nearby_events_count = Column(Integer)
    
    severity_score = Column(Float)
    confidence_score = Column(Float)
    
    event = relationship("Event", back_populates="analytics")

def init_db(engine):
    Base.metadata.create_all(bind=engine)