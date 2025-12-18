import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';

const CartReminderPopup = () => {
  const { items } = useContext(CartContext);
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [showPopup, setShowPopup] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Helper to get full image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return null;
    if (imagePath.startsWith('http')) return imagePath;
    if (imagePath.startsWith('/media/')) {
      return `http://localhost:8000${imagePath}`;
    }
    return `http://localhost:8000/media/${imagePath}`;
  };

  useEffect(() => {
    // Only show reminder if user is logged in and has items in cart
    if (!user || items.length === 0 || dismissed) {
      setShowPopup(false);
      return;
    }

    // Check if we've shown the popup recently (within 30 minutes)
    const lastShown = localStorage.getItem('cartReminderLastShown');
    const now = Date.now();
    
    if (lastShown && now - parseInt(lastShown) < 30 * 60 * 1000) {
      return; // Don't show if shown within last 30 minutes
    }

    // Show popup after 10 seconds of page load
    const showTimer = setTimeout(() => {
      setShowPopup(true);
      localStorage.setItem('cartReminderLastShown', now.toString());
    }, 10000);

    return () => clearTimeout(showTimer);
  }, [user, items, dismissed]);

  // Auto-hide popup after 8 seconds
  useEffect(() => {
    if (showPopup) {
      const hideTimer = setTimeout(() => {
        setShowPopup(false);
      }, 8000);

      return () => clearTimeout(hideTimer);
    }
  }, [showPopup]);

  const handleGoToCart = () => {
    setShowPopup(false);
    navigate('/cart');
  };

  const handleDismiss = () => {
    setShowPopup(false);
    setDismissed(true);
  };

  if (!showPopup) return null;

  const totalItems = items.reduce((sum, item) => sum + item.qty, 0);
  const cartTotal = items.reduce((sum, item) => sum + (parseFloat(item.price) * item.qty), 0);

  return (
    <div className="cart-reminder-overlay">
      <div className="cart-reminder-popup">
        <button className="cart-reminder-close" onClick={handleDismiss}>
          <i className="fas fa-times"></i>
        </button>
        
        <div className="cart-reminder-icon">
          <i className="fas fa-shopping-cart"></i>
          <span className="cart-reminder-badge">{totalItems}</span>
        </div>
        
        <h3 className="cart-reminder-title">Don't forget your items!</h3>
        
        <p className="cart-reminder-message">
          You have <strong>{totalItems} item{totalItems > 1 ? 's' : ''}</strong> waiting in your cart 
          worth <strong>₹{cartTotal.toFixed(2)}</strong>
        </p>
        
        <div className="cart-reminder-items">
          {items.slice(0, 3).map((item, index) => (
            <div key={index} className="cart-reminder-item">
              <img 
                src={getImageUrl(item.images?.[0])} 
                alt={item.title}
                className="cart-reminder-item-img"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.style.display = 'none';
                }}
              />
              <span className="cart-reminder-item-name">{item.title}</span>
            </div>
          ))}
          {items.length > 3 && (
            <p className="cart-reminder-more">+{items.length - 3} more item{items.length - 3 > 1 ? 's' : ''}</p>
          )}
        </div>
        
        <div className="cart-reminder-actions">
          <button className="cart-reminder-btn-primary" onClick={handleGoToCart}>
            <i className="fas fa-shopping-bag"></i>
            Complete Purchase
          </button>
          <button className="cart-reminder-btn-secondary" onClick={handleDismiss}>
            Maybe Later
          </button>
        </div>
        
        <div className="cart-reminder-progress">
          <div className="cart-reminder-progress-bar"></div>
        </div>
      </div>
    </div>
  );
};

export default CartReminderPopup;
