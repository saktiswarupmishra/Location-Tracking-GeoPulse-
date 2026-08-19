/**
 * GeoPulse — Auth Context & Provider
 *
 * Global authentication state management.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '../utils/AsyncStorageWeb';
import { getTokens, clearTokens } from '../api/client';
import { userApi } from '../api/endpoints';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  // Check stored tokens on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const { accessToken } = await getTokens();
      if (accessToken) {
        const { data } = await userApi.getProfile();
        setUser(data);
        setIsAuthenticated(true);
      }
    } catch (e) {
      console.log('Auth check failed:', e.message);
      await clearTokens();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logout = async () => {
    await clearTokens();
    setUser(null);
    setIsAuthenticated(false);
  };

  const refreshProfile = async () => {
    try {
      const { data } = await userApi.getProfile();
      setUser(data);
    } catch (e) {
      console.warn('Profile refresh failed:', e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout,
        refreshProfile,
        checkAuth,
      }}>
      {children}
    </AuthContext.Provider>
  );
};
