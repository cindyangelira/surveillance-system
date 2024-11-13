// src/services/eventService.js
import { fetchEvents, fetchEventDetails, fetchHeatmapData } from './api';

class EventService {
  constructor() {
    this.listeners = new Set();
    this.events = [];
    this.isPolling = false;
    this.pollInterval = 5000; // 5 seconds
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notifyListeners() {
    this.listeners.forEach(listener => listener(this.events));
  }

  async startPolling() {
    if (this.isPolling) return;
    this.isPolling = true;
    
    const poll = async () => {
      if (!this.isPolling) return;
      
      try {
        const data = await fetchEvents();
        this.events = data.features;
        this.notifyListeners();
      } catch (error) {
        console.error('Polling error:', error);
      }
      
      setTimeout(poll, this.pollInterval);
    };

    poll();
  }

  stopPolling() {
    this.isPolling = false;
  }

  async getEventDetails(eventId) {
    try {
      return await fetchEventDetails(eventId);
    } catch (error) {
      console.error('Error fetching event details:', error);
      throw error;
    }
  }

  async getHeatmapData(params) {
    try {
      return await fetchHeatmapData(params);
    } catch (error) {
      console.error('Error fetching heatmap data:', error);
      throw error;
    }
  }

  filterEvents(filters) {
    return this.events.filter(event => {
      if (filters.riskLevel && event.properties.analysis.risk_level !== filters.riskLevel) {
        return false;
      }
      if (filters.timeRange) {
        const eventTime = new Date(event.properties.timestamp);
        if (eventTime < filters.timeRange.start || eventTime > filters.timeRange.end) {
          return false;
        }
      }
      return true;
    });
  }

  sortEvents(events, sortBy = 'timestamp') {
    return [...events].sort((a, b) => {
      switch (sortBy) {
        case 'risk':
          const riskOrder = { high: 3, medium: 2, low: 1 };
          return riskOrder[b.properties.analysis.risk_level] - 
                 riskOrder[a.properties.analysis.risk_level];
        case 'timestamp':
        default:
          return new Date(b.properties.timestamp) - new Date(a.properties.timestamp);
      }
    });
  }
}

export const eventService = new EventService();