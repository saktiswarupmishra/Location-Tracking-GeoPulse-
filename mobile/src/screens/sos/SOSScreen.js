/**
 * GeoPulse — SOS Emergency Screen
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Alert,
  Vibration,
  Platform,
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme';
import { sosApi } from '../../api/endpoints';
import { useLocation } from '../../store/LocationContext';

const SOSScreen = () => {
  const { myLocation } = useLocation();
  const [isActive, setIsActive] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [activeAlert, setActiveAlert] = useState(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const countdownTimer = useRef(null);

  useEffect(() => {
    // Check for active alerts on mount
    checkActiveAlerts();
  }, []);

  useEffect(() => {
    if (isActive) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 600,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 600,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    }
  }, [isActive]);

  const checkActiveAlerts = async () => {
    try {
      const { data } = await sosApi.getActive();
      if (data?.length > 0) {
        setActiveAlert(data[0]);
        setIsActive(true);
      }
    } catch (e) {
      // No active alerts
    }
  };

  const startCountdown = () => {
    Vibration.vibrate([0, 500, 200, 500]);
    setCountdown(5);

    countdownTimer.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(countdownTimer.current);
          triggerSOS();
          return 0;
        }
        Vibration.vibrate(100);
        return prev - 1;
      });
    }, 1000);
  };

  const cancelCountdown = () => {
    if (countdownTimer.current) {
      clearInterval(countdownTimer.current);
      countdownTimer.current = null;
    }
    setCountdown(5);
  };

  const triggerSOS = async () => {
    try {
      const { data } = await sosApi.trigger({
        latitude: myLocation?.latitude,
        longitude: myLocation?.longitude,
        message: 'Emergency — I need help!',
      });
      setActiveAlert(data);
      setIsActive(true);
      Vibration.vibrate([0, 1000, 500, 1000, 500, 1000]);
    } catch (e) {
      Alert.alert('Error', 'Failed to send SOS. Please try calling emergency services directly.');
    }
  };

  const resolveAlert = async () => {
    if (!activeAlert) return;

    Alert.alert(
      'Resolve Emergency',
      'Are you sure you want to mark this emergency as resolved?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'I\'m Safe',
          onPress: async () => {
            try {
              await sosApi.resolve(activeAlert.id);
              setIsActive(false);
              setActiveAlert(null);
              Alert.alert('Resolved', 'Your emergency contacts have been notified that you\'re safe.');
            } catch (e) {
              Alert.alert('Error', 'Failed to resolve alert');
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {!isActive ? (
          <>
            <Text style={styles.title}>Emergency SOS</Text>
            <Text style={styles.description}>
              Press and hold the button to send an emergency alert to your
              contacts with your current location.
            </Text>

            <View style={styles.sosArea}>
              <Animated.View style={[styles.sosRing, styles.sosRing3]} />
              <Animated.View style={[styles.sosRing, styles.sosRing2]} />
              <TouchableOpacity
                style={styles.sosButton}
                onLongPress={startCountdown}
                onPressOut={cancelCountdown}
                delayLongPress={500}
                activeOpacity={0.8}>
                <Text style={styles.sosText}>SOS</Text>
                <Text style={styles.sosHint}>Hold to activate</Text>
              </TouchableOpacity>
            </View>

            {countdown < 5 && (
              <View style={styles.countdownContainer}>
                <Text style={styles.countdownText}>{countdown}</Text>
                <Text style={styles.countdownLabel}>
                  Sending alert in {countdown}s...
                </Text>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={cancelCountdown}>
                  <Text style={styles.cancelText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            )}

            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>What happens when you trigger SOS:</Text>
              <Text style={styles.infoItem}>
                📍 Your live location is shared with emergency contacts
              </Text>
              <Text style={styles.infoItem}>
                🔔 All emergency contacts receive an alert notification
              </Text>
              <Text style={styles.infoItem}>
                📱 Your location updates every 5 seconds
              </Text>
            </View>
          </>
        ) : (
          <>
            <Animated.View
              style={[
                styles.activeHeader,
                { transform: [{ scale: pulseAnim }] },
              ]}>
              <Text style={styles.activeIcon}>🆘</Text>
            </Animated.View>
            <Text style={styles.activeTitle}>Emergency Active</Text>
            <Text style={styles.activeDescription}>
              Your emergency contacts are being notified with your live location.
            </Text>

            {myLocation && (
              <View style={styles.locationCard}>
                <Text style={styles.locationLabel}>Current Location</Text>
                <Text style={styles.locationCoords}>
                  {myLocation.latitude?.toFixed(6)}, {myLocation.longitude?.toFixed(6)}
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={styles.resolveButton}
              onPress={resolveAlert}>
              <Text style={styles.resolveText}>I'm Safe — Resolve Alert</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  content: {
    flex: 1,
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...typography.h1,
    color: colors.text.primary,
    marginBottom: spacing.sm,
  },
  description: {
    ...typography.body,
    color: colors.text.secondary,
    textAlign: 'center',
    marginBottom: spacing.xxl,
    maxWidth: 300,
  },

  // SOS Button
  sosArea: {
    width: 200,
    height: 200,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xl,
  },
  sosRing: {
    position: 'absolute',
    borderRadius: 999,
    borderWidth: 2,
  },
  sosRing2: {
    width: 170,
    height: 170,
    borderColor: colors.brand.danger + '30',
  },
  sosRing3: {
    width: 200,
    height: 200,
    borderColor: colors.brand.danger + '15',
  },
  sosButton: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: colors.brand.danger,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.glow(colors.brand.danger),
  },
  sosText: {
    fontSize: 36,
    fontWeight: '900',
    color: colors.text.primary,
    letterSpacing: 4,
  },
  sosHint: {
    ...typography.small,
    color: colors.text.primary,
    opacity: 0.7,
    marginTop: 4,
  },

  // Countdown
  countdownContainer: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  countdownText: {
    fontSize: 64,
    fontWeight: '900',
    color: colors.brand.danger,
  },
  countdownLabel: {
    ...typography.body,
    color: colors.brand.danger,
    marginBottom: spacing.md,
  },
  cancelButton: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.text.secondary,
  },
  cancelText: {
    ...typography.bodyBold,
    color: colors.text.secondary,
  },

  // Info card
  infoCard: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    width: '100%',
  },
  infoTitle: {
    ...typography.bodyBold,
    color: colors.text.primary,
    marginBottom: spacing.md,
  },
  infoItem: {
    ...typography.caption,
    color: colors.text.secondary,
    marginBottom: spacing.sm,
    lineHeight: 22,
  },

  // Active state
  activeHeader: {
    marginBottom: spacing.lg,
  },
  activeIcon: {
    fontSize: 80,
  },
  activeTitle: {
    ...typography.h1,
    color: colors.brand.danger,
    marginBottom: spacing.sm,
  },
  activeDescription: {
    ...typography.body,
    color: colors.text.secondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
    maxWidth: 300,
  },
  locationCard: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    width: '100%',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  locationLabel: {
    ...typography.label,
    color: colors.text.tertiary,
    marginBottom: spacing.xs,
  },
  locationCoords: {
    ...typography.body,
    color: colors.text.primary,
    fontFamily: Platform?.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  resolveButton: {
    backgroundColor: colors.brand.secondary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.full,
    ...shadows.glow(colors.brand.secondary),
  },
  resolveText: {
    ...typography.bodyBold,
    color: colors.text.inverse,
  },
});

export default SOSScreen;
