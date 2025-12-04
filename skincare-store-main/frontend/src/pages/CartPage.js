import React, { useContext, useState } from 'react';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:8000/api';

const CartPage = () => {
  const { items, loading, setQuantity, removeItem, subtotal, tax, total, refreshCart } = useContext(CartContext);
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);

  // Helper to get full image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return null;
    if (imagePath.startsWith('http')) return imagePath;
    if (imagePath.startsWith('/media/')) {
      return `http://localhost:8000${imagePath}`;
    }
    return `http://localhost:8000/media/${imagePath}`;
  };

  // Handle checkout
  const handleCheckout = async () => {
    if (processing) return;
    
    setProcessing(true);
    try {
      const token = localStorage.getItem('access_token');
      
      // Format items for backend
      const orderItems = items.map(item => ({
        product: { id: item.product_id || item.id },
        qty: item.qty
      }));
      
      const response = await fetch(`${API_URL}/orders/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          items: orderItems,
          total: total
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Refresh cart to clear items
        if (refreshCart) await refreshCart();
        
        // Show success and navigate to orders
        alert('Order placed successfully! 🎉');
        navigate('/orders');
      } else {
        alert(data.error || 'Failed to create order. Please try again.');
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('An error occurred during checkout. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  if (!user) {
    return (
      <div className="cart-empty-container">
        <div className="cart-empty-content">
          <i className="fas fa-shopping-cart"></i>
          <h2>Your Cart is Empty</h2>
          <p>Please login to view your cart items</p>
          <button className="btn-primary" onClick={() => navigate('/')}>Continue Shopping</button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="cart-loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your cart...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="cart-empty-container">
        <div className="cart-empty-content">
          <i className="fas fa-shopping-cart"></i>
          <h2>Your Cart is Empty</h2>
          <p>Looks like you haven't added anything to your cart yet</p>
          <button className="btn-primary" onClick={() => navigate('/')}>Start Shopping</button>
        </div>
      </div>
    );
  }

  return (
    <div className="cart-page-container">
      <div className="cart-page-wrapper">
        <div className="cart-header">
          <button className="cart-back-btn" onClick={() => navigate(-1)}>
            <i className="fas fa-arrow-left"></i>
          </button>
          <h1 className="cart-title">Your Cart</h1>
          <span className="cart-item-count">{items.length} {items.length === 1 ? 'item' : 'items'}</span>
        </div>

        <div className="cart-content-grid">
          <div className="cart-items-section">
            {items.map(item => {
              const itemImage = item.images && item.images.length > 0 ? getImageUrl(item.images[0]) : null;
              
              return (
              <div key={item.id} className="cart-item-card">
                <div className="cart-item-image-wrapper">
                  {itemImage ? (
                    <img src={itemImage} alt={item.title} className="cart-item-image" />
                  ) : (
                    <div className="cart-item-no-image">
                      <i className="fas fa-image"></i>
                    </div>
                  )}
                </div>
                
                <div className="cart-item-details">
                  <h3 className="cart-item-title">{item.title}</h3>
                  <p className="cart-item-price">${item.price?.toFixed(2)} each</p>
                  
                  <div className="cart-item-actions">
                    <div className="cart-quantity-control">
                      <button 
                        className="quantity-btn quantity-decrease" 
                        onClick={() => setQuantity(item.id, Math.max(1, item.qty - 1))}
                      >
                        <i className="fas fa-minus"></i>
                      </button>
                      <span className="quantity-value">{item.qty}</span>
                      <button 
                        className="quantity-btn quantity-increase" 
                        onClick={() => setQuantity(item.id, item.qty + 1)}
                      >
                        <i className="fas fa-plus"></i>
                      </button>
                    </div>
                    
                    <div className="cart-item-total">${(item.price * item.qty).toFixed(2)}</div>
                  </div>
                </div>
                
                <button 
                  className="cart-item-remove" 
                  onClick={() => removeItem(item.id)}
                  title="Remove item"
                >
                  <i className="fas fa-trash-alt"></i>
                </button>
              </div>
            );
            })}
          </div>

          <div className="cart-summary-section">
            <div className="cart-summary-card">
              <h3 className="cart-summary-title">Price Details</h3>
              
              <div className="cart-summary-rows">
                <div className="cart-summary-row">
                  <span className="summary-label">Bag MRP ({items.length} {items.length === 1 ? 'item' : 'items'})</span>
                  <span className="summary-value">${subtotal.toFixed(2)}</span>
                </div>
                
                <div className="cart-summary-row">
                  <span className="summary-label">
                    <i className="fas fa-shipping-fast"></i> Shipping & Platform Fee
                  </span>
                  <span className="summary-value summary-free">FREE</span>
                </div>
                
                <div className="cart-summary-row">
                  <span className="summary-label">Tax (8%)</span>
                  <span className="summary-value">${tax.toFixed(2)}</span>
                </div>
              </div>
              
              <div className="cart-summary-divider"></div>
              
              <div className="cart-summary-total">
                <span className="total-label">You Pay</span>
                <span className="total-value">${total.toFixed(2)}</span>
              </div>
              
              <button 
                className="cart-checkout-btn" 
                onClick={handleCheckout}
                disabled={processing}
              >
                {processing ? (
                  <>
                    <div className="loading-spinner" style={{width: '20px', height: '20px', borderWidth: '2px'}}></div>
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Proceed</span>
                    <i className="fas fa-arrow-right"></i>
                  </>
                )}
              </button>
              
              <div className="cart-savings-badge">
                <i className="fas fa-tag"></i>
                <span>You're saving ${(0).toFixed(2)} on this order</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartPage;
