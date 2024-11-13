from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EventBase(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    terrain_type: str
    land_use: str
    num_people: int = Field(..., ge=0)
    violence_type: str
    weapons_present: bool = False
    weapon_types: Optional[List[str]] = []
    risk_level: RiskLevel
    terrain_context: str
    recommended_actions: List[str]
    detection_confidence: float = Field(..., ge=0, le=1)
    detection_data: Dict[str, Any]
    image_path: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    risk_level: Optional[RiskLevel]
    num_people: Optional[int] = Field(None, ge=0)
    weapons_present: Optional[bool]
    weapon_types: Optional[List[str]]
    recommended_actions: Optional[List[str]]
    detection_confidence: Optional[float] = Field(None, ge=0, le=1)

class EventAnalyticsBase(BaseModel):
    response_time: float
    event_duration: Optional[float]
    zone_risk_level: RiskLevel
    nearby_events_count: int
    severity_score: float = Field(..., ge=0, le=1)
    confidence_score: float = Field(..., ge=0, le=1)

class EventAnalyticsCreate(EventAnalyticsBase):
    event_id: int

class EventAnalyticsResponse(EventAnalyticsBase):
    id: int
    event_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class EventResponse(EventBase):
    id: int
    analytics: Optional[EventAnalyticsResponse]

    class Config:
        orm_mode = True

class HeatmapPoint(BaseModel):
    location: Dict[str, Any]  # GeoJSON Point
    risk_level: RiskLevel
    weight: float = Field(..., ge=0, le=1)

class AnalyticsSummary(BaseModel):
    total_events: int
    average_severity: float
    average_response_time: float
    risk_distribution: Dict[RiskLevel, int]
    weapon_statistics: Dict[str, int]

class HotspotResponse(BaseModel):
    location: Dict[str, Any]  # GeoJSON Point
    event_count: int
    average_severity: float
    recent_events: List[Dict[str, Any]]

class TrendInterval(BaseModel):
    start_time: datetime
    end_time: datetime
    event_count: int
    average_severity: float

class ResponseMetrics(BaseModel):
    risk_level: RiskLevel
    average_response_time: float
    min_response_time: float
    max_response_time: float
    event_count: int