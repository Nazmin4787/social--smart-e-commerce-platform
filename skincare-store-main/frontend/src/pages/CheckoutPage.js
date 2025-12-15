import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getCart, getAddresses, createPaymentOrder, loadCashfreeSDK, getWalletBalance } from '../api';
import Header from '../components/Header';

const CheckoutPage = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [cartItems, setCartItems] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [walletBalance, setWalletBalance] = useState(0);
  const [selectedShipping, setSelectedShipping] = useState(null);
  const [selectedBilling, setSelectedBilling] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('cashfree');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchCheckoutData();
  }, [user]);

  const fetchCheckoutData = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      // Fetch cart
      const cartData = await getCart(token);
      setCartItems(cartData.items || []);
      
      // Fetch addresses
      const addressData = await getAddresses(token);
      setAddresses(addressData.addresses || []);
      
      // Set default addresses
      const defaultShipping = addressData.addresses?.find(a => a.address_type === 'shipping' && a.is_default);
      const defaultBilling = addressData.addresses?.find(a => a.address_type === 'billing' && a.is_default);
      
      if (defaultShipping) setSelectedShipping(defaultShipping.id);
      if (defaultBilling) setSelectedBilling(defaultBilling.id);
      
      // Fetch wallet balance
      const walletData = await getWalletBalance(token);
      setWalletBalance(walletData.wallet?.balance || 0);
      
    } catch (error) {
      console.error('Error fetching checkout data:', error);
      setError('Failed to load checkout data');
    }
  };

  const calculateTotal = () => {
    return cartItems.reduce((sum, item) => sum + (item.product.price * item.qty), 0);
  };

  const handlePlaceOrder = async () => {
    if (!selectedShipping) {
      setError('Please select a shipping address');
      return;
    }

    if (paymentMethod === 'cashfree' && !selectedBilling) {
      setError('Please select a billing address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('accessToken');
      const returnUrl = `${window.location.origin}/payment/success`;
      
      const response = await createPaymentOrder(
        token,
        paymentMethod,
        selectedShipping,
        selectedBilling || selectedShipping,
        returnUrl
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to create order');
      }

      // Handle different payment methods
      if (paymentMethod === 'cod') {
        // Cash on Delivery - redirect to success page
        navigate(`/orders/${response.order_id}?success=true`);
      } else if (paymentMethod === 'wallet') {
        // Wallet payment - redirect to success page
        navigate(`/orders/${response.order_id}?success=true`);
      } else if (paymentMethod === 'cashfree') {
        // Cashfree payment - redirect to payment gateway
        const { payment_session_id } = response;
        
        if (!payment_session_id) {
          throw new Error('Payment session not created');
        }

        // Load Cashfree SDK
        const cashfree = await loadCashfreeSDK();
        
        // Initialize Cashfree
        const cashfreeInstance = await cashfree.Cashfree({
          mode: 'sandbox' // Use 'production' for live
        });

        // Create checkout options
        const checkoutOptions = {
          paymentSessionId: payment_session_id,
          returnUrl: returnUrl,
          redirectTarget: '_self' // Opens in same window
        };

        // Redirect to Cashfree checkout
        cashfreeInstance.checkout(checkoutOptions);
      }
      
    } catch (error) {
      console.error('Error placing order:', error);
      setError(error.message || 'Failed to place order');
      setLoading(false);
    }
  };

  const shippingAddresses = addresses.filter(a => a.address_type === 'shipping');
  const billingAddresses = addresses.filter(a => a.address_type === 'billing');
  const total = calculateTotal();

  if (!user) {
    return null;
  }

  return (
    <div className="checkout-page">
      <Header />
      <div className="checkout-container">
        <h1>Checkout</h1>

        {error && <div className="error-message">{error}</div>}

        <div className="checkout-content">
          {/* Cart Summary */}
          <div className="checkout-section">
            <h2>Order Summary</h2>
            {cartItems.length === 0 ? (
              <p>Your cart is empty</p>
            ) : (
              <div className="cart-summary">
                {cartItems.map(item => (
                  <div key={item.id} className="cart-item-summary">
                    <img 
                      src={
                        item.product.images && item.product.images.length > 0
                          ? (item.product.images[0].startsWith('http') 
                              ? item.product.images[0] 
                              : `http://localhost:8000${item.product.images[0]}`)
                          : '/placeholder.png'
                      }
                      alt={item.product.title}
                      onError={(e) => { e.target.src = '/placeholder.png'; }}
                    />
                    <div className="item-details">
                      <h3>{item.product.title}</h3>
                      <p>Qty: {item.qty}</p>
                      <p className="price">₹{item.product.price} × {item.qty} = ₹{(item.product.price * item.qty).toFixed(2)}</p>
                    </div>
                  </div>
                ))}
                <div className="total">
                  <strong>Total: ₹{total.toFixed(2)}</strong>
                </div>
              </div>
            )}
          </div>

          {/* Shipping Address */}
          <div className="checkout-section">
            <h2>Shipping Address</h2>
            {shippingAddresses.length === 0 ? (
              <p>No shipping addresses found. <a href="/profile">Add one</a></p>
            ) : (
              <div className="address-list">
                {shippingAddresses.map(addr => (
                  <label key={addr.id} className={`address-card ${selectedShipping === addr.id ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="shipping"
                      value={addr.id}
                      checked={selectedShipping === addr.id}
                      onChange={() => setSelectedShipping(addr.id)}
                    />
                    <div className="address-details">
                      <strong>{addr.full_name}</strong>
                      <p>{addr.address_line1}</p>
                      {addr.address_line2 && <p>{addr.address_line2}</p>}
                      <p>{addr.city}, {addr.state} {addr.postal_code}</p>
                      <p>{addr.phone}</p>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Billing Address (only for Cashfree) */}
          {paymentMethod === 'cashfree' && (
            <div className="checkout-section">
              <h2>Billing Address</h2>
              <label>
                <input
                  type="checkbox"
                  checked={selectedBilling === selectedShipping}
                  onChange={(e) => setSelectedBilling(e.target.checked ? selectedShipping : null)}
                />
                Same as shipping address
              </label>
              {selectedBilling !== selectedShipping && billingAddresses.length > 0 && (
                <div className="address-list">
                  {billingAddresses.map(addr => (
                    <label key={addr.id} className={`address-card ${selectedBilling === addr.id ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="billing"
                        value={addr.id}
                        checked={selectedBilling === addr.id}
                        onChange={() => setSelectedBilling(addr.id)}
                      />
                      <div className="address-details">
                        <strong>{addr.full_name}</strong>
                        <p>{addr.address_line1}</p>
                        {addr.address_line2 && <p>{addr.address_line2}</p>}
                        <p>{addr.city}, {addr.state} {addr.postal_code}</p>
                        <p>{addr.phone}</p>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Payment Method */}
          <div className="checkout-section">
            <h2>Payment Method</h2>
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

          {/* Place Order Button */}
          <div className="checkout-actions">
            <button
              className="btn-primary btn-place-order"
              onClick={handlePlaceOrder}
              disabled={loading || cartItems.length === 0 || !selectedShipping}
            >
              {loading ? 'Processing...' : `Place Order - ₹${total.toFixed(2)}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
