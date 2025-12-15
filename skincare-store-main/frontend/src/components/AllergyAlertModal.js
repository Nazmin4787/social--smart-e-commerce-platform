import React from 'react';
import { useNavigate } from 'react-router-dom';

const AllergyAlertModal = ({ allergyData, onClose, onAddAnyway }) => {
  const navigate = useNavigate();
  const { has_allergens, allergens_found, product, alternatives } = allergyData;

  if (!has_allergens) return null;

  // Helper to get full image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return null;
    if (imagePath.startsWith('http')) return imagePath;
    if (imagePath.startsWith('/media/')) {
      return `http://localhost:8000${imagePath}`;
    }
    return `http://localhost:8000/media/${imagePath}`;
  };

  const handleViewAlternative = (altProductId) => {
    onClose();
    navigate(`/product/${altProductId}`);
  };

  return (
    <div className="allergy-alert-overlay" onClick={onClose}>
      <div className="allergy-alert-modal" onClick={(e) => e.stopPropagation()}>
        <button className="allergy-close-btn" onClick={onClose}>×</button>
        
        <div className="allergy-alert-header">
          <div className="allergy-warning-icon">
            <i className="fas fa-exclamation-triangle"></i>
          </div>
          <h2>Allergy Warning!</h2>
        </div>

        <div className="allergy-alert-content">
          <p className="allergy-alert-message">
            This product contains ingredients you're allergic to:
          </p>
          
          <div className="allergens-list">
            {allergens_found.map((allergen, index) => (
              <div key={index} className="allergen-item">
                <i className="fas fa-times-circle"></i>
                <span>{allergen}</span>
              </div>
            ))}
          </div>

          <div className="allergy-product-info">
            <h3>{product.title}</h3>
            <p className="allergy-recommendation">
              We strongly recommend choosing an alternative product that's safe for you.
            </p>
          </div>

          {alternatives && alternatives.length > 0 && (
            <div className="allergy-alternatives">
              <h3 className="alternatives-title">
                <i className="fas fa-lightbulb"></i> Recommended Alternatives
              </h3>
              <p className="alternatives-subtitle">
                These products don't contain your allergens:
              </p>
              
              <div className="alternatives-grid">
                {alternatives.map((alt) => (
                  <div key={alt.id} className="alternative-card">
                    <div className="alternative-image">
                      {alt.images && alt.images.length > 0 ? (
                        <img 
                          src={getImageUrl(alt.images[0])} 
                          alt={alt.title}
                          onError={(e) => { e.target.src = '/placeholder.png'; }}
                        />
                      ) : (
                        <div className="no-image">
                          <i className="fas fa-image"></i>
                        </div>
                      )}
                    </div>
                    <div className="alternative-info">
                      <h4>{alt.title}</h4>
                      <p className="alternative-price">${alt.price}</p>
                      <div className="alternative-safety">
                        <i className="fas fa-shield-alt"></i>
                        <span>Safe for you</span>
                      </div>
                    </div>
                    <button
                      className="view-alternative-btn"
                      onClick={() => handleViewAlternative(alt.id)}
                    >
                      View Product
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="allergy-actions">
            <button
              className="proceed-anyway-btn"
              onClick={() => {
                onAddAnyway();
                onClose();
              }}
            >
              Add to Cart Anyway
            </button>
            <button className="go-back-btn" onClick={onClose}>
              Go Back to Product
            </button>
          </div>

          <div className="allergy-disclaimer">
            <i className="fas fa-info-circle"></i>
            <p>
              If you proceed with this purchase, we are not responsible for any allergic reactions.
              Please consult with a dermatologist before using products with known allergens.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllergyAlertModal;
