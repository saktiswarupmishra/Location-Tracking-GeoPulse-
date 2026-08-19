/**
 * GeoPulse — Map Screen (Main Screen)
 *
 * Displays the live map with user location and shared contacts.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Platform,
} from 'react-native';
import MapView, { Marker, Circle, PROVIDER_GOOGLE } from 'react-native-maps';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme';
import { useLocation } from '../../store/LocationContext';
import { useAuth } from '../../store/AuthContext';

const MapScreen = ({ navigation }) => {
  const { user } = useAuth();
  const {
    isSharing,
    myLocation,
    sharedLocations,
    isWsConnected,
    startSharing,
    stopSharing,
  } = useLocation();
  const mapRef = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Pulse animation for sharing indicator
  useEffect(() => {
    if (isSharing) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.3,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    }
  }, [isSharing]);

  // Center map on user location
  useEffect(() => {
    if (myLocation && mapRef.current) {
      mapRef.current.animateToRegion({
        latitude: myLocation.latitude,
        longitude: myLocation.longitude,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      });
    }
  }, [myLocation?.latitude, myLocation?.longitude]);

  const toggleSharing = () => {
    if (isSharing) {
      stopSharing();
    } else {
      startSharing();
    }
  };

  const getFreshnessColor = (data) => {
    if (!data?.receivedAt) return colors.status.offline;
    const age = (Date.now() - new Date(data.receivedAt).getTime()) / 1000;
    if (age <= 30) return colors.status.live;
    if (age <= 120) return colors.status.delayed;
    return colors.status.stale;
  };

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        provider={PROVIDER_GOOGLE}
        showsUserLocation={false}
        showsMyLocationButton={false}
        customMapStyle={darkMapStyle}
        initialRegion={{
          latitude: 20.5937,
          longitude: 78.9629,
          latitudeDelta: 5,
          longitudeDelta: 5,
        }}>
        {/* My location marker */}
        {myLocation && (
          <>
            <Circle
              center={{
                latitude: myLocation.latitude,
                longitude: myLocation.longitude,
              }}
              radius={myLocation.accuracy || 20}
              fillColor={colors.brand.primary + '20'}
              strokeColor={colors.brand.primary + '60'}
              strokeWidth={1}
            />
            <Marker
              coordinate={{
                latitude: myLocation.latitude,
                longitude: myLocation.longitude,
              }}
              anchor={{ x: 0.5, y: 0.5 }}>
              <View style={styles.myMarker}>
                <View style={styles.myMarkerInner} />
              </View>
            </Marker>
          </>
        )}

        {/* Shared contacts markers */}
        {Array.from(sharedLocations.entries()).map(([userId, data]) => (
          <Marker
            key={userId}
            coordinate={{
              latitude: data.location?.latitude || 0,
              longitude: data.location?.longitude || 0,
            }}
            anchor={{ x: 0.5, y: 0.5 }}
            onPress={() =>
              navigation.navigate('UserDetail', { userId })
            }>
            <View
              style={[
                styles.sharedMarker,
                { borderColor: getFreshnessColor(data) },
              ]}>
              <Text style={styles.sharedMarkerText}>
                {data.name?.[0]?.toUpperCase() || '?'}
              </Text>
            </View>
          </Marker>
        ))}
      </MapView>

      {/* Status Bar */}
      <View style={styles.statusBar}>
        <View style={styles.statusLeft}>
          <View
            style={[
              styles.wsIndicator,
              { backgroundColor: isWsConnected ? colors.status.online : colors.status.offline },
            ]}
          />
          <Text style={styles.statusText}>
            {isWsConnected ? 'Connected' : 'Offline'}
          </Text>
        </View>
        {isSharing && (
          <Animated.View
            style={[
              styles.sharingBadge,
              { transform: [{ scale: pulseAnim }] },
            ]}>
            <Text style={styles.sharingText}>● LIVE</Text>
          </Animated.View>
        )}
      </View>

      {/* FAB — Share Toggle */}
      <TouchableOpacity
        style={[
          styles.fab,
          isSharing && styles.fabActive,
        ]}
        onPress={toggleSharing}
        activeOpacity={0.8}>
        <Text style={styles.fabIcon}>
          {isSharing ? '⏹' : '📡'}
        </Text>
        <Text style={styles.fabText}>
          {isSharing ? 'Stop' : 'Share'}
        </Text>
      </TouchableOpacity>

      {/* Shared contacts list */}
      {sharedLocations.size > 0 && (
        <View style={styles.contactsBar}>
          {Array.from(sharedLocations.entries()).map(([userId, data]) => (
            <TouchableOpacity
              key={userId}
              style={styles.contactChip}
              onPress={() => {
                if (data.location) {
                  mapRef.current?.animateToRegion({
                    latitude: data.location.latitude,
                    longitude: data.location.longitude,
                    latitudeDelta: 0.005,
                    longitudeDelta: 0.005,
                  });
                }
              }}>
              <View
                style={[
                  styles.contactDot,
                  { backgroundColor: getFreshnessColor(data) },
                ]}
              />
              <Text style={styles.contactName} numberOfLines={1}>
                {data.name || userId.slice(0, 6)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
};

// Google Maps dark style
const darkMapStyle = [
  { elementType: 'geometry', stylers: [{ color: '#0A0E27' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#7F8AB8' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0A0E27' }] },
  {
    featureType: 'road',
    elementType: 'geometry',
    stylers: [{ color: '#151A42' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry.stroke',
    stylers: [{ color: '#1E2358' }],
  },
  {
    featureType: 'water',
    elementType: 'geometry',
    stylers: [{ color: '#111639' }],
  },
  {
    featureType: 'poi',
    elementType: 'geometry',
    stylers: [{ color: '#111639' }],
  },
];

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  map: {
    flex: 1,
  },

  // Status bar
  statusBar: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 60 : 40,
    left: spacing.md,
    right: spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg.card + 'DD',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    ...shadows.sm,
  },
  wsIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.sm,
  },
  statusText: {
    ...typography.small,
    color: colors.text.secondary,
  },
  sharingBadge: {
    backgroundColor: colors.brand.danger + '22',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.brand.danger + '44',
  },
  sharingText: {
    color: colors.brand.danger,
    fontWeight: '700',
    fontSize: 12,
  },

  // User markers
  myMarker: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.brand.primary + '40',
    alignItems: 'center',
    justifyContent: 'center',
  },
  myMarkerInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.brand.primary,
  },
  sharedMarker: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.bg.card,
    borderWidth: 3,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.md,
  },
  sharedMarkerText: {
    color: colors.text.primary,
    fontWeight: '700',
    fontSize: 14,
  },

  // FAB
  fab: {
    position: 'absolute',
    bottom: 100,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.brand.primary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.full,
    ...shadows.glow(colors.brand.primary),
  },
  fabActive: {
    backgroundColor: colors.brand.danger,
    ...shadows.glow(colors.brand.danger),
  },
  fabIcon: {
    fontSize: 20,
    marginRight: spacing.sm,
  },
  fabText: {
    ...typography.bodyBold,
    color: colors.text.primary,
  },

  // Contacts bar
  contactsBar: {
    position: 'absolute',
    bottom: 30,
    left: spacing.md,
    right: spacing.md,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  contactChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg.card + 'EE',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    ...shadows.sm,
  },
  contactDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.xs,
  },
  contactName: {
    ...typography.small,
    color: colors.text.primary,
    maxWidth: 80,
  },
});

export default MapScreen;
