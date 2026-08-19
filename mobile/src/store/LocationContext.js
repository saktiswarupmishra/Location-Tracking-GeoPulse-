/**
 * GeoPulse — Location Context
 *
 * Manages live location tracking state and WebSocket integration.
 */

import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import wsService from '../services/websocket';

const LocationContext = createContext(null);

export const useLocation = () => {
  const context = useContext(LocationContext);
  if (!context) throw new Error('useLocation must be used within LocationProvider');
  return context;
};

export const LocationProvider = ({ children }) => {
  const [isSharing, setIsSharing] = useState(false);
  const [myLocation, setMyLocation] = useState(null);
  const [sharedLocations, setSharedLocations] = useState(new Map());
  const [isWsConnected, setIsWsConnected] = useState(false);
  const sequenceRef = useRef(0);

  useEffect(() => {
    // WebSocket event listeners
    const unsubs = [
      wsService.on('connected', () => setIsWsConnected(true)),
      wsService.on('disconnected', () => setIsWsConnected(false)),
      wsService.on('LOCATION_UPDATE', handleLocationUpdate),
      wsService.on('USER_ONLINE', handleUserOnline),
      wsService.on('USER_OFFLINE', handleUserOffline),
      wsService.on('LOCATION_STARTED', handleLocationStarted),
      wsService.on('LOCATION_STOPPED', handleLocationStopped),
    ];

    return () => unsubs.forEach((unsub) => unsub?.());
  }, []);

  const handleLocationUpdate = (data) => {
    if (!data?.userId) return;
    setSharedLocations((prev) => {
      const next = new Map(prev);
      next.set(data.userId, {
        ...data,
        receivedAt: new Date(),
      });
      return next;
    });
  };

  const handleUserOnline = (data) => {
    setSharedLocations((prev) => {
      const next = new Map(prev);
      const existing = next.get(data.userId);
      if (existing) {
        next.set(data.userId, { ...existing, isOnline: true });
      }
      return next;
    });
  };

  const handleUserOffline = (data) => {
    setSharedLocations((prev) => {
      const next = new Map(prev);
      const existing = next.get(data.userId);
      if (existing) {
        next.set(data.userId, { ...existing, isOnline: false });
      }
      return next;
    });
  };

  const handleLocationStarted = (data) => {
    console.log('[Location] User started sharing:', data.userId);
  };

  const handleLocationStopped = (data) => {
    setSharedLocations((prev) => {
      const next = new Map(prev);
      next.delete(data.userId);
      return next;
    });
  };

  const startSharing = () => {
    setIsSharing(true);
    sequenceRef.current = 0;
    wsService.startLocationSharing();
  };

  const stopSharing = () => {
    setIsSharing(false);
    wsService.stopLocationSharing();
  };

  const sendLocation = (location) => {
    sequenceRef.current += 1;
    const payload = {
      latitude: location.latitude,
      longitude: location.longitude,
      accuracy: location.accuracy,
      speed: location.speed,
      heading: location.heading,
      altitude: location.altitude,
      timestamp: new Date().toISOString(),
      sequence: sequenceRef.current,
    };
    setMyLocation(payload);
    wsService.sendLocationUpdate(payload);
  };

  return (
    <LocationContext.Provider
      value={{
        isSharing,
        myLocation,
        sharedLocations,
        isWsConnected,
        startSharing,
        stopSharing,
        sendLocation,
      }}>
      {children}
    </LocationContext.Provider>
  );
};
