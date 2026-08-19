/**
 * GeoPulse — Web Entrypoint
 *
 * Renders the application in a responsive mobile simulator frame on desktop,
 * and full screen on mobile browser viewports.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import { View, StyleSheet, Platform } from 'react-native';
import App from './src/App';

const RootWeb = () => {
  return (
    <View style={styles.webContainer}>
      <View style={styles.phoneFrame}>
        <View style={styles.statusBarNotch}>
          <View style={styles.cameraDot} />
        </View>
        <View style={styles.appViewport}>
          <App />
        </View>
        <View style={styles.homeBar} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  webContainer: {
    width: '100vw',
    height: '100vh',
    backgroundColor: '#050814',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  phoneFrame: {
    width: '100%',
    maxWidth: 430,
    height: '100%',
    maxHeight: 932,
    backgroundColor: '#0A0E27',
    borderRadius: Platform.OS === 'web' && window.innerWidth > 500 ? 44 : 0,
    borderWidth: Platform.OS === 'web' && window.innerWidth > 500 ? 8 : 0,
    borderColor: '#1E2358',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(108, 92, 231, 0.25)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
  },
  statusBarNotch: {
    height: 32,
    backgroundColor: '#0A0E27',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  cameraDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#151A42',
    borderWidth: 2,
    borderColor: '#1E2358',
  },
  appViewport: {
    flex: 1,
    overflow: 'hidden',
    position: 'relative',
  },
  homeBar: {
    height: 16,
    backgroundColor: '#0A0E27',
    alignItems: 'center',
    justifyContent: 'center',
  },
});

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<RootWeb />);
