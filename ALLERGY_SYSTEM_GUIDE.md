# Allergy Management System - Implementation Guide

## Overview
The allergy management system allows users to specify their allergies during registration and receives alerts when trying to purchase products containing those allergens, with alternative product recommendations.

## Features Implemented

### 1. Backend Changes

#### Database Models
- **AppUser Model**: Added `allergies` field (JSONField) to store user's allergen list
- **Product Model**: Added `ingredients` field (JSONField) to store product ingredients

#### API Endpoints
- `POST /api/auth/register/` - Now accepts `allergies` array parameter
- `GET /api/allergies/check/<product_id>/` - Check if product contains user allergens
- `PUT /api/allergies/update/` - Update user's allergy list

### 2. Frontend Components

#### AllergySelector Component
Location: `frontend/src/components/AllergySelector.js`

Features:
- 25+ common skincare allergens pre-populated
- Custom allergen input
- Chip-based selection UI
- Skip option for users without allergies

Usage during registration:
```javascript
import AllergySelector from './components/AllergySelector';

const [allergies, setAllergies] = useState([]);

<AllergySelector 
  selectedAllergies={allergies}
  onChange={setAllergies}
/>
```

#### AllergyAlertModal Component
Location: `frontend/src/components/AllergyAlertModal.js`

Features:
- Warning display for detected allergens
- Product information
- Up to 3 alternative product recommendations
- Options to proceed or go back
- Safety disclaimer

Usage in product pages:
```javascript
import AllergyAlertModal from './components/AllergyAlertModal';
import { checkProductAllergies } from '../api';

const checkAllergies = async (productId) => {
  const token = localStorage.getItem('accessToken');
  const data = await checkProductAllergies(token, productId);
  
  if (data.has_allergens) {
    setAllergyData(data);
    setShowAllergyModal(true);
  } else {
    // Proceed with add to cart
  }
};
```

### 3. Integration Points

#### Registration Flow
1. User enters basic information
2. AllergySelector component displays
3. User selects allergies or skips
4. Registration API call includes allergies array
5. User account created with allergy preferences

#### Product Purchase Flow
1. User clicks "Add to Cart" on product
2. System checks if user is logged in
3. API call to `/allergies/check/<product_id>/`
4. If allergens found:
   - AllergyAlertModal appears
   - Shows allergens in product
   - Displays safe alternatives
   - User can proceed or cancel
5. If no allergens or user proceeds:
   - Product added to cart

### 4. Admin Requirements

To fully utilize this system, admins need to:

1. **Add ingredients to products** via admin panel or API
2. **Update existing products** with ingredient lists
3. **Ensure ingredient naming consistency** for accurate matching

Example product ingredients:
```json
[
  "Hyaluronic Acid",
  "Niacinamide",
  "Glycerin",
  "Vitamin C",
  "Fragrance"
]
```

### 5. API Usage Examples

#### Register with allergies:
```javascript
POST /api/auth/register/
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123",
  "allergies": ["Parabens", "Sulfates", "Fragrance"]
}
```

#### Check product allergies:
```javascript
GET /api/allergies/check/5/
Headers: Authorization: Bearer <token>

Response:
{
  "has_allergens": true,
  "allergens_found": ["fragrance", "parabens"],
  "product": { product object },
  "alternatives": [ array of safe products ]
}
```

#### Update user allergies:
```javascript
PUT /api/allergies/update/
Headers: Authorization: Bearer <token>
{
  "allergies": ["Retinol", "Vitamin C", "Essential Oils"]
}
```

## Next Steps for Full Implementation

### In AuthModal.js:
Add a third step for allergy selection during registration:

```javascript
const [step, setStep] = useState(1); // 1: phone, 2: details, 3: allergies
const [allergies, setAllergies] = useState([]);

// In step 3:
{step === 3 && (
  <div className="auth-step-three">
    <AllergySelector 
      selectedAllergies={allergies}
      onChange={setAllergies}
    />
    <button onClick={handleFinalSubmit}>Complete Registration</button>
  </div>
)}

// Update registration call:
const response = await apiRegister(
  formData.name, 
  formData.email, 
  formData.password,
  allergies  // Pass allergies
);
```

### In ProductDetailPage.js:
Add allergy check before adding to cart:

```javascript
import { checkProductAllergies } from '../api';
import AllergyAlertModal from '../components/AllergyAlertModal';

const [allergyData, setAllergyData] = useState(null);
const [showAllergyModal, setShowAllergyModal] = useState(false);

const handleAddToCart = async () => {
  if (!user) {
    // Show login modal
    return;
  }

  // Check for allergies
  try {
    const data = await checkProductAllergies(token, product.id);
    
    if (data.has_allergens) {
      setAllergyData(data);
      setShowAllergyModal(true);
    } else {
      // Safe to add - proceed with add to cart
      await addToCart(token, product.id, quantity);
      showSuccess('Added to cart!');
    }
  } catch (error) {
    console.error('Allergy check failed:', error);
    // Proceed with caution or show error
  }
};

// In JSX:
{showAllergyModal && allergyData && (
  <AllergyAlertModal
    allergyData={allergyData}
    onClose={() => setShowAllergyModal(false)}
    onAddAnyway={() => addToCart(token, product.id, quantity)}
  />
)}
```

### In ProfilePage.js:
Add allergies management section:

```javascript
import { updateUserAllergies } from '../api';
import AllergySelector from '../components/AllergySelector';

const [allergies, setAllergies] = useState(user?.allergies || []);
const [editingAllergies, setEditingAllergies] = useState(false);

const saveAllergies = async () => {
  try {
    await updateUserAllergies(token, allergies);
    setEditingAllergies(false);
    showSuccess('Allergies updated!');
  } catch (error) {
    showError('Failed to update allergies');
  }
};

// In profile UI:
<div className="profile-allergies-section">
  <h3>My Allergies</h3>
  {editingAllergies ? (
    <>
      <AllergySelector 
        selectedAllergies={allergies}
        onChange={setAllergies}
      />
      <button onClick={saveAllergies}>Save</button>
      <button onClick={() => setEditingAllergies(false)}>Cancel</button>
    </>
  ) : (
    <>
      <div className="allergy-list">
        {allergies.length > 0 ? allergies.map(a => (
          <span key={a} className="allergy-badge">{a}</span>
        )) : 'No allergies listed'}
      </div>
      <button onClick={() => setEditingAllergies(true)}>Edit Allergies</button>
    </>
  )}
</div>
```

## Testing the System

1. **Run migrations**: `python manage.py migrate`
2. **Start backend**: `python manage.py runserver`
3. **Start frontend**: `npm start`
4. **Test registration** with allergy selection
5. **Add ingredients** to products via Django admin
6. **Test product purchase** with matching allergens
7. **Verify alternatives** are shown correctly

## Common Allergens Included

- Parabens
- Sulfates
- Fragrance
- Alcohol
- Silicones
- Retinol
- Salicylic Acid
- Benzoyl Peroxide
- Alpha/Beta Hydroxy Acids
- Vitamin C
- Niacinamide
- Tea Tree Oil
- Coconut Oil
- Essential Oils
- And more...

## Security Considerations

- Allergies are stored as JSON array in database
- Input sanitization applied to custom allergens
- Token-based authentication required for allergy checks
- User can only update their own allergies

## Styling

All styles are included in `styles.css`:
- Forest green theme matching the site
- Responsive design for mobile
- Accessible chip-based selection
- Warning colors for allergy alerts

---

**Status**: Backend complete, frontend components ready
**Next**: Integrate into registration flow and product pages
**Migration**: `0005_allergies_and_ingredients.py` applied
