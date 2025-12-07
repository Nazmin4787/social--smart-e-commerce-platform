# Admin Guide: Adding Product Ingredients

## Overview
The allergy tracking system helps users avoid products with ingredients they're allergic to. For this system to work, admins must add ingredients to each product.

## Accessing Django Admin

1. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py runserver
   ```

2. Open your browser and go to: `http://localhost:8000/admin`

3. Login with superuser credentials

## Adding Ingredients to Products

### Method 1: Through Django Admin UI

1. Navigate to **Products** in the admin panel
2. Click on a product to edit it
3. Scroll to the **"Ingredients (For Allergy Tracking)"** section
4. Add ingredients as a JSON array in the ingredients field

**Example format:**
```json
["Parabens", "Sulfates", "Fragrance", "Retinol", "Hyaluronic Acid"]
```

**Important Naming Guidelines:**
- Use the exact same spelling as the common allergens list
- Capitalize properly (e.g., "Parabens" not "parabens")
- Be consistent across all products
- Don't use abbreviations unless they're standard

### Method 2: Through Django Shell (Bulk Update)

For updating multiple products at once:

```bash
python manage.py shell
```

Then run:

```python
from api.models import Product

# Update a specific product
product = Product.objects.get(id=1)
product.ingredients = ["Parabens", "Sulfates", "Fragrance", "Vitamin E", "Aloe Vera"]
product.save()

# Or update multiple products
products = Product.objects.filter(category='serum')
for product in products:
    product.ingredients = ["Retinol", "Hyaluronic Acid", "Vitamin C"]
    product.save()
```

## Common Allergens Reference

Here are the 25 most common skincare allergens that users can select:

1. Parabens
2. Sulfates
3. Fragrance
4. Phthalates
5. Formaldehyde
6. Triclosan
7. Retinol
8. Hydroquinone
9. Oxybenzone
10. Alcohol (Denat)
11. Salicylic Acid
12. Benzoyl Peroxide
13. Glycolic Acid
14. Lactic Acid
15. Essential Oils
16. Lanolin
17. Propylene Glycol
18. Methylisothiazolinone
19. Coconut Oil
20. Shea Butter
21. Vitamin C (Ascorbic Acid)
22. Niacinamide
23. Alpha Hydroxy Acids (AHA)
24. Beta Hydroxy Acids (BHA)
25. Mineral Oil

## Best Practices

### 1. Be Comprehensive
Include ALL ingredients in the product, not just potential allergens. This gives users complete transparency.

### 2. Use Standard Names
- ✅ "Vitamin C (Ascorbic Acid)"
- ❌ "Vit C" or "Ascorbic acid"

### 3. Include Ingredient Categories
If a product contains multiple types of acids, list them specifically:
```json
["Glycolic Acid", "Lactic Acid", "Salicylic Acid", "Hyaluronic Acid"]
```

### 4. Update Existing Products
Don't forget to add ingredients to products that were created before the allergy system was implemented.

### 5. Verify Ingredients
Double-check the product packaging or manufacturer website to ensure accuracy.

## How the Allergy System Works

1. **During Registration**: Users select their allergies from the common allergens list
2. **Before Purchase**: When adding to cart, the system checks if the product contains any of the user's allergens
3. **Warning Display**: If allergens are found, users see:
   - Which specific allergens were detected
   - Up to 3 alternative safe products from the same category
   - Option to proceed anyway with the purchase
4. **Profile Management**: Users can update their allergies anytime in their profile

## Checking Product Status

In the admin panel, each product shows:
- ✅ Green "✓ X ingredients" - Product has ingredients added
- ⚠️ Orange "⚠ No ingredients" - Product needs ingredients added

**Priority**: Add ingredients to products with the orange warning first!

## Example: Complete Product Setup

### Product: "Bionera Vitamin C Serum"

**Title**: Bionera Vitamin C Serum
**Category**: serum
**Price**: 49.99
**Description**: Brightening serum with pure vitamin C...

**Ingredients** (JSON format):
```json
[
  "Vitamin C (Ascorbic Acid)",
  "Hyaluronic Acid",
  "Vitamin E",
  "Ferulic Acid",
  "Glycerin",
  "Panthenol",
  "Aloe Vera Extract",
  "Chamomile Extract",
  "Green Tea Extract"
]
```

## Troubleshooting

### Issue: Allergy check not working
**Solution**: Verify that:
1. Product has ingredients field populated
2. Ingredient names match exactly with user's allergy list
3. Backend server is running
4. No console errors in browser

### Issue: No alternative products shown
**Solution**: 
1. Check if there are other products in the same category
2. Ensure those products have ingredients added
3. Verify those products don't contain the user's allergens

### Issue: Users can't save allergies
**Solution**:
1. Check backend logs for errors
2. Verify the allergies API endpoint is working
3. Test with Django admin - can you update user allergies directly?

## Testing the System

### Test Scenario 1: New User Registration
1. Create a test user account
2. Select "Parabens" and "Sulfates" as allergies
3. Complete registration
4. Navigate to profile → My Allergies
5. Verify allergies are displayed

### Test Scenario 2: Product Warning
1. Find a product with "Parabens" in ingredients
2. Try to add it to cart
3. Verify warning modal appears
4. Check that alternative products are shown
5. Test both "Go Back" and "Add Anyway" buttons

### Test Scenario 3: Update Allergies
1. Go to profile → My Allergies
2. Click "Edit Allergies"
3. Add or remove allergies
4. Click "Save Changes"
5. Verify updated allergies are displayed

## Questions?

For technical support, check:
- `ALLERGY_SYSTEM_GUIDE.md` - Complete developer documentation
- Django logs: `backend/` directory
- Browser console for frontend errors
- API endpoint: `http://localhost:8000/api/allergies/check/<product_id>/`

---

**Remember**: The allergy system is a safety feature. Accurate ingredient data is crucial for protecting users with genuine allergies!
