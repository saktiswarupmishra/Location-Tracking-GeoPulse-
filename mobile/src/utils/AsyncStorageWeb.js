/**
 * GeoPulse — AsyncStorage Web Implementation
 *
 * Full drop-in localStorage replacement for @react-native-async-storage/async-storage on Web.
 */

const AsyncStorage = {
  getItem: async (key) => {
    try {
      return typeof window !== 'undefined' && window.localStorage
        ? window.localStorage.getItem(key)
        : null;
    } catch (e) {
      return null;
    }
  },
  setItem: async (key, value) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);
      }
    } catch (e) {}
  },
  removeItem: async (key) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(key);
      }
    } catch (e) {}
  },
  clear: async () => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.clear();
      }
    } catch (e) {}
  },
  getAllKeys: async () => {
    try {
      return typeof window !== 'undefined' && window.localStorage
        ? Object.keys(window.localStorage)
        : [];
    } catch (e) {
      return [];
    }
  },
  multiGet: async (keys) => {
    try {
      return keys.map((key) => [
        key,
        typeof window !== 'undefined' && window.localStorage
          ? window.localStorage.getItem(key)
          : null,
      ]);
    } catch (e) {
      return [];
    }
  },
  multiSet: async (keyValuePairs) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        keyValuePairs.forEach(([key, value]) =>
          window.localStorage.setItem(key, value)
        );
      }
    } catch (e) {}
  },
  multiRemove: async (keys) => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        keys.forEach((key) => window.localStorage.removeItem(key));
      }
    } catch (e) {}
  },
};

export default AsyncStorage;
