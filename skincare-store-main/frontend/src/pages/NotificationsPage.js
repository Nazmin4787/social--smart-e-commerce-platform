import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { CartContext } from '../context/CartContext';
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../api/socialApi';

const NotificationsPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const { items, total } = useContext(CartContext);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'unread'
  const [cartReminderDismissed, setCartReminderDismissed] = useState(false);

  // Calculate total items in cart
  const totalItems = items.reduce((sum, item) => sum + (item.qty || 1), 0);

  // Helper function to get full image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return '/images/placeholder.png';
    if (imagePath.startsWith('http')) return imagePath;
    return `http://localhost:8000${imagePath.startsWith('/') ? '' : '/'}${imagePath}`;
  };

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');

    try {
      const isRead = filter === 'unread' ? false : null;
      const data = await getNotifications(1, isRead, token);
      setNotifications(data.notifications);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    // Skip API call for message notifications (they're marked read in chat)
    if (String(notificationId).startsWith('msg_')) {
      setNotifications(prev =>
        prev.map(notif =>
          notif.id === notificationId ? { ...notif, is_read: true } : notif
        )
      );
      return;
    }
    
    const token = localStorage.getItem('access_token');

    try {
      await markNotificationRead(notificationId, token);
      setNotifications(prev =>
        prev.map(notif =>
          notif.id === notificationId ? { ...notif, is_read: true } : notif
        )
      );
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    const token = localStorage.getItem('access_token');

    try {
      await markAllNotificationsRead(token);
      setNotifications(prev =>
        prev.map(notif => ({ ...notif, is_read: true }))
      );
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  // Show message for admin users
  if (user && (user.is_staff || user.is_superuser)) {
    return (
      <div className="notifications-page">
        <div className="notifications-container">
          <div className="notifications-header">
            <h1>Notifications</h1>
          </div>
          <div className="search-info" style={{ padding: '3rem', textAlign: 'center', background: 'white', borderRadius: '12px' }}>
            <i className="fas fa-user-shield" style={{ fontSize: '4rem', color: '#e53e3e', marginBottom: '1rem' }}></i>
            <h3 style={{ color: '#2d3748', marginBottom: '0.5rem' }}>Admin Access Only</h3>
            <p style={{ color: '#718096' }}>Notifications are only available to regular users.</p>
            <button 
              onClick={() => navigate('/')} 
              style={{ marginTop: '1.5rem', padding: '0.75rem 1.5rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      handleMarkAsRead(notification.id);
    }
    
    // Navigate based on notification type
    if (notification.notification_type === 'message') {
      navigate('/messages');
    } else {
      navigate(`/users/${notification.actor.id}/profile`);
    }
  };

  const getTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="container" style={{ padding: '40px 20px' }}>
      <div className="notifications-header">
        <h2>
          <i className="fas fa-bell"></i> Notifications
        </h2>
        <div className="notifications-actions">
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="filter-select">
            <option value="all">All</option>
            <option value="unread">Unread</option>
          </select>
          {notifications.some(n => !n.is_read) && (
            <button className="btn-mark-all-read" onClick={handleMarkAllAsRead}>
              Mark All as Read
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-spinner fa-spin" style={{ fontSize: '32px' }}></i>
          <p style={{ marginTop: '10px' }}>Loading notifications...</p>
        </div>
      )}

      {/* Cart Reminder Notification */}
      {!loading && totalItems > 0 && !cartReminderDismissed && (
        <div className="cart-reminder-notification" onClick={() => navigate('/cart')}>
          <div className="cart-reminder-notification-icon">
            <i className="fas fa-shopping-cart"></i>
            <span className="cart-reminder-notification-badge">{totalItems}</span>
          </div>
          <div className="cart-reminder-notification-content">
            <div className="cart-reminder-notification-header">
              <strong>Don't forget your cart!</strong>
              <button 
                className="cart-reminder-dismiss-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setCartReminderDismissed(true);
                }}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
            <p className="cart-reminder-notification-text">
              You have {totalItems} item{totalItems > 1 ? 's' : ''} worth <strong>₹{total.toFixed(2)}</strong> waiting
            </p>
            <div className="cart-reminder-notification-items">
              {items.slice(0, 3).map((item, index) => (
                <img 
                  key={index}
                  src={getImageUrl(item.images?.[0])}
                  alt={item.title}
                  className="cart-reminder-notification-item-img"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.style.display = 'none';
                  }}
                />
              ))}
              {items.length > 3 && (
                <span className="cart-reminder-notification-more">+{items.length - 3}</span>
              )}
            </div>
          </div>
          <div className="cart-reminder-notification-action">
            <i className="fas fa-chevron-right"></i>
          </div>
        </div>
      )}

      {!loading && notifications.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <i className="fas fa-bell-slash" style={{ fontSize: '48px', color: '#ccc' }}></i>
          <p style={{ marginTop: '20px', color: '#999' }}>
            {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
          </p>
        </div>
      )}

      {!loading && notifications.length > 0 && (
        <div className="notifications-list">
          {notifications.map(notification => (
            <div
              key={notification.id}
              className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
              onClick={() => handleNotificationClick(notification)}
            >
              <div className="notification-avatar">
                <i className={`fas ${notification.notification_type === 'message' ? 'fa-comment-dots' : 'fa-user-circle'}`}></i>
              </div>
              <div className="notification-content">
                <p>
                  <strong>{notification.actor.name}</strong> {notification.message}
                </p>
                <span className="notification-time">{getTimeAgo(notification.created_at)}</span>
              </div>
              {!notification.is_read && (
                <div className="notification-unread-dot"></div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;
