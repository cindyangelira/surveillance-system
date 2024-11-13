// src/components/EventDetails.jsx
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Shield, MapPin } from 'lucide-react';

export const EventDetails = ({ event }) => {
  if (!event) return null;

  const getRiskColor = (risk) => {
    switch (risk.toLowerCase()) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-slate-500';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Event Details
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden">
            <img
              src="/api/placeholder/400/300"
              alt="Event"
              className="w-full h-full object-cover"
            />
          </div>

          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                <span className="text-sm text-slate-600">
                  {event.properties.location.terrain_type}
                </span>
              </div>
              <Badge className={getRiskColor(event.properties.analysis.risk_level)}>
                {event.properties.analysis.risk_level} Risk
              </Badge>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm">Incident Details</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-slate-600">People Involved:</div>
                <div>{event.properties.analysis.num_people}</div>
                <div className="text-slate-600">Violence Type:</div>
                <div>{event.properties.analysis.violence_type}</div>
                <div className="text-slate-600">Weapons Present:</div>
                <div>{event.properties.analysis.weapons_present ? 'Yes' : 'No'}</div>
                {event.properties.analysis.weapons_present && (
                  <>
                    <div className="text-slate-600">Weapon Types:</div>
                    <div>
                      {event.properties.analysis.weapon_types.join(', ')}
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Recommended Actions
              </h3>
              <ul className="list-disc pl-4 space-y-1 text-sm">
                {event.properties.analysis.recommended_actions.map((action, i) => (
                  <li key={i} className="text-slate-600">{action}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};