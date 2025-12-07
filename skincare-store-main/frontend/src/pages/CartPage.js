import React, { useContext, useState } from 'react';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { checkCartAllergies } from '../api';

const API_URL = 'http://localhost:8000/api';

const CartPage = () => {
  const { items, loading, setQuantity, removeItem, subtotal, tax, total, refreshCart } = useContext(CartContext);
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);
  const [showAllergyWarning, setShowAllergyWarning] = useState(false);
  const [allergyData, setAllergyData] = useState(null);
  const [checkingAllergies, setCheckingAllergies] = useState(false);

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
    if (processing || checkingAllergies) return;
    
    // First check for allergies
    setCheckingAllergies(true);
    try {
      const token = localStorage.getItem('access_token');
      const productIds = items.map(item => item.product_id || item.id);
      
      console.log('🔍 Checking allergies for products:', productIds);
      
      const allergyCheckResult = await checkCartAllergies(token, productIds);
      
      console.log('✅ Allergy check result:', allergyCheckResult);
      
      if (allergyCheckResult.has_allergens) {
        // Show allergy warning modal
        console.log('⚠️ Allergens detected! Showing warning modal...');
        setAllergyData(allergyCheckResult);
        setShowAllergyWarning(true);
        setCheckingAllergies(false);
        return;
      }
      
      console.log('✅ No allergens detected, proceeding with checkout');
      // No allergies, proceed with checkout
      proceedWithCheckout();
    } catch (error) {
      console.error('❌ Allergy check error:', error);
      console.error('Error details:', error.response?.data);
      // If allergy check fails, still allow checkout
      proceedWithCheckout();
    } finally {
      setCheckingAllergies(false);
    }
  };

  const proceedWithCheckout = async () => {
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

  const handleProceedAnyway = () => {
    setShowAllergyWarning(false);
    proceedWithCheckout();
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
                disabled={processing || checkingAllergies}
              >
                {checkingAllergies ? (
                  <>
                    <div className="loading-spinner" style={{width: '20px', height: '20px', borderWidth: '2px'}}></div>
                    <span>Checking allergies...</span>
                  </>
                ) : processing ? (
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

      {/* Allergy Warning Modal */}
      {showAllergyWarning && allergyData && (
        <div className="allergy-alert-modal-overlay" onClick={() => setShowAllergyWarning(false)}>
          <div className="allergy-alert-modal" onClick={(e) => e.stopPropagation()}>
            <button className="allergy-alert-close" onClick={() => setShowAllergyWarning(false)}>×</button>
            
            <div className="allergy-alert-header">
              <i className="fas fa-exclamation-triangle"></i>
              <h2>⚠️ Allergy Warning!</h2>
              <p className="allergy-alert-subtitle">Some items in your cart contain ingredients you're allergic to</p>
            </div>

            {allergyData.products_with_allergens.map((item, index) => (
              <div key={index} className="allergy-product-section">
                <h3 className="allergy-product-title">
                  <i className="fas fa-box"></i> {item.product.title}
                </h3>
                
                <div className="allergens-detected">
                  <strong>Detected Allergens:</strong>
                  <div className="allergen-tags">
                    {item.allergens_found.map((allergen, idx) => (
                      <span key={idx} className="allergen-tag">
                        <i className="fas fa-times-circle"></i> {allergen}
                      </span>
                    ))}
                  </div>
                </div>

                {item.alternatives && item.alternatives.length > 0 && (
                  <div className="alternative-products-section">
                    <h4><i className="fas fa-check-circle"></i> Safe Alternatives for You:</h4>
                    <div className="alternative-products-grid">
                      {item.alternatives.map((alt) => (
                        <div key={alt.id} className="alternative-product-card" onClick={() => {
                          setShowAllergyWarning(false);
                          navigate(`/products/${alt.id}`);
                        }}>
                          <div className="alternative-product-image">
                            {alt.images && alt.images.length > 0 ? (
                              <img src={alt.images[0]} alt={alt.title} />
                            ) : (
                              <i className="fas fa-image"></i>
                            )}
                          </div>
                          <div className="alternative-product-info">
                            <h5>{alt.title}</h5>
                            <p className="alternative-product-price">${alt.price}</p>
                            <span className="view-product-link">View Product →</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            <div className="allergy-alert-actions">
              <button className="allergy-alert-back-btn" onClick={() => setShowAllergyWarning(false)}>
                <i className="fas fa-arrow-left"></i> Go Back
              </button>
              <button className="allergy-alert-proceed-btn" onClick={handleProceedAnyway}>
                Proceed Anyway <i className="fas fa-exclamation-circle"></i>
              </button>
            </div>

            <div className="allergy-alert-disclaimer">
              <i className="fas fa-info-circle"></i>
              <p>We recommend choosing safe alternatives. Proceeding with allergenic products may cause adverse reactions.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;