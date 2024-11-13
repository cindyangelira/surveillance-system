import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Clock, AlertTriangle } from 'lucide-react';

export const EventsList = ({ events, onSelectEvent, selectedEventId }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Recent Events
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-[calc(100vh-16rem)] overflow-y-auto">
          {events.map((event) => (
            <Alert
              key={event.properties.id}
              className={`cursor-pointer transition-colors hover:bg-slate-50 ${
                selectedEventId === event.properties.id ? 'border-primary' : ''
              }`}
              onClick={() => onSelectEvent(event)}
            >
              <AlertTitle className="flex items-center justify-between">
                <span>{event.properties.analysis.violence_type}</span>
                <Badge className={`${
                  getRiskColor(event.properties.analysis.risk_level)
                }`}>
                  {event.properties.analysis.risk_level}
                </Badge>
              </AlertTitle>
              <AlertDescription className="flex items-center gap-2 text-slate-500">
                <Clock className="w-4 h-4" />
                {formatTime(event.properties.timestamp)}
              </AlertDescription>
            </Alert>
          ))}
          {events.length === 0 && (
            <div className="text-center text-slate-500 py-4">
              No events detected
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};