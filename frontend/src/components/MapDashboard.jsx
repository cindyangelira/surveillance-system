import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  MapPin, 
  AlertTriangle, 
  Eye, 
  Clock,
  Shield,
  Camera,
  Maximize2
} from 'lucide-react';
import { useEvents } from '../hooks/useEvents';
import { EventsList } from './EventsList';
import { EventDetails } from './EventDetails';
import { latLongToXY } from '../utils/geoUtils';

const MapVisualization = ({ 
  events, 
  selectedEvent, 
  onEventSelect, 
  width = 800, 
  height = 400 
}) => {
  const svgRef = React.useRef();
  const [transform, setTransform] = useState({ scale: 1, x: 0, y: 0 });

  const getRiskColor = (risk) => {
    switch (risk.toLowerCase()) {
      case 'high': return '#ef4444';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  // Pan and zoom handlers
  const handleWheel = (e) => {
    e.preventDefault();
    const scale = transform.scale * (e.deltaY > 0 ? 0.9 : 1.1);
    setTransform({ ...transform, scale: Math.max(0.5, Math.min(4, scale)) });
  };

  return (
    <div className="relative w-full h-full overflow-hidden bg-slate-100 rounded-lg">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full"
        onWheel={handleWheel}
      >
        {/* Grid lines */}
        <g className="text-slate-200">
          {Array.from({ length: 20 }).map((_, i) => (
            <React.Fragment key={i}>
              <line
                x1={width * (i / 20)}
                y1={0}
                x2={width * (i / 20)}
                y2={height}
                stroke="currentColor"
                strokeWidth="1"
              />
              <line
                x1={0}
                y1={height * (i / 20)}
                x2={width}
                y2={height * (i / 20)}
                stroke="currentColor"
                strokeWidth="1"
              />
            </React.Fragment>
          ))}
        </g>

        {/* Events */}
        <g transform={`scale(${transform.scale}) translate(${transform.x},${transform.y})`}>
          {events.map((event) => {
            const { x, y } = latLongToXY(
              event.geometry.coordinates[1],
              event.geometry.coordinates[0],
              width,
              height
            );
            const isSelected = selectedEvent?.properties.id === event.properties.id;
            const color = getRiskColor(event.properties.analysis.risk_level);

            return (
              <g
                key={event.properties.id}
                transform={`translate(${x},${y})`}
                className="cursor-pointer transition-transform duration-200 hover:scale-150"
                onClick={() => onEventSelect(event)}
              >
                <circle
                  r={isSelected ? 8 : 6}
                  fill={color}
                  className="transition-all duration-200"
                  opacity={0.7}
                />
                {isSelected && (
                  <>
                    <circle
                      r={12}
                      fill="none"
                      stroke={color}
                      strokeWidth="2"
                      opacity={0.5}
                      className="animate-ping"
                    />
                    <line
                      x1="0"
                      y1="-12"
                      x2="0"
                      y2="12"
                      stroke={color}
                      strokeWidth="2"
                    />
                    <line
                      x1="-12"
                      y1="0"
                      x2="12"
                      y2="0"
                      stroke={color}
                      strokeWidth="2"
                    />
                  </>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* Controls */}
      <div className="absolute bottom-4 right-4 flex gap-2">
        <button
          onClick={() => setTransform({ scale: 1, x: 0, y: 0 })}
          className="p-2 bg-white rounded-full shadow hover:bg-slate-50"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white/90 p-2 rounded-lg shadow-sm">
        <div className="text-xs text-slate-600 space-y-1">
          {['High', 'Medium', 'Low'].map((risk) => (
            <div key={risk} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getRiskColor(risk) }}
              />
              <span>{risk} Risk</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const MapDashboard = () => {
  const { events, loading, error } = useEvents();
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [viewMode, setViewMode] = useState('markers');

  const handleEventSelect = (event) => {
    setSelectedEvent(event);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="loading-spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 h-[calc(100vh-4rem)]">
      <div className="md:col-span-2 space-y-4">
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-5 h-5" />
                Surveillance Map
              </div>
              <div className="flex gap-2">
                <Badge
                  className={`cursor-pointer ${
                    viewMode === 'markers' ? 'bg-primary' : 'bg-secondary'
                  }`}
                  onClick={() => setViewMode('markers')}
                >
                  Markers
                </Badge>
                <Badge
                  className={`cursor-pointer ${
                    viewMode === 'heatmap' ? 'bg-primary' : 'bg-secondary'
                  }`}
                  onClick={() => setViewMode('heatmap')}
                >
                  Density
                </Badge>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <MapVisualization
              events={events}
              selectedEvent={selectedEvent}
              onEventSelect={handleEventSelect}
            />
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4 h-full overflow-y-auto">
        <EventsList
          events={events}
          onSelectEvent={handleEventSelect}
          selectedEventId={selectedEvent?.properties.id}
        />
        {selectedEvent && <EventDetails event={selectedEvent} />}
      </div>
    </div>
  );
};

export default MapDashboard;