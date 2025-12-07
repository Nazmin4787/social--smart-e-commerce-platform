import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { getUnreadNotificationsCount } from '../api/socialApi';
import { AuthContext } from '../context/AuthContext';

const NotificationBell = () => {
  const { user } = useContext(AuthContext);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      // Poll every 30 seconds
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchUnreadCount = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const data = await getUnreadNotificationsCount(token);
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  if (!user) return null;

  return (
    <Link to="/notifications" className="notification-bell">
      <i className="fas fa-bell"></i>
      {unreadCount > 0 && (
        <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
      )}
    </Link>
  );
};

export default NotificationBell;
