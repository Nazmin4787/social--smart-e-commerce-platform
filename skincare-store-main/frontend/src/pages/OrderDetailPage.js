import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getOrderDetail, verifyPayment } from '../api';
import Header from '../components/Header';

const OrderDetailPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useContext(AuthContext);
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    // Check if coming from payment
    const orderNumber = searchParams.get('order_number');
    if (orderNumber) {
      handlePaymentReturn(orderNumber);
    } else {
      fetchOrderDetail();
    }
  }, [user, orderId]);

  const handlePaymentReturn = async (orderNumber) => {
    setVerifying(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await verifyPayment(token, orderNumber);
      
      if (response.success && response.payment_status === 'success') {
        // Payment successful, fetch order details
        fetchOrderDetail();
      } else {
        setError('Payment verification failed. Please contact support.');
        fetchOrderDetail();
      }
    } catch (error) {
      console.error('Error verifying payment:', error);
      setError('Failed to verify payment');
      fetchOrderDetail();
    } finally {
      setVerifying(false);
    }
  };

  const fetchOrderDetail = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      const response = await getOrderDetail(token, orderId);
      
      if (response.success) {
        setOrder(response.order);
      } else {
        setError('Failed to fetch order details');
      }
    } catch (error) {
      console.error('Error fetching order:', error);
      setError('Failed to load order details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#ffa500',
      confirmed: '#2196f3',
      processing: '#9c27b0',
      shipped: '#ff9800',
      delivered: '#4caf50',
      cancelled: '#f44336',
      refunded: '#607d8b'
    };
    return colors[status] || '#757575';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTrackingStages = () => {
    const stages = [
      { key: 'confirmed', label: 'Order Confirmed', icon: '✓' },
      { key: 'processing', label: 'Processing', icon: '📦' },
      { key: 'shipped', label: 'Shipped', icon: '🚚' },
      { key: 'delivered', label: 'Delivered', icon: '🏠' }
    ];

    const statusOrder = ['pending', 'confirmed', 'processing', 'shipped', 'delivered'];
    const currentIndex = statusOrder.indexOf(order?.status);

    return stages.map((stage, index) => {
      const stageIndex = statusOrder.indexOf(stage.key);
      const isCompleted = stageIndex <= currentIndex;
      const isCurrent = stageIndex === currentIndex;
      
      return {
        ...stage,
        isCompleted,
        isCurrent,
        date: isCompleted ? (isCurrent ? formatDate(new Date()) : null) : null
      };
    });
  };

  if (!user) {
    return null;
  }

  if (loading || verifying) {
    return (
      <div className="order-detail-page">
        <Header />
        <div className="order-detail-container">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>{verifying ? 'Verifying payment...' : 'Loading order details...'}</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="order-detail-page">
        <Header />
        <div className="order-detail-container">
          <div className="error-message">{error || 'Order not found'}</div>
          <button className="btn-primary" onClick={() => navigate('/orders')}>
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  const isPaymentSuccess = searchParams.get('success') === 'true' || order.payment_status === 'success';

  return (
    <div className="order-detail-page">
      <Header />
      <div className="order-detail-container">
        {isPaymentSuccess && (
          <div className="success-banner">
            <div className="success-icon">✓</div>
            <h2>Order Placed Successfully!</h2>
            <p>Thank you for your order. We'll send you updates via email.</p>
          </div>
        )}

        <div className="order-detail-header">
          <div>
            <h1>Order #{order.order_number}</h1>
            <p className="order-date">Placed on {formatDate(order.created_at)}</p>
          </div>
          <span 
            className="status-badge" 
            style={{ backgroundColor: getStatusColor(order.status) }}
          >
            {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
          </span>
        </div>

        {/* Order Tracking Timeline */}
        {order.status !== 'cancelled' && order.status !== 'refunded' && (
          <div className="tracking-timeline-section">
            <h2>Track Your Order</h2>
            <div className="tracking-timeline">
              {getTrackingStages().map((stage, index) => (
                <div 
                  key={stage.key} 
                  className={`tracking-stage ${stage.isCompleted ? 'completed' : ''} ${stage.isCurrent ? 'current' : ''}`}
                >
                  <div className="stage-icon-wrapper">
                    <div className="stage-icon">{stage.icon}</div>
                    {index < 3 && <div className="stage-line"></div>}
                  </div>
                  <div className="stage-info">
                    <div className="stage-label">{stage.label}</div>
                    {stage.isCompleted && stage.isCurrent && (
                      <div className="stage-status">In Progress</div>
                    )}
                    {stage.isCompleted && !stage.isCurrent && (
                      <div className="stage-status">Completed</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="order-detail-content">
          {/* Order Items */}
          <div className="detail-section">
            <h2>Items ({order.items?.length || 0})</h2>
            <div className="order-items-list">
              {order.items && order.items.map((item, idx) => (
                <div key={idx} className="order-item-detail">
                  {item.product && (
                    <>
                      <img 
                        src={item.product.images?.[0] || '/placeholder.png'} 
                        alt={item.product.title} 
                      />
                      <div className="item-info">
                        <h3>{item.product.title}</h3>
                        <p className="item-category">{item.product.category}</p>
                        <p className="item-price">₹{parseFloat(item.price).toFixed(2)} × {item.qty}</p>
                      </div>
                      <div className="item-subtotal">
                        <strong>₹{parseFloat(item.subtotal).toFixed(2)}</strong>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Shipping Address */}
          {order.shipping_address && (
            <div className="detail-section">
              <h2>Shipping Address</h2>
              <div className="address-box">
                <p><strong>{order.shipping_address.full_name}</strong></p>
                <p>{order.shipping_address.address_line1}</p>
                {order.shipping_address.address_line2 && <p>{order.shipping_address.address_line2}</p>}
                <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
                <p>Phone: {order.shipping_address.phone}</p>
              </div>
            </div>
          )}

          {/* Payment Information */}
          <div className="detail-section">
            <h2>Payment Information</h2>
            <div className="payment-box">
              <div className="payment-row">
                <span>Payment Status:</span>
                <strong>{order.payment_status}</strong>
              </div>
              {order.payment && (
                <>
                  <div className="payment-row">
                    <span>Payment Method:</span>
                    <strong>{order.payment.payment_method.toUpperCase()}</strong>
                  </div>
                  {order.payment.payment_id && (
                    <div className="payment-row">
                      <span>Transaction ID:</span>
                      <strong>{order.payment.payment_id}</strong>
                    </div>
                  )}
                </>
              )}
              <div className="payment-row total">
                <span>Total Amount:</span>
                <strong>₹{parseFloat(order.total).toFixed(2)}</strong>
              </div>
            </div>
          </div>

          {/* Tracking Information */}
          {order.tracking_number && (
            <div className="detail-section">
              <h2>Tracking Information</h2>
              <div className="tracking-box">
                <p>Tracking Number: <strong>{order.tracking_number}</strong></p>
              </div>
            </div>
          )}

          {/* Notes */}
          {order.notes && (
            <div className="detail-section">
              <h2>Order Notes</h2>
              <div className="notes-box">
                <p>{order.notes}</p>
              </div>
            </div>
          )}
        </div>

        <div className="order-actions">
          <button className="btn-secondary" onClick={() => navigate('/orders')}>
            View All Orders
          </button>
          <button className="btn-primary" onClick={() => navigate('/')}>
            Continue Shopping
          </button>
        </div>
      </div>
    </div>
  );
};

export default OrderDetailPage;
