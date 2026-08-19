/**
 * GeoPulse — Location Tracking Service
 *
 * Background-capable GPS tracking using react-native-geolocation-service.
 */

import Geolocation from 'react-native-geolocation-service';
import { Platform, PermissionsAndroid } from 'react-native';

class LocationTracker {
  constructor() {
    this.watchId = null;
    this.isTracking = false;
    this.onLocationUpdate = null;
    this.onError = null;
  }

  async requestPermissions() {
    if (Platform.OS === 'ios') {
      const status = await Geolocation.requestAuthorization('always');
      return status === 'granted';
    }

    if (Platform.OS === 'android') {
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

      if (fineLocation === PermissionsAndroid.RESULTS.GRANTED) {
        // Request background location for continuous tracking
        if (Platform.Version >= 29) {
          const backgroundLocation = await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.ACCESS_BACKGROUND_LOCATION,
            {
              title: 'Background Location',
              message:
                'Allow GeoPulse to access your location in the background for continuous sharing.',
              buttonPositive: 'Allow',
              buttonNegative: 'Deny',
            }
          );
          return backgroundLocation === PermissionsAndroid.RESULTS.GRANTED;
        }
        return true;
      }
      return false;
    }

    return false;
  }

  startTracking(onUpdate, onError) {
    this.onLocationUpdate = onUpdate;
    this.onError = onError;

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
        this.isTracking = true;
        this.onLocationUpdate?.(location);
      },
      (error) => {
        console.error('[Location] Error:', error);
        this.onError?.(error);
      },
      {
        enableHighAccuracy: true,
        distanceFilter: 5, // meters
        interval: 3000, // ms (Android)
        fastestInterval: 2000, // ms (Android)
        showsBackgroundLocationIndicator: true,
        forceRequestLocation: true,
      }
    );
  }

  stopTracking() {
    if (this.watchId !== null) {
      Geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
    this.isTracking = false;
  }

  async getCurrentPosition() {
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
