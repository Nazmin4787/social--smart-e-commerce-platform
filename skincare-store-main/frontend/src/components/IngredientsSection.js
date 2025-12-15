import React from 'react';

const ingredients = [
  { 
    name: 'Retinol', 
    value: 'RETINOL',
    image: '/images/ingredients/Retinol.jpeg',
    placeholder: '🧪'
  },
  { 
    name: 'Ceramides', 
    value: 'CERAMIDES',
    image: '/images/ingredients/ceramides.jpeg',
    placeholder: '💧'
  },
  { 
    name: 'Niacinamide', 
    value: 'NIACINAMIDE',
    image: '/images/ingredients/niacinamide.jpeg',
    placeholder: '✨'
  },
  { 
    name: 'Watermelon', 
    value: 'WATERMELON',
    image: '/images/ingredients/watermelon.jpeg',
    placeholder: '🍉'
  },
  { 
    name: 'Strawberry', 
    value: 'STRAWBERRY',
    image: '/images/ingredients/strawberry.jpeg',
    placeholder: '🍓'
  },
  { 
    name: 'Hyaluronic Acid', 
    value: 'HYALURONIC_ACID',
    image: '/images/ingredients/hydraclonic.jpeg',
    placeholder: '💦'
  },
  { 
    name: 'Pomegranate', 
    value: 'POMEGRANATE',
    image: '/images/ingredients/pomegrante.jpeg',
    placeholder: '🍎'
  },
  { 
    name: 'Vitamin C', 
    value: 'VITAMIN_C',
    image: '/images/ingredients/vitamiv C.jpeg',
    placeholder: '🍋'
  }
];

const IngredientsSection = ({ onIngredientSelect, selectedIngredient }) => {
  const handleIngredientClick = (ingredientValue) => {
    if (onIngredientSelect) {
      onIngredientSelect(ingredientValue);
    } else {
      // Fallback to navigation if no callback provided
      window.location.href = `/products?ingredient=${ingredientValue}`;
    }
  };

  return (
    <section className="ingredients-section">
      <div className="ingredients-container">
        <h2 className="ingredients-main-title">Shop by Ingredients</h2>
        <div className="ingredients-grid">
          {ingredients.map((ingredient, index) => (
            <div
              key={index}
              className={`ingredient-item ${selectedIngredient === ingredient.value ? 'active' : ''}`}
              onClick={() => handleIngredientClick(ingredient.value)}
            >
              <div className="ingredient-image-wrapper">
                <img 
                  src={ingredient.image} 
                  alt={ingredient.name}
                  className="ingredient-image"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <div className="ingredient-placeholder">
                  <span className="ingredient-emoji">{ingredient.placeholder}</span>
                </div>
              </div>
              <h3 className="ingredient-name">{ingredient.name}</h3>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default IngredientsSection;
