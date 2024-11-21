from ..database.models import Alert, SessionLocal
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import desc
from .geospatial import GeospatialProcessor

class AlertManager:
    def __init__(self):
        self.geospatial = GeospatialProcessor()
        self.connected_clients = set()  # Store WebSocket connections
    
    async def create_alert(self, detection_data: Dict, analysis: Dict, location: Dict) -> Alert:
        """Create and store new alert with enhanced location data"""
        # Get detailed location info
        location_info = await self.geospatial.get_location_info(
            location.get('latitude'), 
            location.get('longitude')
        )
        
        alert = Alert(
            detection_data=detection_data,
            analysis=analysis,
            location=location_info,
            latitude=location.get('latitude'),
            longitude=location.get('longitude'),
            location_name=location_info.get('address'),
            camera_id=location.get('camera_id')
        )
        
        db = SessionLocal()
        try:
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            # Notify all connected clients
            await self.notify_clients(alert)
            
            return alert
        finally:
            db.close()
    
    async def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """Get recent alerts"""
        db = SessionLocal()
        try:
            return db.query(Alert)\
                    .order_by(desc(Alert.timestamp))\
                    .limit(limit)\
                    .all()
        finally:
            db.close()
    
    async def get_alerts_by_location(self, 
                                   lat: float, 
                                   lon: float, 
                                   radius_km: float = 1, 
                                   limit: int = 100) -> List[Alert]:
        """Get alerts within radius of a point"""
        db = SessionLocal()
        try:
            # Using PostgreSQL's earthdistance extension for geospatial queries
            # You'll need to enable the earthdistance extension in your database
            results = db.execute("""
                SELECT * FROM alerts
                WHERE earth_box(ll_to_earth(:lat, :lon), :radius) @> ll_to_earth(latitude, longitude)
                ORDER BY timestamp DESC
                LIMIT :limit
            """, {
                'lat': lat,
                'lon': lon,
                'radius': radius_km * 1000,  # Convert to meters
                'limit': limit
            }).fetchall()
            
            return [Alert(**dict(r)) for r in results]
        finally:
            db.close()
    
    def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
    
    def remove_client(self, websocket):
        """Remove a WebSocket client"""
        self.connected_clients.remove(websocket)
    
    async def notify_clients(self, alert):
        """Notify all connected clients of new alert"""
        alert_data = {
            'type': 'new_alert',
            'data': {
                'id': alert.id,
                'timestamp': alert.timestamp.isoformat(),
                'detection_data': alert.detection_data,
                'analysis': alert.analysis,
                'location': alert.location,
                'status': alert.status
            }
        }
        
        # Send to all connected clients
        for client in self.connected_clients:
            try:
                await client.send_json(alert_data)
            except Exception as e:
                print(f"Error notifying client: {e}")
                self.remove_client(client)