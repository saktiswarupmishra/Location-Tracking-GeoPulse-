/**
 * GeoPulse — Vector Icons Web Polyfill
 */

import React from 'react';
import { Text } from 'react-native';

const Icon = ({ name, size = 20, color = '#FFFFFF', style }) => {
  return <Text style={[{ fontSize: size, color }, style]}>📍</Text>;
};

export default Icon;
