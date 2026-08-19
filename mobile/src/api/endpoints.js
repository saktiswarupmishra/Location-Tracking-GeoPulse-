/**
 * GeoPulse — Location & Sharing API Modules
 */

import api from './client';

export const locationApi = {
  getMyLocation: () => api.get('/locations/me'),
  getLocation: (userId) => api.get(`/locations/${userId}`),
  getHistory: (userId, params) => api.get(`/locations/${userId}/history`, { params }),
  deleteHistory: (params) => api.delete('/locations/history', { params }),
};

export const sharingApi = {
  sendRequest: (targetPhone, permissions, duration) =>
    api.post('/sharing/request', {
      target_phone: targetPhone,
      permissions,
      duration,
    }),

  respondToRequest: (shareId, action) =>
    api.post(`/sharing/${shareId}/${action}`), // accept | reject

  stopSharing: (shareId) =>
    api.post(`/sharing/${shareId}/stop`),

  getShares: () => api.get('/sharing'),

  getPendingRequests: () => api.get('/sharing/pending'),
};

export const userApi = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
  searchByPhone: (phone) => api.get('/users/search', { params: { phone } }),
};

export const geofenceApi = {
  getGeofences: () => api.get('/geofences'),
  createGeofence: (data) => api.post('/geofences', data),
  deleteGeofence: (id) => api.delete(`/geofences/${id}`),
};

export const sosApi = {
  trigger: (data) => api.post('/sos', data),
  acknowledge: (id) => api.post(`/sos/${id}/acknowledge`),
  resolve: (id) => api.post(`/sos/${id}/resolve`),
  getActive: () => api.get('/sos/active'),
};

export const privacyApi = {
  blockUser: (userId) => api.post(`/users/block/${userId}`),
  unblockUser: (userId) => api.delete(`/users/block/${userId}`),
  reportUser: (data) => api.post('/users/report', data),
  deleteAccount: () => api.delete('/users/me'),
};
