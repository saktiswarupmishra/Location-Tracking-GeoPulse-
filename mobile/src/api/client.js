/**
 * GeoPulse — API Client
 *
 * Axios instance with JWT token management,
 * automatic refresh on 401, and request/response interceptors.
 */

import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '../utils/AsyncStorageWeb';

const getBaseUrl = () => {
  if (Platform.OS === 'web' || typeof window !== 'undefined') {
    return 'http://localhost:8000';
  }
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
};

const API_BASE_URL = getBaseUrl();

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Storage keys
const TOKEN_KEYS = {
  ACCESS: '@geopulse/access_token',
  REFRESH: '@geopulse/refresh_token',
};

// ── Token management ──

export const setTokens = async (accessToken, refreshToken) => {
  await AsyncStorage.multiSet([
    [TOKEN_KEYS.ACCESS, accessToken],
    [TOKEN_KEYS.REFRESH, refreshToken],
  ]);
};

export const getTokens = async () => {
  const values = await AsyncStorage.multiGet([TOKEN_KEYS.ACCESS, TOKEN_KEYS.REFRESH]);
  return {
    accessToken: values?.[0]?.[1] || null,
    refreshToken: values?.[1]?.[1] || null,
  };
};

export const clearTokens = async () => {
  await AsyncStorage.multiRemove([TOKEN_KEYS.ACCESS, TOKEN_KEYS.REFRESH]);
};

// ── Request interceptor — attach JWT ──

api.interceptors.request.use(
  async (config) => {
    const { accessToken } = await getTokens();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor — auto-refresh on 401 ──

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { refreshToken } = await getTokens();
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const { data } = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );

        await setTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        await clearTokens();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };
