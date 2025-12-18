import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getOrderDetail, loadCashfreeSDK, getWalletBalance, API_URL } from '../api';
import axios from 'axios';
import Header from '../components/Header';

const PaymentPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useContext(AuthContext);
  const [order, setOrder] = useState(null);
  const [walletBalance, setWalletBalance] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cashfree');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    fetchOrderAndBalance();
  }, [user, orderId]);

  const fetchOrderAndBalance = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      // Fetch order details
      const orderData = await getOrderDetail(token, orderId);
      setOrder(orderData.order);
      
      // Fetch wallet balance
      const walletData = await getWalletBalance(token);
      setWalletBalance(walletData.wallet?.balance || 0);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load payment information');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    setProcessing(true);
    setError('');

    try {
      const token = localStorage.getItem('accessToken');
      const returnUrl = `${window.location.origin}/orders/${orderId}?success=true`;
      
      // For retry payments on existing orders, we need to update the order's payment method
      // and create a new payment session
      const response = await axios.post(
        `${API_URL}/payment/retry-order/`,
        {
          order_id: orderId,
          payment_method: paymentMethod,
          return_url: returnUrl
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      const data = response.data;

      if (!data.success) {
        throw new Error(data.message || 'Failed to process payment');
      }

      // Handle different payment methods
      if (paymentMethod === 'cod') {
        // Cash on Delivery - redirect to success page
        navigate(`/orders/${orderId}?success=true`);
      } else if (paymentMethod === 'wallet') {
        // Wallet payment - redirect to success page
        navigate(`/orders/${orderId}?success=true`);
      } else if (paymentMethod === 'cashfree') {
        // Cashfree payment - redirect to payment gateway
        const { payment_session_id } = data;
        
        if (!payment_session_id) {
          throw new Error('Payment session not created');
        }

        // Load Cashfree SDK and redirect
        const cashfree = await loadCashfreeSDK();
        
        const checkoutOptions = {
          paymentSessionId: payment_session_id,
          returnUrl: returnUrl,
          redirectTarget: "_self"
        };

        cashfree.checkout(checkoutOptions);
      }
    } catch (error) {
      console.error('Payment error:', error);
      setError(error.response?.data?.error || error.message || 'Payment failed. Please try again.');
      setProcessing(false);
    }
  };

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <div className="payment-page">
        <Header />
        <div className="payment-container">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading payment details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="payment-page">
        <Header />
        <div className="payment-container">
          <h1>Order Not Found</h1>
          <button className="btn-primary" onClick={() => navigate('/orders')}>
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  if (order.payment_status === 'success') {
    return (
      <div className="payment-page">
        <Header />
        <div className="payment-container">
          <div className="success-banner">
            <div className="success-icon">✓</div>
            <h2>Payment Already Completed</h2>
            <p>This order has already been paid for.</p>
          </div>
          <button className="btn-primary" onClick={() => navigate(`/orders/${orderId}`)}>
            View Order Details
          </button>
        </div>
      </div>
    );
  }

  const total = parseFloat(order.total) || 0;

  return (
    <div className="payment-page">
      <Header />
      <div className="payment-container">
        <div className="payment-header">
          <button className="back-button" onClick={() => navigate('/orders')}>
            <i className="fas fa-arrow-left"></i>
          </button>
          <h1>Complete Payment</h1>
        </div>

        {error && (
          <div className="error-banner">
            <p>{error}</p>
          </div>
        )}

        <div className="payment-content">
          {/* Order Summary */}
          <div className="payment-section">
            <h2>Order Summary</h2>
            <div className="order-info-box">
              <div className="info-row">
                <span>Order Number:</span>
                <strong>#{order.order_number}</strong>
              </div>
              <div className="info-row">
                <span>Items:</span>
                <span>{order.items?.length || 0} items</span>
              </div>
              <div className="info-row total-row">
                <span>Total Amount:</span>
                <strong>₹{total.toFixed(2)}</strong>
              </div>
            </div>
          </div>

          {/* Payment Method */}
          <div className="payment-section">
            <h2>Select Payment Method</h2>
            <div className="payment-methods">
              <label className={`payment-option ${paymentMethod === 'cashfree' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="payment"
                  value="cashfree"
                  checked={paymentMethod === 'cashfree'}
                  onChange={() => setPaymentMethod('cashfree')}
                />
                <div className="payment-details">
                  <strong>Cashfree Payment Gateway</strong>
                  <p>Credit/Debit Card, UPI, Net Banking</p>
                </div>
              </label>

              <label className={`payment-option ${paymentMethod === 'wallet' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="payment"
                  value="wallet"
                  checked={paymentMethod === 'wallet'}
                  onChange={() => setPaymentMethod('wallet')}
                  disabled={walletBalance < total}
                />
                <div className="payment-details">
                  <strong>Wallet</strong>
                  <p>Balance: ₹{walletBalance.toFixed(2)}</p>
                  {walletBalance < total && <p className="error-text">Insufficient balance</p>}
                </div>
              </label>

              <label className={`payment-option ${paymentMethod === 'cod' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="payment"
                  value="cod"
                  checked={paymentMethod === 'cod'}
                  onChange={() => setPaymentMethod('cod')}
                />
                <div className="payment-details">
                  <strong>Cash on Delivery</strong>
                  <p>Pay when you receive</p>
                </div>
              </label>
            </div>
          </div>

          {/* Payment Button */}
          <div className="payment-actions">
            <button
              className="btn-primary btn-pay-now"
              onClick={handlePayment}
              disabled={processing}
            >
              {processing ? (
                <>
                  <div className="btn-spinner"></div>
                  Processing...
                </>
              ) : (
                <>
                  <i className="fas fa-lock" style={{ marginRight: '8px' }}></i>
                  Pay ₹{total.toFixed(2)}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentPage;
