import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(api.getUser());
  const [loading, setLoading] = useState(false);

  const refreshUser = useCallback(async () => {
    try {
      const res = await api.getProfile();
      if (res.data) {
        const updatedUser = { ...user, ...res.data };
        setUser(updatedUser);
        api.setUser(updatedUser);
      }
    } catch (err) {
      console.error('Failed to refresh user profile:', err);
    }
  }, [user]);

  const login = async (email, password) => {
    const res = await api.login(email, password);
    setUser(res.data);
    return res;
  };

  const register = async (userData) => {
    const res = await api.register(userData);
    setUser(res.data);
    return res;
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  const isAuthenticated = !!user;
  const isEmployee = user?.role === 'EMPLOYEE';
  const isCustomer = user?.role === 'CUSTOMER';
  const kycStatus = user?.kycStatus || 'UNVERIFIED';

  return (
    <AuthContext.Provider value={{
      user, loading, login, register, logout,
      isAuthenticated, isEmployee, isCustomer,
      refreshUser, kycStatus,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
