import React from 'react';
import Header from '../components/Header';
import Hero from '../components/Hero';
import CategorySection from '../components/CategorySection';
import ProductsSection from '../components/ProductsSection';
import AboutSection from '../components/AboutSection';

const HomePage = () => {
  return (
    <div className="home-page">
      <Header />
      <main>
        <Hero />
        <CategorySection />
        <ProductsSection title="Featured Products" limit={8} />
        <ProductsSection title="Trending Products" limit={4} isTrending={true} />
        <AboutSection />
      </main>
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <p>&copy; 2025 Skincare Store. All rights reserved.</p>
            <div className="footer-links">
              <a href="/privacy">Privacy Policy</a>
              <a href="/terms">Terms of Service</a>
              <a href="/contact">Contact Us</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
