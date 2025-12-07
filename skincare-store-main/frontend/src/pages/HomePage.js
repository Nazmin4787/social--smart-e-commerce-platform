import React from 'react';
import Header from '../components/Header';
import Hero from '../components/Hero';
import CategorySection from '../components/CategorySection';
import ProductsSection from '../components/ProductsSection';
import FeaturedBanner from '../components/FeaturedBanner';
import AboutSection from '../components/AboutSection';

const HomePage = () => {
  return (
    <div className="home-page">
      <Header />
      <main>
        <Hero />
        <CategorySection />
        <ProductsSection title="Featured Products" limit={50} />
        <FeaturedBanner />
        <ProductsSection title="Trending Products" limit={20} isTrending={true} />
        <AboutSection />
      </main>
      <footer className="footer">
        <div className="footer-content">
          <p className="footer-text">&copy; 2025 Skincare Store. All rights reserved.</p>
          <div className="footer-links">
            <a href="/privacy" className="footer-link">Privacy Policy</a>
            <a href="/terms" className="footer-link">Terms of Service</a>
            <a href="/contact" className="footer-link">Contact Us</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
