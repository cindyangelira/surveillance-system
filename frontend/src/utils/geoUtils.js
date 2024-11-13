// src/utils/geoUtils.js
export const latLongToXY = (lat, long, width, height) => {
    // Convert lat/long to x/y coordinates (Mercator projection)
    const x = (long + 180) * (width / 360);
    const lat_rad = lat * Math.PI / 180;
    const mercN = Math.log(Math.tan((Math.PI / 4) + (lat_rad / 2)));
    const y = (height / 2) - (width * mercN / (2 * Math.PI));
    return { x, y };
  };
  
  export const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };
  
  export const getRiskColor = (risk) => {
    const colors = {
      high: '#ef4444',
      medium: '#eab308',
      low: '#22c55e',
      default: '#6b7280'
    };
    return colors[risk.toLowerCase()] || colors.default;
  };