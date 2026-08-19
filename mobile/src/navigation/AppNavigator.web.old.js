/**
 * GeoPulse — Web Navigator
 *
 * Dedicated web navigator with smooth transitions between tabs and auth states.
 */

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../theme';
import { useAuth } from '../store/AuthContext';

// Screens
import LoginScreen from '../screens/auth/LoginScreen';
import MapScreen from '../screens/map/MapScreen';
import ContactsScreen from '../screens/contacts/ContactsScreen';
import GeofenceScreen from '../screens/geofences/GeofenceScreen';
import SOSScreen from '../screens/sos/SOSScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

const WebNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('Map');

  if (isLoading) {
    return (
      <View style={styles.splash}>
        <Text style={styles.splashIcon}>📍</Text>
        <Text style={styles.splashTitle}>GeoPulse</Text>
        <Text style={styles.splashSubtitle}>Privacy-First Location Sharing</Text>
      </View>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  const renderScreen = () => {
    switch (activeTab) {
      case 'Map':
        return <MapScreen navigation={{ navigate: setActiveTab }} />;
      case 'Contacts':
        return <ContactsScreen navigation={{ navigate: setActiveTab }} />;
      case 'Zones':
        return <GeofenceScreen navigation={{ navigate: setActiveTab }} />;
      case 'SOS':
        return <SOSScreen navigation={{ navigate: setActiveTab }} />;
      case 'Profile':
        return <ProfileScreen navigation={{ navigate: setActiveTab }} />;
      default:
        return <MapScreen navigation={{ navigate: setActiveTab }} />;
    }
  };

  const tabs = [
    { key: 'Map', label: 'Map', emoji: '🗺️' },
    { key: 'Contacts', label: 'Contacts', emoji: '👥' },
    { key: 'Zones', label: 'Zones', emoji: '🌐' },
    { key: 'SOS', label: 'SOS', emoji: '🆘' },
    { key: 'Profile', label: 'Profile', emoji: '👤' },
  ];

  return (
    <View style={styles.container}>
      {/* Screen Header (for non-map screens) */}
      {activeTab !== 'Map' && (
        <View style={styles.header}>
          <Text style={styles.headerTitle}>
            {activeTab === 'Zones' ? 'Safe Zones' : activeTab === 'SOS' ? 'Emergency SOS' : activeTab}
          </Text>
        </View>
      )}

      {/* Screen Body */}
      <View style={styles.body}>{renderScreen()}</View>

      {/* Bottom 5-Tab Bar */}
      <View style={styles.tabBar}>
        {tabs.map((t) => {
          const isFocused = activeTab === t.key;
          return (
            <TouchableOpacity
              key={t.key}
              style={styles.tabButton}
              onPress={() => setActiveTab(t.key)}
              activeOpacity={0.7}>
              <Text style={[styles.tabEmoji, isFocused && styles.tabEmojiFocused]}>
                {t.emoji}
              </Text>
              <Text style={[styles.tabLabel, isFocused && styles.tabLabelFocused]}>
                {t.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    height: 52,
    backgroundColor: colors.bg.primary,
    borderBottomWidth: 1,
    borderBottomColor: colors.bg.tertiary,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.text.primary,
  },
  body: {
    flex: 1,
    position: 'relative',
    overflow: 'hidden',
  },
  tabBar: {
    height: 64,
    backgroundColor: colors.bg.secondary,
    borderTopWidth: 1,
    borderTopColor: colors.bg.tertiary,
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingBottom: 4,
    paddingTop: 4,
    zIndex: 9999,
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
  },
  tabEmoji: {
    fontSize: 20,
    opacity: 0.5,
  },
  tabEmojiFocused: {
    opacity: 1,
    transform: [{ scale: 1.15 }],
  },
  tabLabel: {
    fontSize: 10,
    color: colors.text.tertiary,
    marginTop: 2,
    fontWeight: '500',
  },
  tabLabelFocused: {
    color: colors.brand.primaryLight,
    fontWeight: '700',
  },
  splash: {
    flex: 1,
    backgroundColor: colors.bg.primary,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  splashIcon: {
    fontSize: 56,
    marginBottom: 12,
  },
  splashTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.text.primary,
    marginBottom: 4,
  },
  splashSubtitle: {
    fontSize: 14,
    color: colors.text.tertiary,
  },
});

export default WebNavigator;
