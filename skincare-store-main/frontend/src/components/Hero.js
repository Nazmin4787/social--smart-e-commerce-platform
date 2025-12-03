import React, { useState, useEffect } from 'react';
import { getBanners } from '../api';

const Hero = () => {
  const [banners, setBanners] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBanners();
  }, []);

  const fetchBanners = async () => {
    try {
      const data = await getBanners();
      const activeBanners = data.filter(banner => banner.is_active);
      setBanners(activeBanners);
    } catch (error) {
      console.error('Error fetching banners:', error);
    } finally {
      setLoading(false);
    }
  };

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % banners.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + banners.length) % banners.length);
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  // Auto-play slideshow
  useEffect(() => {
    if (banners.length > 1) {
      const interval = setInterval(nextSlide, 5000); // Change slide every 5 seconds
      return () => clearInterval(interval);
    }
  }, [banners.length, currentSlide]);

  if (loading) {
    return <div className="banner-loading">Loading...</div>;
  }

  if (banners.length === 0) {
    // Show default hero if no banners
    return (
      <>
        <section className="hero-section">
          <div className="hero-container-main">
            <div className="hero-image-side">
              <div className="hero-decorative-bubble bubble-1"></div>
              <div className="hero-decorative-bubble bubble-2"></div>
              <div className="hero-decorative-bubble bubble-3"></div>
              <div className="hero-product-placeholder">
                <i className="fas fa-image"></i>
              </div>
            </div>
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
      </>
    );
  }

  return (
    <section className="banner-carousel">
      <div className="carousel-container">
        {banners.map((banner, index) => (
          <div
            key={banner.id}
            className={`carousel-slide ${index === currentSlide ? 'active' : ''}`}
            style={{ display: index === currentSlide ? 'block' : 'none' }}
          >
            <img src={banner.image} alt={banner.title} className="banner-image" />
            <div className="banner-overlay">
              <h2 className="banner-title">{banner.title}</h2>
            </div>
          </div>
        ))}

        {banners.length > 1 && (
          <>
            <button className="carousel-btn prev-btn" onClick={prevSlide}>
              <i className="fas fa-chevron-left"></i>
            </button>
            <button className="carousel-btn next-btn" onClick={nextSlide}>
              <i className="fas fa-chevron-right"></i>
            </button>

            <div className="carousel-dots">
              {banners.map((_, index) => (
                <button
                  key={index}
                  className={`dot ${index === currentSlide ? 'active' : ''}`}
                  onClick={() => goToSlide(index)}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
};

export default Hero;
