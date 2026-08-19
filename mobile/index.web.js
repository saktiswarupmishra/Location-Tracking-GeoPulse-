/**
 * GeoPulse — Web Entrypoint
 *
 * Renders the application in a responsive mobile simulator frame on desktop,
 * and full screen on mobile browser viewports.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import App from './src/App';

const initialMetrics = {
  frame: { x: 0, y: 0, width: 420, height: 900 },
  insets: { top: 12, left: 0, right: 0, bottom: 12 },
};

const RootWeb = () => {
  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        backgroundColor: '#050814',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        padding: '16px',
        boxSizing: 'border-box',
      }}>
      <div
        style={{
          width: '100%',
          maxWidth: '420px',
          height: '100%',
          maxHeight: '900px',
          backgroundColor: '#0A0E27',
          borderRadius: '40px',
          border: '8px solid #1E2358',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 50px rgba(108, 92, 231, 0.3)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}>
        {/* Top Speaker / Camera Notch */}
        <div
          style={{
            height: '28px',
            backgroundColor: '#0A0E27',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            flexShrink: 0,
          }}>
          <div
            style={{
              width: '80px',
              height: '14px',
              borderRadius: '10px',
              backgroundColor: '#151A42',
              border: '1px solid #1E2358',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
            }}>
            <div
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '3px',
                backgroundColor: '#00E5A0',
                boxShadow: '0 0 6px #00E5A0',
              }}
            />
            <div
              style={{
                width: '32px',
                height: '3px',
                borderRadius: '2px',
                backgroundColor: '#2D356A',
              }}
            />
          </div>
        </div>

        {/* Main Application Container */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}>
          <SafeAreaProvider initialMetrics={initialMetrics}>
            <App />
          </SafeAreaProvider>
        </div>

        {/* Bottom Home Indicator */}
        <div
          style={{
            height: '16px',
            backgroundColor: '#0A0E27',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
          <div
            style={{
              width: '120px',
              height: '4px',
              borderRadius: '2px',
              backgroundColor: '#2D356A',
            }}
          />
        </div>
      </div>
    </div>
  );
};

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<RootWeb />);
