import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { Alert, AlertTitle, AlertDescription } from './ui/Alert';
import { 
  AlertTriangle, 
  Users, 
  Compass, 
  Building, 
  ArrowUp,
  Navigation, 
  AlertCircle,
  Shield
} from 'lucide-react';

const SituationDisplay = () => {
  // Simulation data
  const eventData = {
    risk_level: 'high',
    analysis: 'Group confrontation with weapon present',
    recommendations: [
      'Alert law enforcement immediately',
      'Monitor all subjects',
      'Track weapon location'
    ],
    context: 'Urban area with high foot traffic'
  };

  const terrainData = {
    terrain_type: 'urban',
    elevation: 45,
    land_use: 'commercial',
    access_points: ['north', 'south'],
    population_density: 'high'
  };

  const getRiskColor = (risk) => {
    switch (risk.toLowerCase()) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-slate-500';
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      {/* Situation Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Incident Assessment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Risk Level</span>
                <Badge className={getRiskColor(eventData.risk_level)}>
                  {eventData.risk_level.toUpperCase()}
                </Badge>
              </div>
              
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-1 text-red-500" />
                <div>
                  <div className="font-medium">Analysis</div>
                  <div className="text-sm text-slate-600">{eventData.analysis}</div>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Users className="w-4 h-4 mt-1" />
                <div>
                  <div className="font-medium">Context</div>
                  <div className="text-sm text-slate-600">{eventData.context}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Terrain Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building className="w-5 h-5 text-blue-500" />
              Location Context
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Compass className="w-4 h-4 text-blue-500" />
                  <div>
                    <div className="text-sm font-medium">Terrain</div>
                    <div className="text-sm text-slate-600">{terrainData.terrain_type}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <ArrowUp className="w-4 h-4 text-blue-500" />
                  <div>
                    <div className="text-sm font-medium">Elevation</div>
                    <div className="text-sm text-slate-600">{terrainData.elevation}m</div>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Building className="w-4 h-4 mt-1 text-blue-500" />
                <div>
                  <div className="text-sm font-medium">Land Use</div>
                  <div className="text-sm text-slate-600">
                    {terrainData.land_use.charAt(0).toUpperCase() + terrainData.land_use.slice(1)}
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Navigation className="w-4 h-4 mt-1 text-blue-500" />
                <div>
                  <div className="text-sm font-medium">Access Points</div>
                  <div className="flex gap-2 mt-1">
                    {terrainData.access_points.map((point) => (
                      <Badge key={point} variant="secondary">
                        {point.toUpperCase()}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-500" />
                <div>
                  <div className="text-sm font-medium">Population Density</div>
                  <div className="text-sm text-slate-600">
                    {terrainData.population_density.toUpperCase()}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-500" />
            Recommended Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {eventData.recommendations.map((recommendation, index) => (
              <div
                key={index}
                className="bg-slate-50 p-4 rounded-lg border border-slate-200"
              >
                <div className="flex items-start gap-2">
                  <div className="w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center flex-shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-sm">{recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Simple Terrain Visualization */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-purple-500" />
            Terrain Visualization
          </CardTitle>
        </CardHeader>
        <CardContent>
          <svg viewBox="0 0 400 200" className="w-full h-48 border rounded-lg">
            {/* Background */}
            <rect width="400" height="200" fill="#f8fafc" />
            
            {/* Grid lines */}
            <g className="text-slate-200">
              {Array.from({ length: 20 }).map((_, i) => (
                <line
                  key={`v-${i}`}
                  x1={i * 20}
                  y1="0"
                  x2={i * 20}
                  y2="200"
                  stroke="currentColor"
                  strokeWidth="1"
                />
              ))}
              {Array.from({ length: 10 }).map((_, i) => (
                <line
                  key={`h-${i}`}
                  x1="0"
                  y1={i * 20}
                  x2="400"
                  y2={i * 20}
                  stroke="currentColor"
                  strokeWidth="1"
                />
              ))}
            </g>

            {/* Buildings representation */}
            <g className="text-blue-200">
              {Array.from({ length: 5 }).map((_, i) => (
                <rect
                  key={`b-${i}`}
                  x={50 + i * 70}
                  y={50}
                  width="40"
                  height="40"
                  fill="currentColor"
                  stroke="#60a5fa"
                  strokeWidth="2"
                />
              ))}
            </g>

            {/* Access points */}
            <g className="text-green-500">
              <circle cx="200" cy="20" r="8" fill="currentColor" /> {/* North */}
              <circle cx="200" cy="180" r="8" fill="currentColor" /> {/* South */}
            </g>

            {/* Incident location */}
            <circle
              cx="200"
              cy="100"
              r="12"
              fill="#ef4444"
              opacity="0.7"
              className="animate-ping"
            />
            <circle
              cx="200"
              cy="100"
              r="8"
              fill="#ef4444"
            />
          </svg>
        </CardContent>
      </Card>
    </div>
  );
};

export default SituationDisplay;