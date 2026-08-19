/**
 * GeoPulse — Auth API Module
 */

import api, { setTokens, clearTokens } from './client';

export const authApi = {
  sendOtp: (phone) =>
    api.post('/auth/send-otp', { phone }),

  verifyOtp: async (phone, code, name, deviceId, platform) => {
    const { data } = await api.post('/auth/verify-otp', {
      phone,
      code,
      name,
      device_id: deviceId,
      platform,
    });
    await setTokens(data.access_token, data.refresh_token);
    return data;
  },

  logout: async (refreshToken) => {
    try {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    } catch (e) {
      // Best effort
    }
    await clearTokens();
  },

  getWsTicket: () => api.post('/auth/ws-ticket'),
};

export default authApi;
