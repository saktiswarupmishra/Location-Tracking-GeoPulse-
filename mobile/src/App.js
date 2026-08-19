/**
 * GeoPulse — App Entry Point
 */

import React from 'react';
import { StatusBar } from 'react-native';
import { AuthProvider } from './store/AuthContext';
import { LocationProvider } from './store/LocationContext';
import AppNavigator from './navigation/AppNavigator';
import { colors } from './theme';

const App = () => {
  return (
    <AuthProvider>
      <LocationProvider>
        <StatusBar
          barStyle="light-content"
          backgroundColor={colors.bg.primary}
          translucent={false}
        />
        <AppNavigator />
      </LocationProvider>
    </AuthProvider>
  );
};

export default App;
