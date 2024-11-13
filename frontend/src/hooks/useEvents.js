// src/hooks/useEvents.js
import { useState, useEffect } from 'react';
import { fetchEvents, subscribeToEvents } from '../services/api';

export const useEvents = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isSubscribed = true;

    const loadEvents = async () => {
      try {
        setLoading(true);
        const data = await fetchEvents();
        if (isSubscribed) {
          setEvents(data.features);
          setError(null);
        }
      } catch (err) {
        if (isSubscribed) {
          setError(err.message);
        }
      } finally {
        if (isSubscribed) {
          setLoading(false);
        }
      }
    };

    const handleNewEvent = (event) => {
      if (isSubscribed) {
        setEvents(prev => [...prev, event]);
      }
    };

    // Initial load
    loadEvents();

    // Subscribe to real-time updates
    const unsubscribe = subscribeToEvents(handleNewEvent);

    // Cleanup
    return () => {
      isSubscribed = false;
      unsubscribe();
    };
  }, []);

  return { events, loading, error };
};