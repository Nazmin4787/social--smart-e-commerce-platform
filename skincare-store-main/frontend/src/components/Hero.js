import React from 'react';

const Hero = () => {
  return (
    <>
      <section className="hero-section">
        <div className="hero-container-main">
          {/* Left Side - Product Image */}
          <div className="hero-image-side">
            <div className="hero-decorative-bubble bubble-1"></div>
            <div className="hero-decorative-bubble bubble-2"></div>
            <div className="hero-decorative-bubble bubble-3"></div>
            {/* Product image placeholder - can be replaced with actual image */}
            <div className="hero-product-placeholder">
              <i className="fas fa-image"></i>
            </div>
          </div>

          {/* Right Side - Content */}
          <div className="hero-content-side">
            <div className="new-badge">
              <span>NEW</span>
            </div>
            <h1 className="hero-main-title">
              <span className="activate-text">ACTIVATE</span>
              <span className="bright-text">BRIGHT</span>
              <span className="skin-text">SKIN</span>
            </h1>
            <p className="hero-subtitle-main">With <strong>10% Niacinamide</strong></p>
            <button className="hero-shop-btn">Shop Now</button>
          </div>
        </div>
      </section>

      {/* Template Section - For Admin to Insert Custom Templates */}
      <section className="template-section">
        <div className="template-content">
          {/* This blank area is reserved for admin to insert custom templates */}
          {/* Examples: promotional banners, featured collections, seasonal offers, etc. */}
        </div>
      </section>
    </>
  );
};

export default Hero;
