from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
from geoalchemy2.functions import ST_Distance, ST_AsGeoJSON
import json

from ...database import get_db
from ...models import Event, EventAnalytics

router = APIRouter()

@router.get("/analytics/summary")
async def get_analytics_summary(
    time_range: int = 24,  # hours
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get summary analytics for specified time range"""
    time_threshold = datetime.utcnow() - timedelta(hours=time_range)
    
    # get basic statistics
    stats = db.query(
        func.count(Event.id).label('total_events'),
        func.avg(EventAnalytics.severity_score).label('avg_severity'),
        func.avg(EventAnalytics.response_time).label('avg_response_time')
    ).join(EventAnalytics).filter(Event.timestamp >= time_threshold).first()
    
    # get risk level distribution
    risk_distribution = db.query(
        Event.risk_level,
        func.count(Event.id).label('count')
    ).filter(
        Event.timestamp >= time_threshold
    ).group_by(Event.risk_level).all()
    
    # get weapon type distribution
    weapon_stats = db.query(
        Event.weapon_types,
        func.count(Event.id).label('count')
    ).filter(
        Event.timestamp >= time_threshold,
        Event.weapons_present == True
    ).group_by(Event.weapon_types).all()
    
    return {
        "total_events": stats.total_events,
        "average_severity": float(stats.avg_severity) if stats.avg_severity else 0,
        "average_response_time": float(stats.avg_response_time) if stats.avg_response_time else 0,
        "risk_distribution": {
            level.risk_level: level.count for level in risk_distribution
        },
        "weapon_statistics": {
            json.dumps(stat.weapon_types): stat.count for stat in weapon_stats
        }
    }

@router.get("/analytics/hotspots")
async def get_hotspots(
    min_events: int = 3,
    radius_meters: float = 1000,
    time_range: int = 24,  # hours
    db: Session = Depends(get_db)
):
    """Get event hotspots based on spatial clustering"""
    time_threshold = datetime.utcnow() - timedelta(hours=time_range)
    
    # find clusters of events
    clusters = db.query(
        Event.location,
        func.count(Event.id).label('event_count'),
        func.avg(EventAnalytics.severity_score).label('avg_severity')
    ).join(EventAnalytics).filter(
        Event.timestamp >= time_threshold
    ).group_by(
        Event.location
    ).having(
        func.count(Event.id) >= min_events
    ).all()
    
    # process clusters
    hotspots = []
    for cluster in clusters:
        nearby_events = db.query(Event).filter(
            func.ST_DWithin(
                Event.location,
                cluster.location,
                radius_meters
            ),
            Event.timestamp >= time_threshold
        ).all()
        
        if len(nearby_events) >= min_events:
            hotspots.append({
                "location": json.loads(db.scalar(ST_AsGeoJSON(cluster.location))),
                "event_count": cluster.event_count,
                "average_severity": float(cluster.avg_severity),
                "recent_events": [
                    {
                        "id": event.id,
                        "timestamp": event.timestamp,
                        "risk_level": event.risk_level
                    } for event in nearby_events[:5]  # Last 5 events
                ]
            })
    
    return hotspots

@router.get("/analytics/trends")
async def get_trends(
    time_range: int = 24,  # hours
    interval_minutes: int = 60,
    db: Session = Depends(get_db)
):
    """Get event trends over time"""
    time_threshold = datetime.utcnow() - timedelta(hours=time_range)
    
    # generate time intervals
    intervals = []
    current_time = time_threshold
    while current_time < datetime.utcnow():
        interval_end = current_time + timedelta(minutes=interval_minutes)
        
        # count events in interval
        event_count = db.query(func.count(Event.id)).filter(
            Event.timestamp >= current_time,
            Event.timestamp < interval_end
        ).scalar()
        
        # get average severity
        avg_severity = db.query(
            func.avg(EventAnalytics.severity_score)
        ).join(Event).filter(
            Event.timestamp >= current_time,
            Event.timestamp < interval_end
        ).scalar()
        
        intervals.append({
            "start_time": current_time,
            "end_time": interval_end,
            "event_count": event_count,
            "average_severity": float(avg_severity) if avg_severity else 0
        })
        
        current_time = interval_end
    
    return intervals

@router.get("/analytics/response-metrics")
async def get_response_metrics(
    time_range: int = 24,  # hours
    db: Session = Depends(get_db)
):
    """Get response time metrics"""
    time_threshold = datetime.utcnow() - timedelta(hours=time_range)
    
    metrics = db.query(
        Event.risk_level,
        func.avg(EventAnalytics.response_time).label('avg_response_time'),
        func.min(EventAnalytics.response_time).label('min_response_time'),
        func.max(EventAnalytics.response_time).label('max_response_time'),
        func.count(Event.id).label('event_count')
    ).join(EventAnalytics).filter(
        Event.timestamp >= time_threshold
    ).group_by(Event.risk_level).all()
    
    return {
        "overall_metrics": {
            "risk_levels": {
                metric.risk_level: {
                    "average_response_time": float(metric.avg_response_time) if metric.avg_response_time else 0,
                    "min_response_time": float(metric.min_response_time) if metric.min_response_time else 0,
                    "max_response_time": float(metric.max_response_time) if metric.max_response_time else 0,
                    "event_count": metric.event_count
                } for metric in metrics
            }
        },
        "response_time_distribution": calculate_response_distribution(db, time_threshold)
    }

def calculate_response_distribution(db: Session, time_threshold: datetime):
    """Calculate distribution of response times"""
    ranges = [
        (0, 300),      # 0-5 minutes
        (300, 600),    # 5-10 minutes
        (600, 1800),   # 10-30 minutes
        (1800, 3600),  # 30-60 minutes
        (3600, None)   # Over 60 minutes
    ]
    
    distribution = {}
    for start, end in ranges:
        query = db.query(func.count(EventAnalytics.id)).\
            join(Event).\
            filter(Event.timestamp >= time_threshold)
        
        if end:
            query = query.filter(
                EventAnalytics.response_time >= start,
                EventAnalytics.response_time < end
            )
        else:
            query = query.filter(EventAnalytics.response_time >= start)
        
        count = query.scalar()
        
        if end:
            key = f"{start//60}-{end//60} mins"
        else:
            key = f">{start//60} mins"
            
        distribution[key] = count
    
    return distribution