# Quick Start Guide - Testing the Allergy System

## Step 1: Start the Backend

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

Backend will run on: `http://localhost:8000`

## Step 2: Start the Frontend

```bash
cd frontend
npm start
```

Frontend will run on: `http://localhost:3000`

## Step 3: Access Django Admin

1. Open browser: `http://localhost:8000/admin`
2. Login with superuser credentials
   - If you don't have a superuser, create one:
     ```bash
     cd backend
     python manage.py createsuperuser
     ```

## Step 4: Add Ingredients to a Product

1. In Django Admin, click **Products**
2. Click on any product to edit
3. Scroll to **"Ingredients (For Allergy Tracking)"** section
4. Add ingredients in JSON format:
   ```json
   ["Parabens", "Sulfates", "Fragrance", "Retinol", "Vitamin E"]
   ```
5. Click **Save**

**Tip**: Products without ingredients show ⚠️ orange warning in the list.

## Step 5: Test Registration with Allergies

1. Go to frontend: `http://localhost:3000`
2. Click **Login/Register** button
3. Switch to **Sign Up** tab
4. **Step 1**: Enter phone number
5. **Step 2**: Enter name, email, password
6. **Step 3**: Select allergies (NEW!)
   - Click on chips to select (e.g., "Parabens", "Sulfates")
   - Or add custom allergen
   - Or click "Skip" if no allergies
7. Click **Complete Registration**

## Step 6: Test Allergy Warning

1. After login, browse products
2. Click on a product that contains your selected allergens
3. Click **"Add to Cart"** button
4. **Expected**: Warning modal appears showing:
   - ⚠️ Which allergens were detected
   - 3 alternative safe products
   - "Go Back" button
   - "Add Anyway" button

## Step 7: Test Profile Allergy Management

1. Click your profile icon → **Profile**
2. In sidebar, click **"My Allergies"** tab
3. View your current allergies displayed as red chips
4. Click **"Edit Allergies"** button
5. Add or remove allergies
6. Click **"Save Changes"**
7. Verify updated allergies are shown

## Expected Results ✅

### Registration Flow
- [x] 3-step registration process
- [x] Allergy selector in step 3
- [x] 25 common allergens available
- [x] Custom allergen input works
- [x] Can skip allergies
- [x] Allergies saved to database

### Product Purchase Flow
- [x] Adding product checks for allergens
- [x] Modal appears if allergens found
- [x] Shows which specific allergens
- [x] Displays 3 safe alternatives
- [x] Can proceed anyway with warning
- [x] No error if no allergens found

### Profile Management
- [x] Allergies tab visible in sidebar
- [x] Current allergies displayed
- [x] Edit mode with AllergySelector
- [x] Save/Cancel buttons work
- [x] Loading spinner during save
- [x] Success message after save

### Admin Interface
- [x] Products show ingredient count
- [x] ⚠️ warning for products without ingredients
- [x] Easy to add ingredients
- [x] User allergies visible
- [x] Organized fieldsets

## Common Test Scenarios

### Scenario 1: User with No Allergies
1. Register without selecting any allergies (click Skip)
2. Try to add any product to cart
3. **Expected**: Product added directly, no warning

### Scenario 2: Product with No Ingredients
1. Try to add a product without ingredients
2. **Expected**: Product added directly, system doesn't break

### Scenario 3: Multiple Allergens Detected
1. Add product with multiple user allergens
2. **Expected**: Modal lists all detected allergens

### Scenario 4: No Safe Alternatives Exist
1. Try to buy product when no alternatives available
2. **Expected**: Modal shows "No safe alternatives found" message

### Scenario 5: Update Allergies Then Shop
1. Go to profile → Update allergies
2. Add new allergen (e.g., "Retinol")
3. Try to buy product with Retinol
4. **Expected**: New allergy is detected

## Troubleshooting

### Backend Not Starting
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Restart backend
python manage.py runserver
```

### Frontend Not Starting
```bash
# Check if port 3000 is already in use
lsof -i :3000

# Install dependencies if needed
npm install

# Restart frontend
npm start
```

### Database Issues
```bash
# Check migrations
python manage.py showmigrations

# Apply migrations if needed
python manage.py migrate
```

### CORS Errors
Verify `settings.py` has:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

## Quick Test Data Setup

### Add Test Product with Ingredients
```bash
python manage.py shell
```

```python
from api.models import Product

# Create test product
product = Product.objects.create(
    title="Test Vitamin C Serum",
    description="Brightening serum for testing",
    price=49.99,
    stock=100,
    category="serum",
    images=["https://via.placeholder.com/300"],
    ingredients=["Vitamin C (Ascorbic Acid)", "Hyaluronic Acid", "Vitamin E"]
)
print(f"Created product ID: {product.id}")

# Add another with allergens
product2 = Product.objects.create(
    title="Test Moisturizer",
    description="Contains common allergens",
    price=39.99,
    stock=50,
    category="moisturizer",
    images=["https://via.placeholder.com/300"],
    ingredients=["Parabens", "Sulfates", "Fragrance", "Shea Butter"]
)
print(f"Created product ID: {product2.id}")
```

## Video Test Flow

1. **Record your test**: Screen record the complete flow
2. **Start to finish**: Registration → Shopping → Warning → Profile
3. **Show admin**: Demonstrate adding ingredients
4. **Verify all features**: Check each component works

## Success Indicators 🎉

- ✅ Registration includes allergy step
- ✅ Allergies saved and retrievable
- ✅ Product warnings appear correctly
- ✅ Alternative products shown
- ✅ Profile management works
- ✅ Admin can add ingredients easily
- ✅ No console errors
- ✅ UI matches forest green theme
- ✅ Mobile responsive

## Next Steps After Testing

1. **Add ingredients to all products** (via admin)
2. **Create real product data** with accurate ingredients
3. **User acceptance testing** with real users
4. **Monitor for errors** in production
5. **Collect feedback** on allergy features

## Support

- Django logs: Check terminal running backend
- React logs: Check browser console (F12)
- API testing: Use Postman or `curl`
- Database: Use Django shell or admin

---

**Ready to test!** 🚀 Follow steps 1-7 above to verify the complete allergy tracking system.
