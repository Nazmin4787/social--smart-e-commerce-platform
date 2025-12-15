import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister } from '../api';
import AllergySelector from './AllergySelector';

const AuthModal = ({ onClose }) => {
  const [step, setStep] = useState(1); // 1: phone, 2: details, 3: allergies
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    phone: '',
    name: '',
    email: '',
    password: ''
  });
  const [allergies, setAllergies] = useState([]);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('error'); // 'error', 'success', 'info'
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
      setMessage('');
    } else {
      setMessage('Please enter a valid phone number');
      setMessageType('error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // For signup, move to allergy step first
    if (!isLogin && step === 2) {
      if (!acceptTerms) {
        setMessage('Please accept the Terms & Conditions and Privacy Policy');
        setMessageType('error');
        return;
      }
      setStep(3); // Move to allergy selection
      setMessage('');
      return;
    }
    
    // For login or final signup submission
    setLoading(true);
    setMessage('');

    if (!acceptTerms) {
      setMessage('Please accept the Terms & Conditions and Privacy Policy');
      setMessageType('error');
      setLoading(false);
      return;
    }

    try {
      if (isLogin) {
        console.log('Attempting login with:', formData.email);
        const response = await apiLogin(formData.email, formData.password);
        console.log('Login response:', response);
        
        if (response && response.user && response.access_token) {
          login(response.user, response.access_token, response.refresh_token);
          setMessage('Login successful! Redirecting...');
          setMessageType('success');
          setTimeout(() => {
            onClose();
            window.location.reload();
          }, 1000);
        } else {
          setMessage('Login failed: Invalid response from server');
          setMessageType('error');
        }
      } else {
        console.log('Attempting registration with:', formData.email);
        const response = await apiRegister(formData.name, formData.email, formData.password, allergies);
        console.log('Register response:', response);
        
        if (response && response.user && response.access_token) {
          login(response.user, response.access_token, response.refresh_token);
          setMessage('Registration successful! Redirecting...');
          setMessageType('success');
          setTimeout(() => {
            onClose();
            window.location.reload();
          }, 1000);
        } else {
          setMessage('Registration failed: Invalid response from server');
          setMessageType('error');
        }
      }
    } catch (error) {
      console.error('Auth error:', error);
      console.error('Error response:', error.response);
      
      let errorMsg = 'An error occurred. Please try again.';
      
      if (error.response) {
        errorMsg = error.response.data?.error || error.response.data?.message || 
                   `Server error: ${error.response.status}`;
      } else if (error.request) {
        errorMsg = 'Cannot connect to server. Please check if the backend is running.';
      } else {
        errorMsg = error.message || 'An unexpected error occurred';
      }
      
      if (errorMsg.includes('already exists')) {
        setMessage('This email is already registered. Please use Login instead.');
        setMessageType('info');
        setIsLogin(true); // Switch to login tab
      } else {
        setMessage(errorMsg);
        setMessageType('error');
      }
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
                <div className="auth-logo-container">
                  <div className="auth-logo-wrapper">
                    <div className="auth-logo-text-serif">NOVACELL</div>
                    <svg className="auth-leaf-accent" viewBox="0 0 30 30" width="45" height="45">
                      <path d="M15 3 Q20 8, 25 15 Q20 22, 15 27 Q10 22, 5 15 Q10 8, 15 3 Z" 
                            fill="#059669" opacity="0.8" />
                      <path d="M15 10 L15 24" stroke="#047857" strokeWidth="1" opacity="0.5" />
                    </svg>
                  </div>
                </div>
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

              {message && <div className={`auth-error-msg ${messageType}`}>{message}</div>}
            </div>
          </div>
        ) : step === 2 ? (
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
              
              {isLogin && (
                <div style={{background: '#e0f2fe', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem', color: '#0369a1'}}>
                  💡 <strong>Admin Login:</strong> admin@example.com / admin123
                </div>
              )}
              
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

              {message && <div className={`auth-error-msg ${messageType}`}>{message}</div>}
            </form>
          </div>
        ) : step === 3 ? (
          <div className="auth-step-three">
            <button className="back-btn" onClick={() => setStep(2)}>← Back</button>
            
            <div className="allergy-step-header">
              <h2>Almost Done!</h2>
              <p className="allergy-step-subtitle">
                Help us keep you safe by telling us about any allergies
              </p>
            </div>

            <AllergySelector 
              selectedAllergies={allergies}
              onChange={setAllergies}
            />

            <button 
              type="button"
              className="complete-registration-btn" 
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Complete Registration'}
            </button>

            {message && <div className={`auth-error-msg ${messageType}`}>{message}</div>}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default AuthModal;
