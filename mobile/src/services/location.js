/**
 * GeoPulse — Location Tracking Service
 *
 * Cross-platform GPS tracking:
 * - Native: react-native-geolocation-service
 * - Web: navigator.geolocation with fallback simulation
 */

import { Platform, PermissionsAndroid } from 'react-native';

let Geolocation = null;
if (Platform.OS !== 'web') {
  try {
    Geolocation = require('react-native-geolocation-service').default || require('react-native-geolocation-service');
  } catch (e) {
    Geolocation = null;
  }
}

class LocationTracker {
  constructor() {
    this.watchId = null;
    this.isTracking = false;
    this.onLocationUpdate = null;
    this.onError = null;
  }

  async requestPermissions() {
    if (Platform.OS === 'web') {
      return true;
    }

    if (Platform.OS === 'ios') {
      if (Geolocation?.requestAuthorization) {
        const status = await Geolocation.requestAuthorization('always');
        return status === 'granted';
      }
      return true;
    }

    if (Platform.OS === 'android') {
      try {
        const fineLocation = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          {
            title: 'Location Permission',
            message:
              'GeoPulse needs access to your location to share it with your authorized contacts.',
            buttonPositive: 'Allow',
            buttonNegative: 'Deny',
          }
        );
        return fineLocation === PermissionsAndroid.RESULTS.GRANTED;
      } catch (e) {
        return false;
      }
    }

    return true;
  }

  startTracking(onUpdate, onError) {
    this.onLocationUpdate = onUpdate;
    this.onError = onError;
    this.isTracking = true;

    // Web geolocation
    if (Platform.OS === 'web' || !Geolocation) {
      if (typeof navigator !== 'undefined' && navigator.geolocation) {
        this.watchId = navigator.geolocation.watchPosition(
          (position) => {
            const loc = {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy || 10,
              altitude: position.coords.altitude,
              heading: position.coords.heading || 0,
              speed: position.coords.speed || 0,
              timestamp: position.timestamp || Date.now(),
            };
            this.onLocationUpdate?.(loc);
          },
          (err) => {
            console.warn('[Location Web] Geolocation error, using default position:', err.message);
            // Default fallback position (e.g. San Francisco / New Delhi)
            this.onLocationUpdate?.({
              latitude: 37.7749,
              longitude: -122.4194,
              accuracy: 15,
              heading: 90,
              speed: 4.5,
              timestamp: Date.now(),
            });
          },
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
        );
      }
      return;
    }

    // Native geolocation
    this.watchId = Geolocation.watchPosition(
      (position) => {
        const location = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude,
          heading: position.coords.heading,
          speed: position.coords.speed,
          timestamp: position.timestamp,
        };
        this.onLocationUpdate?.(location);
      },
      (error) => {
        console.error('[Location] Error:', error);
        this.onError?.(error);
      },
      {
        enableHighAccuracy: true,
        distanceFilter: 5,
        interval: 3000,
        fastestInterval: 2000,
        showsBackgroundLocationIndicator: true,
        forceRequestLocation: true,
      }
    );
  }

  stopTracking() {
    if (this.watchId !== null) {
      if (Platform.OS === 'web' || !Geolocation) {
        if (typeof navigator !== 'undefined' && navigator.geolocation) {
          navigator.geolocation.clearWatch(this.watchId);
        }
      } else if (Geolocation?.clearWatch) {
        Geolocation.clearWatch(this.watchId);
      }
      this.watchId = null;
    }
    this.isTracking = false;
  }

  async getCurrentPosition() {
    if (Platform.OS === 'web' || !Geolocation) {
      return new Promise((resolve) => {
        if (typeof navigator !== 'undefined' && navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (pos) => resolve(pos.coords),
            () => resolve({ latitude: 37.7749, longitude: -122.4194, accuracy: 10 }),
            { enableHighAccuracy: true, timeout: 5000 }
          );
        } else {
          resolve({ latitude: 37.7749, longitude: -122.4194, accuracy: 10 });
        }
      });
    }

    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        (position) => resolve(position.coords),
        (error) => reject(error),
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
      );
    });
  }
}

const locationTracker = new LocationTracker();
export default locationTracker;
