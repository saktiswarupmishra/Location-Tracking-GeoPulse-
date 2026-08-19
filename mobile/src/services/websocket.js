/**
 * GeoPulse — WebSocket Service
 *
 * Manages the real-time WebSocket connection.
 * Uses ticket-based auth (§15).
 * Supports reconnection with exponential backoff.
 */

import { API_BASE_URL } from '../api/client';
import authApi from '../api/auth';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.listeners = new Map();
    this.reconnectTimer = null;
  }

  /**
   * Connect to WebSocket using ticket-based auth (§15).
   * 1. Request a short-lived ticket from REST API
   * 2. Connect to WS with ticket as query param
   */
  async connect() {
    try {
      // §15 — Get one-time ticket
      const { data } = await authApi.getWsTicket();
      const ticket = data.ticket;

      const wsUrl = API_BASE_URL.replace('http', 'ws');
      this.ws = new WebSocket(`${wsUrl}/ws/location?ticket=${ticket}`);

      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this._emit('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const eventType = message.event;
          this._emit(eventType, message.data);
          this._emit('message', message);
        } catch (e) {
          console.warn('[WS] Parse error:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        this._emit('error', error);
      };

      this.ws.onclose = (event) => {
        console.log('[WS] Closed:', event.code, event.reason);
        this.isConnected = false;
        this._emit('disconnected', { code: event.code, reason: event.reason });

        // Auto-reconnect unless intentionally closed
        if (event.code !== 1000 && event.code !== 4001) {
          this._scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WS] Connection failed:', error);
      this._scheduleReconnect();
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close(1000, 'User disconnect');
      this.ws = null;
    }
    this.isConnected = false;
  }

  // ── Send events ──

  sendLocationUpdate(locationData) {
    this._send({
      event: 'LOCATION_UPDATE',
      data: locationData,
    });
  }

  startLocationSharing() {
    this._send({ event: 'LOCATION_START', data: {} });
  }

  stopLocationSharing() {
    this._send({ event: 'LOCATION_STOP', data: {} });
  }

  pauseSession() {
    this._send({ event: 'LOCATION_SESSION_PAUSE', data: {} });
  }

  resumeSession() {
    this._send({ event: 'LOCATION_SESSION_RESUME', data: {} });
  }

  subscribeToUser(userId) {
    this._send({ event: 'SUBSCRIBE_LOCATION', data: { userId } });
  }

  unsubscribeFromUser(userId) {
    this._send({ event: 'UNSUBSCRIBE_LOCATION', data: { userId } });
  }

  ping() {
    this._send({ event: 'PING', data: {} });
  }

  // ── Event listeners ──

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.listeners.get(event)?.delete(callback);
  }

  off(event, callback) {
    this.listeners.get(event)?.delete(callback);
  }

  // ── Private ──

  _send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  _emit(event, data) {
    this.listeners.get(event)?.forEach((cb) => {
      try {
        cb(data);
      } catch (e) {
        console.warn('[WS] Listener error:', e);
      }
    });
  }

  _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached');
      this._emit('reconnectFailed');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000
    );
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }
}

// Singleton
const wsService = new WebSocketService();
export default wsService;
