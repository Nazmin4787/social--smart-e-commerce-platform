import React, { useState } from 'react';

const COMMON_ALLERGENS = [
  'Parabens',
  'Sulfates',
  'Fragrance',
  'Alcohol',
  'Silicones',
  'Retinol',
  'Salicylic Acid',
  'Benzoyl Peroxide',
  'Alpha Hydroxy Acids (AHA)',
  'Beta Hydroxy Acids (BHA)',
  'Vitamin C',
  'Niacinamide',
  'Hyaluronic Acid',
  'Glycolic Acid',
  'Lactic Acid',
  'Tea Tree Oil',
  'Coconut Oil',
  'Mineral Oil',
  'Lanolin',
  'Beeswax',
  'Essential Oils',
  'Dimethicone',
  'Phenoxyethanol',
  'Formaldehyde',
  'Phthalates'
];

const AllergySelector = ({ selectedAllergies, onChange }) => {
  const [customAllergy, setCustomAllergy] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  const toggleAllergy = (allergen) => {
    if (selectedAllergies.includes(allergen)) {
      onChange(selectedAllergies.filter(a => a !== allergen));
    } else {
      onChange([...selectedAllergies, allergen]);
    }
  };

  const addCustomAllergy = () => {
    if (customAllergy.trim() && !selectedAllergies.includes(customAllergy.trim())) {
      onChange([...selectedAllergies, customAllergy.trim()]);
      setCustomAllergy('');
      setShowCustomInput(false);
    }
  };

  const removeAllergy = (allergen) => {
    onChange(selectedAllergies.filter(a => a !== allergen));
  };

  return (
    <div className="allergy-selector">
      <div className="allergy-header">
        <h3>Do you have any allergies?</h3>
        <p className="allergy-subtitle">
          Select any ingredients you're allergic to. We'll alert you if a product contains them.
        </p>
      </div>

      {selectedAllergies.length > 0 && (
        <div className="selected-allergies">
          <label className="allergy-label">Selected Allergies:</label>
          <div className="allergy-chips">
            {selectedAllergies.map((allergy, index) => (
              <div key={index} className="allergy-chip selected">
                <span>{allergy}</span>
                <button 
                  type="button"
                  onClick={() => removeAllergy(allergy)}
                  className="remove-chip-btn"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="allergy-options">
        <label className="allergy-label">Common Allergens:</label>
        <div className="allergy-grid">
          {COMMON_ALLERGENS.map((allergen, index) => (
            <button
              key={index}
              type="button"
              className={`allergy-chip ${selectedAllergies.includes(allergen) ? 'selected' : ''}`}
              onClick={() => toggleAllergy(allergen)}
            >
              {allergen}
              {selectedAllergies.includes(allergen) && <span className="check-icon">✓</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="custom-allergy-section">
        {!showCustomInput ? (
          <button
            type="button"
            className="add-custom-btn"
            onClick={() => setShowCustomInput(true)}
          >
            <i className="fas fa-plus"></i> Add Custom Allergen
          </button>
        ) : (
          <div className="custom-input-group">
            <input
              type="text"
              className="custom-allergy-input"
              placeholder="Enter custom allergen"
              value={customAllergy}
              onChange={(e) => setCustomAllergy(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addCustomAllergy();
                }
              }}
            />
            <button
              type="button"
              className="add-custom-confirm-btn"
              onClick={addCustomAllergy}
            >
              Add
            </button>
            <button
              type="button"
              className="cancel-custom-btn"
              onClick={() => {
                setShowCustomInput(false);
                setCustomAllergy('');
              }}
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      <button
        type="button"
        className="skip-allergies-btn"
        onClick={() => onChange([])}
      >
        Skip - I don't have any allergies
      </button>
    </div>
  );
};

export default AllergySelector;
