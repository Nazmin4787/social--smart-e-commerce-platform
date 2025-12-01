import React from 'react';

const categories = [
  { name: 'Skin Care', icon: 'fa-spa', value: 'skincare' },
  { name: 'Hair Care', icon: 'fa-cut', value: 'haircare' },
  { name: 'Make Up', icon: 'fa-palette', value: 'makeup' },
  { name: 'Appliances', icon: 'fa-plug', value: 'appliances' }
];

const CategorySection = () => {
  const handleCategoryClick = (category) => {
    window.location.href = `/products?category=${category}`;
  };

  return (
    <section className="category-section">
      <div className="category-container">
        <h2 className="category-main-title">Shop by Category</h2>
        <div className="category-pills">
          {categories.map((category, index) => (
            <button
              key={index}
              className={`category-pill ${index === 0 ? 'active' : ''}`}
              onClick={() => handleCategoryClick(category.value)}
            >
              {category.name}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};

export default CategorySection;
