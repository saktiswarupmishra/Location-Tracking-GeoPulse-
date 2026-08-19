/**
 * GeoPulse — Theme & Design System
 *
 * Premium dark theme with vibrant accent colors.
 */

export const colors = {
  // Background layers
  bg: {
    primary: '#0A0E27',
    secondary: '#111639',
    tertiary: '#1A1F4E',
    card: '#151A42',
    elevated: '#1E2358',
  },

  // Brand colors
  brand: {
    primary: '#6C5CE7',
    primaryLight: '#A29BFE',
    secondary: '#00E5A0',
    secondaryDark: '#00B87D',
    accent: '#FF6B9D',
    warning: '#FDCB6E',
    danger: '#FF4757',
    info: '#54A0FF',
  },

  // Text
  text: {
    primary: '#FFFFFF',
    secondary: '#B8C1EC',
    tertiary: '#7F8AB8',
    disabled: '#4A5078',
    inverse: '#0A0E27',
  },

  // Map
  map: {
    userMarker: '#6C5CE7',
    sharedMarker: '#00E5A0',
    geofence: '#FF6B9D',
    path: '#A29BFE',
    sos: '#FF4757',
  },

  // Status
  status: {
    online: '#00E5A0',
    offline: '#7F8AB8',
    live: '#00E5A0',
    delayed: '#FDCB6E',
    stale: '#FF6B9D',
  },

  // Gradient pairs
  gradients: {
    brand: ['#6C5CE7', '#A29BFE'],
    success: ['#00E5A0', '#00B87D'],
    danger: ['#FF4757', '#FF6B9D'],
    card: ['#151A42', '#1E2358'],
    sos: ['#FF4757', '#FF2E46'],
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const typography = {
  h1: { fontSize: 32, fontWeight: '800', letterSpacing: -0.5 },
  h2: { fontSize: 24, fontWeight: '700', letterSpacing: -0.3 },
  h3: { fontSize: 20, fontWeight: '600' },
  body: { fontSize: 16, fontWeight: '400', lineHeight: 24 },
  bodyBold: { fontSize: 16, fontWeight: '600' },
  caption: { fontSize: 14, fontWeight: '400' },
  small: { fontSize: 12, fontWeight: '400' },
  label: { fontSize: 14, fontWeight: '600', letterSpacing: 0.5 },
};

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  glow: (color = '#6C5CE7') => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  }),
};

export default { colors, spacing, borderRadius, typography, shadows };
