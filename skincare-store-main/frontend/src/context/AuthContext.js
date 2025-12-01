import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);

  useEffect(() => {
    // Load user data from localStorage on mount
    const storedUser = localStorage.getItem('user');
    const storedAccessToken = localStorage.getItem('accessToken');
    const storedRefreshToken = localStorage.getItem('refreshToken');

    if (storedUser && storedAccessToken) {
      const userData = JSON.parse(storedUser);
      setUser({ ...userData, token: storedAccessToken });
      setAccessToken(storedAccessToken);
      setRefreshToken(storedRefreshToken);
    }
  }, []);

  const login = (userData, access, refresh) => {
    setUser({ ...userData, token: access });
    setAccessToken(access);
    setRefreshToken(refresh);
    
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
  };

  const logout = () => {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    
    localStorage.removeItem('user');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    window.location.href = '/';
  };

  const updateToken = (newAccessToken) => {
    setAccessToken(newAccessToken);
    if (user) {
      setUser({ ...user, token: newAccessToken });
    }
    localStorage.setItem('accessToken', newAccessToken);
  };

  return (
    <AuthContext.Provider value={{ user, accessToken, refreshToken, login, logout, updateToken }}>
      {children}
    </AuthContext.Provider>
  );
};
