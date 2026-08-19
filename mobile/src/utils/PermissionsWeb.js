/**
 * GeoPulse — Permissions Web Polyfill
 */

export const check = async () => 'granted';
export const request = async () => 'granted';
export const RESULTS = {
  UNAVAILABLE: 'unavailable',
  DENIED: 'denied',
  BLOCKED: 'blocked',
  GRANTED: 'granted',
  LIMITED: 'limited',
};

export default { check, request, RESULTS };
