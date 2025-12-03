import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister, fetchProducts, addToCart } from '../api';
import AuthModal from './AuthModal';
import { CartContext } from '../context/CartContext';

const Header = () => {
  const navigate = useNavigate();
  const { user, logout, login } = useContext(AuthContext);
  const { items, fetchCart } = useContext(CartContext);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [cartCount, setCartCount] = useState(0);
  const [likedCount, setLikedCount] = useState(0);
  useEffect(() => {
    if (user) fetchCart();
  }, [user]);
  useEffect(() => {
    setCartCount(items ? items.length : 0);
  }, [items]);

  // Developer/demo login helper - creates or logs in a demo user
  const demoLogin = async () => {
    const demo = { name: 'Demo User', email: 'demo@example.com', password: 'demopass' };
    try {
      // try login first
      const res = await apiLogin(demo.email, demo.password).catch(async () => {
        // if login fails, register then login
        await apiRegister(demo.name, demo.email, demo.password);
        return apiLogin(demo.email, demo.password);
      });
      // call AuthContext.login
      if (res && res.access_token) {
        // AuthContext expects login(userData, access, refresh)
        const userData = res.user || { id: null, name: demo.name, email: demo.email };
        // call context login so other contexts react
        login(userData, res.access_token, res.refresh_token);
        // fetch cart after login
        await fetchCart();
        // if cart empty, add first product for demo
        if ((!items || items.length === 0)) {
          try {
            const prods = await fetchProducts();
            if (prods && prods.length > 0) {
              await addToCart(res.access_token, prods[0].id, 1);
              await fetchCart();
            }
          } catch (e) {
            // ignore demo auto-add failures
            console.warn('Demo auto-add failed', e);
          }
        }
        return;
      }
    } catch (err) {
      console.error('Demo login failed', err);
      alert('Demo login failed: ' + (err.response?.data?.error || err.message));
    }
  };
  const [searchQuery, setSearchQuery] = useState('');

  const handleProfileClick = () => {
    if (user) {
      navigate('/profile');
    } else {
      setShowAuthModal(true);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Navigate to products search page
      console.log('Search:', searchQuery);
    }
  };

  return (
    <>
      {/* Top Banner */}
      <div className="top-banner">
        <div className="banner-content-wrapper">
          <span className="banner-text">AWARE: No one from our team will call you for offers, free gifts or payments.</span>
          <a href="#" className="banner-link">Click For More Offers</a>
        </div>
      </div>

      {/* Main Header */}
      <header className="main-header">
        <div className="header-container">
          {/* Logo */}
          <div className="brand-logo" onClick={() => navigate('/')}>
            <span className="logo-text">SKINCARE STORE</span>
          </div>

          {/* Search Bar */}
          <div className="header-search">
            <form onSubmit={handleSearch}>
              <input
                type="text"
                className="search-input-main"
                placeholder="Search for products, ingredients, brands..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit" className="search-btn">
                <i className="fas fa-search"></i>
              </button>
            </form>
          </div>

          {/* Header Icons */}
          <div className="header-icons">
            <button className="header-icon-btn" title="Track Order">
              <i className="fas fa-truck"></i>
            </button>

            <button className="header-icon-btn" onClick={() => navigate('/cart')} title="Cart">
              <i className="fas fa-shopping-bag"></i>
              {cartCount > 0 && <span className="icon-badge">{cartCount}</span>}
            </button>

            <button className="header-icon-btn" onClick={handleProfileClick} title={user ? user.name : 'Login'}>
              <i className="fas fa-user"></i>
            </button>

            {user && user.is_staff && (
              <button className="header-icon-btn" onClick={() => navigate('/admin')} title="Admin Panel" style={{background: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)', color: 'white', borderRadius: '8px', padding: '0.5rem 1rem'}}>
                <i className="fas fa-cog"></i> Admin
              </button>
            )}

            {!user && (
              <button className="header-icon-btn demo-login-btn" onClick={demoLogin} title="Demo Login" style={{marginLeft:8}}>
                Demo
              </button>
            )}
            
            {user && (
              <div className="user-greeting">
                <span>Hi, {user.name}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation Menu */}
      <nav className="main-navigation">
        <div className="nav-container">
          <div className="nav-item dropdown">
            <span>SHOP ALL <i className="fas fa-chevron-down"></i></span>
          </div>
          <div className="nav-item dropdown">
            <span>SKIN CONCERN <i className="fas fa-chevron-down"></i></span>
          </div>
          <div className="nav-item dropdown">
            <span>INGREDIENTS <i className="fas fa-chevron-down"></i></span>
          </div>
          <div className="nav-item dropdown">
            <span>SKIN TYPE <i className="fas fa-chevron-down"></i></span>
          </div>
          <div className="nav-item">
            <span>BEST SELLERS</span>
          </div>
          <div className="nav-item">
            <span>NEW ARRIVALS</span>
          </div>
          <div className="nav-item">
            <span>BLOGS</span>
          </div>
        </div>
      </nav>

      {/* Promotional Banner */}
      <div className="promo-banner">
        <div className="promo-content">
          <i className="fas fa-gift promo-icon"></i>
          <span className="promo-text">UPTO 20% OFF + <em>Free Gifts</em></span>
          <i className="fas fa-chevron-right promo-arrow"></i>
        </div>
      </div>

      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
    </>
  );
};

export default Header;
