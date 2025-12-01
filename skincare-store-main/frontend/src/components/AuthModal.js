import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister } from '../api';

const AuthModal = ({ onClose }) => {
  const [step, setStep] = useState(1); // 1: phone, 2: details
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    phone: '',
    name: '',
    email: '',
    password: ''
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [notifyUpdates, setNotifyUpdates] = useState(false);
  const { login } = useContext(AuthContext);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleContinue = () => {
    if (formData.phone.length >= 10) {
      setStep(2);
    } else {
      setMessage('Please enter a valid phone number');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (!acceptTerms) {
      setMessage('Please accept the Terms & Conditions and Privacy Policy');
      setLoading(false);
      return;
    }

    try {
      if (isLogin) {
        const response = await apiLogin(formData.email, formData.password);
        login(response.user, response.access_token, response.refresh_token);
        onClose();
        window.location.reload();
      } else {
        const response = await apiRegister(formData.name, formData.email, formData.password);
        login(response.user, response.access_token, response.refresh_token);
        onClose();
        window.location.reload();
      }
    } catch (error) {
      setMessage(error.response?.data?.error || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-box" onClick={(e) => e.stopPropagation()}>
        <button className="auth-close-btn" onClick={onClose}>×</button>
        
        {step === 1 ? (
          <div className="auth-step-one">
            <div className="auth-modal-header">
              <div className="auth-customer-badge">
                More than 65 Lakh+ Happy Customers
              </div>
              <div className="auth-logo-center">
                <span className="auth-logo-text">SKINCARE STORE</span>
              </div>
              <div className="auth-hero-image">
                <div className="auth-placeholder-icon">
                  <i className="fas fa-spa"></i>
                  <i className="fas fa-heart"></i>
                  <i className="fas fa-star"></i>
                </div>
              </div>
            </div>

            <div className="auth-form-content">
              <h2 className="auth-title">LOG IN / SIGN UP</h2>
              <p className="auth-subtitle">Let's get started</p>

              <div className="phone-input-group">
                <div className="country-code">
                  <span className="flag">🇮🇳</span>
                  <span>+91</span>
                </div>
                <input
                  type="tel"
                  className="phone-input"
                  placeholder="Enter your phone number"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  maxLength={10}
                />
              </div>

              <button 
                className="continue-btn" 
                onClick={handleContinue}
                disabled={formData.phone.length < 10}
              >
                <span className="btn-icon">↻</span> Continue
              </button>

              <div className="auth-checkboxes">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={notifyUpdates}
                    onChange={(e) => setNotifyUpdates(e.target.checked)}
                  />
                  <span>Notify me for any updates/offers using RCS/WABA & SMS</span>
                </label>
              </div>

              <div className="auth-terms">
                <p>
                  By proceeding, I accept the <a href="#">T&C</a> and <a href="#">Privacy Policy</a>
                </p>
                <div className="secured-badge">
                  🔒 Secured by Shopify
                </div>
              </div>

              {message && <p className="auth-error-msg">{message}</p>}
            </div>
          </div>
        ) : (
          <div className="auth-step-two">
            <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
            
            <div className="auth-tabs-switch">
              <button
                className={`tab-switch ${isLogin ? 'active' : ''}`}
                onClick={() => setIsLogin(true)}
              >
                Login
              </button>
              <button
                className={`tab-switch ${!isLogin ? 'active' : ''}`}
                onClick={() => setIsLogin(false)}
              >
                Sign Up
              </button>
            </div>

            <form onSubmit={handleSubmit} className="auth-details-form">
              <h3>{isLogin ? 'Welcome Back!' : 'Create Your Account'}</h3>
              
              {!isLogin && (
                <div className="form-field">
                  <label>Full Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    placeholder="Enter your name"
                  />
                </div>
              )}

              <div className="form-field">
                <label>Email Address</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  placeholder="Enter your email"
                />
              </div>

              <div className="form-field">
                <label>Password</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  minLength={6}
                  placeholder="Enter your password"
                />
                {!isLogin && <small>Minimum 6 characters</small>}
              </div>

              <div className="form-field">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(e) => setAcceptTerms(e.target.checked)}
                    required
                  />
                  <span>I accept the Terms & Conditions and Privacy Policy</span>
                </label>
              </div>

              <button type="submit" className="submit-auth-btn" disabled={loading}>
                {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Sign Up')}
              </button>

              {message && <p className="auth-error-msg">{message}</p>}
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthModal;
