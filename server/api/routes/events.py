from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from geoalchemy2.functions import ST_AsGeoJSON
import json

from ...database import get_db
from ...models import Event, EventAnalytics
from ..schemas.events import (
    EventCreate, 
    EventResponse, 
    EventUpdate,
    EventAnalyticsResponse
)

router = APIRouter()

@router.post("/events", response_model=EventResponse)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    db_event = Event(
        timestamp=event.timestamp,
        location=f'POINT({event.longitude} {event.latitude})',
        terrain_type=event.terrain_type,
        land_use=event.land_use,
        num_people=event.num_people,
        violence_type=event.violence_type,
        weapons_present=event.weapons_present,
        weapon_types=event.weapon_types,
        risk_level=event.risk_level,
        terrain_context=event.terrain_context,
        recommended_actions=event.recommended_actions,
        detection_confidence=event.detection_confidence,
        detection_data=event.detection_data,
        image_path=event.image_path
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Create analytics entry
    analytics = EventAnalytics(
        event_id=db_event.id,
        severity_score=calculate_severity_score(event),
        confidence_score=event.detection_confidence,
        zone_risk_level=calculate_zone_risk(db, event)
    )
    
    db.add(analytics)
    db.commit()
    
    return db_event

@router.get("/events", response_model=List[EventResponse])
async def get_events(
    skip: int = 0,
    limit: int = 100,
    risk_level: Optional[str] = None,
    time_range: Optional[int] = None,  # minutes
    db: Session = Depends(get_db)
):
    """Get events with optional filtering"""
    query = db.query(Event)
    
    if risk_level:
        query = query.filter(Event.risk_level == risk_level)
    
    if time_range:
        time_threshold = datetime.utcnow() - timedelta(minutes=time_range)
        query = query.filter(Event.timestamp >= time_threshold)
    
    events = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()
    return events

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get specific event details"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events/heatmap")
async def get_heatmap_data(
    time_range: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get heatmap data for events"""
    query = db.query(
        Event.location,
        Event.risk_level,
        func.count(Event.id).label('event_count')
    )
    
    if time_range:
        time_threshold = datetime.utcnow() - timedelta(minutes=time_range)
        query = query.filter(Event.timestamp >= time_threshold)
    
    query = query.group_by(Event.location, Event.risk_level)
    
    results = query.all()
    
    heatmap_data = [{
        'location': json.loads(db.scalar(ST_AsGeoJSON(result.location))),
        'risk_level': result.risk_level,
        'weight': result.event_count * get_risk_weight(result.risk_level)
    } for result in results]
    
    return heatmap_data

def calculate_severity_score(event: EventCreate) -> float:
    """Calculate event severity score"""
    base_score = {
        'high': 1.0,
        'medium': 0.6,
        'low': 0.3
    }.get(event.risk_level, 0.3)
    
    # adjust for weapons
    if event.weapons_present:
        base_score *= 1.5
    
    # adjust for number of people
    people_factor = min(event.num_people / 10, 1.0)
    base_score *= (1 + people_factor)
    
    return min(base_score, 1.0)

def calculate_zone_risk(db: Session, event: EventCreate) -> str:
    """Calculate risk level for the zone"""
    # Query nearby events in last hour
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    nearby_events = db.query(Event).filter(
        func.ST_DWithin(
            Event.location,
            f'POINT({event.longitude} {event.latitude})',
            1000  # 1km radius
        ),
        Event.timestamp >= hour_ago
    ).all()
    
    if not nearby_events:
        return 'low'
    
    # calculate average risk
    risk_scores = {
        'high': 3,
        'medium': 2,
        'low': 1
    }
    
    avg_risk = sum(risk_scores[e.risk_level] for e in nearby_events) / len(nearby_events)
    
    if avg_risk >= 2.5:
        return 'high'
    elif avg_risk >= 1.5:
        return 'medium'
    return 'low'

def get_risk_weight(risk_level: str) -> float:
    """Get weight multiplier for risk level"""
    return {
        'high': 1.0,
        'medium': 0.6,
        'low': 0.3
    }.get(risk_level, 0.3)