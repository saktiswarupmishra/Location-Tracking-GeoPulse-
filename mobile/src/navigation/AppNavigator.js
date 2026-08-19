/**
 * GeoPulse — Navigation Setup
 *
 * Auth flow → Main tab navigator with Map, Contacts, SOS, Profile.
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, View, StyleSheet } from 'react-native';
import { colors, borderRadius } from '../theme';
import { useAuth } from '../store/AuthContext';

// Screens
import LoginScreen from '../screens/auth/LoginScreen';
import MapScreen from '../screens/map/MapScreen';
import ContactsScreen from '../screens/contacts/ContactsScreen';
import SOSScreen from '../screens/sos/SOSScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Tab icon component
const TabIcon = ({ label, emoji, focused }) => (
  <View style={styles.tabIcon}>
    <Text style={[styles.tabEmoji, focused && styles.tabEmojiActive]}>
      {emoji}
    </Text>
    <Text style={[styles.tabLabel, focused && styles.tabLabelActive]}>
      {label}
    </Text>
  </View>
);

// Main Tab Navigator
const MainTabs = () => (
  <Tab.Navigator
    screenOptions={{
      headerShown: false,
      tabBarStyle: {
        backgroundColor: colors.bg.secondary,
        borderTopColor: colors.bg.tertiary,
        borderTopWidth: 1,
        height: 72,
        paddingBottom: 8,
        paddingTop: 8,
      },
      tabBarShowLabel: false,
    }}>
    <Tab.Screen
      name="Map"
      component={MapScreen}
      options={{
        tabBarIcon: ({ focused }) => (
          <TabIcon label="Map" emoji="🗺️" focused={focused} />
        ),
      }}
    />
    <Tab.Screen
      name="Contacts"
      component={ContactsScreen}
      options={{
        headerShown: true,
        headerTitle: 'Contacts',
        headerStyle: { backgroundColor: colors.bg.primary },
        headerTintColor: colors.text.primary,
        tabBarIcon: ({ focused }) => (
          <TabIcon label="Contacts" emoji="👥" focused={focused} />
        ),
      }}
    />
    <Tab.Screen
      name="SOS"
      component={SOSScreen}
      options={{
        headerShown: true,
        headerTitle: 'Emergency',
        headerStyle: { backgroundColor: colors.bg.primary },
        headerTintColor: colors.text.primary,
        tabBarIcon: ({ focused }) => (
          <TabIcon label="SOS" emoji="🆘" focused={focused} />
        ),
      }}
    />
    <Tab.Screen
      name="Profile"
      component={ProfileScreen}
      options={{
        headerShown: true,
        headerTitle: 'Profile',
        headerStyle: { backgroundColor: colors.bg.primary },
        headerTintColor: colors.text.primary,
        tabBarIcon: ({ focused }) => (
          <TabIcon label="Profile" emoji="👤" focused={focused} />
        ),
      }}
    />
  </Tab.Navigator>
);

// Root Navigator
const AppNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.splash}>
        <Text style={styles.splashIcon}>📍</Text>
        <Text style={styles.splashText}>GeoPulse</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <Stack.Screen name="Main" component={MainTabs} />
        ) : (
          <Stack.Screen name="Login" component={LoginScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  tabIcon: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabEmoji: {
    fontSize: 22,
    opacity: 0.5,
  },
  tabEmojiActive: {
    opacity: 1,
  },
  tabLabel: {
    fontSize: 10,
    color: colors.text.tertiary,
    marginTop: 2,
  },
  tabLabelActive: {
    color: colors.brand.primaryLight,
    fontWeight: '600',
  },
  splash: {
    flex: 1,
    backgroundColor: colors.bg.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  splashIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  splashText: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.text.primary,
  },
});

export default AppNavigator;
