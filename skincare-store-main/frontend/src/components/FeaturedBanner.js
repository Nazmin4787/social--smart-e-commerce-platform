import React, { useState, useEffect } from 'react';

const FeaturedBanner = () => {
  const [banner, setBanner] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBanner();
  }, []);

  const fetchBanner = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/banners/?type=featured');
      const data = await response.json();
      
      console.log('Featured banner data:', data); // Debug log
      
      if (data.banners && data.banners.length > 0) {
        const activeBanner = data.banners[0];
        console.log('Setting banner:', activeBanner); // Debug log
        setBanner(activeBanner);
      }
    } catch (error) {
      console.error('Error fetching banner:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleShopClick = () => {
    if (banner && banner.link_url) {
      window.location.href = banner.link_url;
    } else {
      window.location.href = '/products';
    }
  };

  return (
    <section className="featured-banner">
      <div className="featured-banner-container">
        <div className="featured-banner-content">
          <div className="featured-text-section">
            <span className="featured-badge">Most Popular</span>
            <h2 className="featured-title">
              {banner?.title || 'Customer Favorites'}
            </h2>
            <p className="featured-description">
              {banner?.description || 'Discover our best-selling products loved by thousands of customers worldwide. Natural ingredients, proven results.'}
            </p>
            <div className="featured-stats">
              <div className="stat-item">
                <span className="stat-number">10K+</span>
                <span className="stat-label">Happy Customers</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">4.8★</span>
                <span className="stat-label">Average Rating</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">100%</span>
                <span className="stat-label">Natural</span>
              </div>
            </div>
            <button className="featured-cta-btn" onClick={handleShopClick}>
              Shop Best Sellers
              <i className="fas fa-arrow-right"></i>
            </button>
          </div>
          
          <div className="featured-image-section">
            <div className="featured-image-wrapper">
              <div className="featured-glow-effect"></div>
              {banner?.image ? (
                <img 
                  src={`http://localhost:8000${banner.image}`}
                  alt={banner.title}
                  className="featured-main-image"
                  onLoad={() => console.log('Image loaded successfully:', banner.image)}
                  onError={(e) => {
                    console.error('Image failed to load:', banner.image);
                    console.error('Full image URL:', e.target.src);
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="featured-placeholder" style={{ display: 'flex' }}>
                  <div className="placeholder-content">
                    <i className="fas fa-star"></i>
                    <i className="fas fa-heart"></i>
                    <i className="fas fa-leaf"></i>
                  </div>
                </div>
              )}
              
              {/* Floating product badges */}
              <div className="floating-badge badge-1">
                <i className="fas fa-certificate"></i>
                <span>Organic</span>
              </div>
              <div className="floating-badge badge-2">
                <i className="fas fa-shield-alt"></i>
                <span>Dermatologist Tested</span>
              </div>
              <div className="floating-badge badge-3">
                <i className="fas fa-leaf"></i>
                <span>Cruelty Free</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturedBanner;
