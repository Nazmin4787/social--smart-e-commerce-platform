import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const OrdersPage = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    fetchOrders();
  }, [user]);

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/orders/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Transform backend data to match frontend expectations
        const transformedOrders = data.map(order => ({
          id: order.id,
          created_at: order.created_at,
          status: order.status || 'pending',
          total: order.total,
          items: order.items.map(item => ({
            product_title: item.product.title,
            product_image: item.product.images && item.product.images.length > 0 
              ? item.product.images[0] 
              : null,
            quantity: item.qty,
            price: item.price
          }))
        }));
        setOrders(transformedOrders);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (imagePath) => {
    if (!imagePath) return null;
    if (imagePath.startsWith('http')) return imagePath;
    if (imagePath.startsWith('/media/')) {
      return `http://localhost:8000${imagePath}`;
    }
    return `http://localhost:8000/media/${imagePath}`;
  };

  const getStatusColor = (status) => {
    const statusColors = {
      'created': '#f59e0b',
      'pending': '#f59e0b',
      'processing': '#3b82f6',
      'shipped': '#8b5cf6',
      'delivered': '#10b981',
      'cancelled': '#ef4444',
      'completed': '#10b981'
    };
    return statusColors[status?.toLowerCase()] || '#6b7280';
  };

  if (loading) {
    return (
      <div className="orders-loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your orders...</p>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="orders-empty-container">
        <div className="orders-empty-content">
          <i className="fas fa-box-open"></i>
          <h2>No Orders Yet</h2>
          <p>You haven't placed any orders yet. Start shopping now!</p>
          <button className="btn-primary" onClick={() => navigate('/')}>
            Start Shopping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="orders-page-container">
      <div className="orders-page-wrapper">
        <div className="orders-header">
          <button className="orders-back-btn" onClick={() => navigate(-1)}>
            <i className="fas fa-arrow-left"></i>
          </button>
          <h1 className="orders-title">My Orders</h1>
          <span className="orders-count">{orders.length} {orders.length === 1 ? 'Order' : 'Orders'}</span>
        </div>

        <div className="orders-list">
          {orders.map(order => (
            <div key={order.id} className="order-card">
              <div className="order-card-header">
                <div className="order-info">
                  <span className="order-id">Order #{order.id}</span>
                  <span className="order-date">
                    {new Date(order.created_at).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </span>
                </div>
                <div 
                  className="order-status-badge" 
                  style={{ background: getStatusColor(order.status) }}
                >
                  {order.status || 'Pending'}
                </div>
              </div>

              <div className="order-items">
                {order.items && order.items.map((item, index) => (
                  <div key={index} className="order-item">
                    <div className="order-item-image-wrapper">
                      {item.product_image ? (
                        <img 
                          src={getImageUrl(item.product_image)} 
                          alt={item.product_title} 
                          className="order-item-image" 
                        />
                      ) : (
                        <div className="order-item-no-image">
                          <i className="fas fa-image"></i>
                        </div>
                      )}
                    </div>
                    <div className="order-item-details">
                      <h4 className="order-item-title">{item.product_title}</h4>
                      <p className="order-item-quantity">Qty: {item.quantity}</p>
                    </div>
                    <div className="order-item-price">
                      ${(item.price * item.quantity).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>

              <div className="order-card-footer">
                <div className="order-total">
                  <span className="total-label">Total Amount</span>
                  <span className="total-value">${order.total?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="order-actions">
                  <button className="btn-secondary" onClick={() => navigate(`/orders/${order.id}`)}>
                    View Details
                  </button>
                  {order.status?.toLowerCase() === 'pending' && (
                    <button className="btn-cancel">Cancel Order</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OrdersPage;
