// src/services/api.js
const API_BASE_URL = 'http://localhost:8000/api';

export const fetchEvents = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/events`);
    if (!response.ok) {
      throw new Error('Failed to fetch events');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching events:', error);
    throw error;
  }
};

export const fetchEventDetails = async (eventId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/events/${eventId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch event details');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching event details:', error);
    throw error;
  }
};

export const fetchHeatmapData = async (params = {}) => {
  const queryString = new URLSearchParams(params).toString();
  try {
    const response = await fetch(`${API_BASE_URL}/heatmap?${queryString}`);
    if (!response.ok) {
      throw new Error('Failed to fetch heatmap data');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching heatmap data:', error);
    throw error;
  }
};

export const subscribeToEvents = (callback) => {
  const eventSource = new EventSource(`${API_BASE_URL}/events/stream`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    callback(data);
  };

  return () => {
    eventSource.close();
  };
};