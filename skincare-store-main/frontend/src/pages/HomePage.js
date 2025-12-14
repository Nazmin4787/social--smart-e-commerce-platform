import React, { useState } from 'react';
import Header from '../components/Header';
import Hero from '../components/Hero';
import CategorySection from '../components/CategorySection';
import IngredientsSection from '../components/IngredientsSection';
import ProductsSection from '../components/ProductsSection';
import FeaturedBanner from '../components/FeaturedBanner';
import AboutSection from '../components/AboutSection';

const HomePage = () => {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedIngredient, setSelectedIngredient] = useState(null);

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setSelectedIngredient(null);
    // Scroll to featured products section
    const productsSection = document.querySelector('.products-section');
    if (productsSection) {
      productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleIngredientSelect = (ingredient) => {
    setSelectedIngredient(ingredient);
    setSelectedCategory(null);
    // Scroll to ingredient products section
    setTimeout(() => {
      const ingredientSection = document.querySelectorAll('.products-section')[1];
      if (ingredientSection) {
        ingredientSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  return (
    <div className="home-page">
      <Header />
      <main>
        <Hero />
        <CategorySection onCategorySelect={handleCategorySelect} selectedCategory={selectedCategory} />
        <ProductsSection 
          title="Featured Products" 
          limit={50} 
          category={selectedCategory}
        />
        <FeaturedBanner />
        <IngredientsSection onIngredientSelect={handleIngredientSelect} selectedIngredient={selectedIngredient} />
        {selectedIngredient && (
          <ProductsSection 
            title={`Shop by ${selectedIngredient.replace('_', ' ')}`}
            limit={50} 
            ingredient={selectedIngredient}
          />
        )}
        <ProductsSection title="Trending Products" limit={20} isTrending={true} />
        <AboutSection />
      </main>
      <footer className="footer">
        <div className="footer-content">
          <p className="footer-text">&copy; 2025 Novacell. All rights reserved.</p>
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
