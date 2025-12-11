import React from 'react';

const categories = [
  { 
    name: 'Skin Care', 
    value: 'SKINCARE',
    image: '/images/categories/skincare.jpeg',
    placeholder: '🧴'
  },
  { 
    name: 'Hair Care', 
    value: 'HAIRCARE',
    image: '/images/categories/haircare.jpeg',
    placeholder: '💇'
  },
  { 
    name: 'Body Care', 
    value: 'BODYCARE',
    image: '/images/categories/bodycare.jpeg',
    placeholder: '🧴'
  },
  { 
    name: 'Make Up', 
    value: 'MAKEUP',
    image: '/images/categories/makeup.jpeg',
    placeholder: '💄'
  },
  { 
    name: 'Perfume', 
    value: 'PERFUME',
    image: '/images/categories/perfume.jpeg',
    placeholder: '🌸'
  }
];

const CategorySection = ({ onCategorySelect, selectedCategory }) => {
  const handleCategoryClick = (categoryValue) => {
    if (onCategorySelect) {
      onCategorySelect(categoryValue);
    } else {
      // Fallback to navigation if no callback provided
      window.location.href = `/products?category=${categoryValue}`;
    }
  };

  return (
    <section className="category-section">
      <div className="category-container">
        <h2 className="category-main-title">Shop by Category</h2>
        <div className="category-boxes-grid">
          {categories.map((category, index) => (
            <div
              key={index}
              className={`category-box ${selectedCategory === category.value ? 'active' : ''}`}
              onClick={() => handleCategoryClick(category.value)}
            >
              <div className="category-box-image">
                <img 
                  src={category.image} 
                  alt={category.name}
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <div className="category-box-placeholder">
                  <span className="category-emoji">{category.placeholder}</span>
                </div>
              </div>
              <h3 className="category-box-title">{category.name}</h3>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default CategorySection;
