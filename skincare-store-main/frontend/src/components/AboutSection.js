import React, { useState, useEffect } from 'react';
import { getAboutUs } from '../api';

const AboutSection = () => {
  const [aboutData, setAboutData] = useState(null);

  useEffect(() => {
    fetchAboutData();
  }, []);

  const fetchAboutData = async () => {
    try {
      const data = await getAboutUs();
      setAboutData(data);
    } catch (error) {
      console.error('Error fetching about data:', error);
      // Set default data if API fails
      setAboutData({
        company_name: 'Skincare Store',
        description: 'Your trusted destination for premium skincare products. We believe in natural beauty and provide high-quality products to help you achieve healthy, glowing skin.',
        mission: 'To provide accessible, effective skincare solutions that enhance natural beauty and promote skin health.',
        contact: {
          email: 'support@skincarestore.com',
          phone: '+1-800-SKINCARE',
          address: '123 Beauty Lane, Wellness City, CA 90210'
        },
        social_media: {
          instagram: 'skincarestore',
          facebook: 'facebook.com/skincarestore',
          twitter: 'skincarestore'
        }
      });
    }
  };

  return (
    <section className="about-section" id="about">
      <div className="container">
        <div className="about-content">
          <div className="about-text">
            <h2>About Us</h2>
            <h3>{aboutData?.company_name || 'Skincare Store'}</h3>
            <p className="about-description">
              {aboutData?.description || 'Your trusted destination for premium skincare products. We believe in natural beauty and provide high-quality products to help you achieve healthy, glowing skin.'}
            </p>
            <p className="about-mission">
              <strong>Our Mission:</strong> {aboutData?.mission || 'To provide accessible, effective skincare solutions that enhance natural beauty and promote skin health.'}
            </p>
            
            <div className="about-info">
              <div className="info-item">
                <i className="fas fa-envelope"></i>
                <span>{aboutData?.contact?.email || 'support@skincarestore.com'}</span>
              </div>
              <div className="info-item">
                <i className="fas fa-phone"></i>
                <span>{aboutData?.contact?.phone || '+1-800-SKINCARE'}</span>
              </div>
              <div className="info-item">
                <i className="fas fa-map-marker-alt"></i>
                <span>{aboutData?.contact?.address || '123 Beauty Lane, Wellness City, CA 90210'}</span>
              </div>
            </div>

            <div className="social-links">
              <a href={`https://instagram.com/${aboutData?.social_media?.instagram || 'skincarestore'}`} target="_blank" rel="noopener noreferrer">
                <i className="fab fa-instagram"></i>
              </a>
              <a href={`https://${aboutData?.social_media?.facebook || 'facebook.com/skincarestore'}`} target="_blank" rel="noopener noreferrer">
                <i className="fab fa-facebook"></i>
              </a>
              <a href={`https://twitter.com/${aboutData?.social_media?.twitter || 'skincarestore'}`} target="_blank" rel="noopener noreferrer">
                <i className="fab fa-twitter"></i>
              </a>
            </div>
          </div>

          <div className="about-stats">
            <div className="stat-card">
              <i className="fas fa-users"></i>
              <h3>5000+</h3>
              <p>Happy Customers</p>
            </div>
            <div className="stat-card">
              <i className="fas fa-box"></i>
              <h3>100+</h3>
              <p>Premium Products</p>
            </div>
            <div className="stat-card">
              <i className="fas fa-star"></i>
              <h3>4.9★</h3>
              <p>Average Rating</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
