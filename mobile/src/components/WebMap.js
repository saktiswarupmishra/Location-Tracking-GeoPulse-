/**
 * GeoPulse — Interactive Web Map Component
 *
 * Drop-in web replacement for react-native-maps using Leaflet.
 * Displays ultra-sleek dark map tiles, user location beacon, accuracy ring,
 * and shared contact markers.
 */

import React, { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { View, StyleSheet } from 'react-native';
import L from 'leaflet';

export const PROVIDER_GOOGLE = 'google';

export const Marker = ({ coordinate, children, onPress }) => null;
export const Circle = ({ center, radius, fillColor, strokeColor }) => null;

const WebMap = forwardRef(({
  style,
  initialRegion,
  children,
  ...props
}, ref) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const lat = initialRegion?.latitude || 20.5937;
    const lng = initialRegion?.longitude || 78.9629;
    const zoom = 14;

    const map = L.map(mapContainerRef.current, {
      center: [lat, lng],
      zoom: zoom,
      zoomControl: false,
      attributionControl: false,
    });

    // Dark tiles from CartoDB
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    const markersLayer = L.layerGroup().addTo(map);
    markersLayerRef.current = markersLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Expose imperative methods like animateToRegion
  useImperativeHandle(ref, () => ({
    animateToRegion: ({ latitude, longitude, zoom = 15 }) => {
      if (mapInstanceRef.current && latitude && longitude) {
        mapInstanceRef.current.flyTo([latitude, longitude], zoom, {
          duration: 1.2,
        });
      }
    },
    fitToCoordinates: (coords, options) => {
      if (mapInstanceRef.current && coords?.length) {
        const bounds = L.latLngBounds(coords.map((c) => [c.latitude, c.longitude]));
        mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40] });
      }
    },
  }));

  // Render children markers and circles onto the Leaflet map
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layer = markersLayerRef.current;
    if (!map || !layer) return;

    layer.clearLayers();

    React.Children.forEach(children, (child) => {
      if (!child || !child.props) return;

      // Circle overlay
      if (child.type === Circle || child.props.radius !== undefined) {
        const { center, radius = 50, fillColor = 'rgba(108, 92, 231, 0.2)', strokeColor = '#6C5CE7' } = child.props;
        if (center?.latitude && center?.longitude) {
          L.circle([center.latitude, center.longitude], {
            radius: radius,
            color: strokeColor,
            fillColor: fillColor,
            fillOpacity: 0.25,
            weight: 1.5,
          }).addTo(layer);
        }
      }

      // Marker overlay
      if (child.type === Marker || child.props.coordinate !== undefined) {
        const { coordinate, onPress } = child.props;
        if (coordinate?.latitude && coordinate?.longitude) {
          const customIcon = L.divIcon({
            className: 'custom-map-marker',
            html: `
              <div style="
                width: 32px;
                height: 32px;
                border-radius: 16px;
                background: #151A42;
                border: 3px solid #00E5A0;
                box-shadow: 0 0 16px #00E5A0;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #FFFFFF;
                font-weight: 800;
                font-size: 14px;
                cursor: pointer;
                transform: translate(-16px, -16px);
              ">
                📍
              </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
          });

          const marker = L.marker([coordinate.latitude, coordinate.longitude], {
            icon: customIcon,
          }).addTo(layer);

          if (onPress) {
            marker.on('click', onPress);
          }
        }
      }
    });
  }, [children]);

  return (
    <div
      ref={mapContainerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: '#0A0E27',
      }}
    />
  );
});

export default WebMap;
