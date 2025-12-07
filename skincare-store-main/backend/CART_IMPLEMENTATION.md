# Cart Model & Database Implementation

## Overview
Enhanced Cart and CartItem models with comprehensive validation, price snapshots, and quantity limits.

## Implementation Date
December 2, 2025

---

## ✅ Completed Features

### 1. Cart Model Enhancement
**Location:** `backend/api/models.py`

#### New Fields Added:
- ✅ `is_active` (BooleanField) - Flag to mark cart as active/inactive (default: True)
- ✅ `created_at` (DateTimeField) - Timestamp when cart was created
- ✅ `updated_at` (DateTimeField) - Auto-updated timestamp for cart modifications

#### Features:
- One-to-one relationship with AppUser
- Complete serialization via `to_dict()` method
- Includes all cart items in serialized output

---

### 2. CartItem Model Enhancement
**Location:** `backend/api/models.py`

#### New Fields Added:
- ✅ `price_at_addition` (DecimalField) - **Price snapshot** preserving product price at time of adding to cart
- ✅ `added_at` (DateTimeField) - Timestamp when item was added to cart

#### Validation Features:

##### A. Maximum Quantity Validation
```python
MAX_QUANTITY_PER_ITEM = 99  # Class constant
```
- Maximum 99 units per cart item
- Enforced in `save()` method
- Raises `ValueError` if exceeded

##### B. Minimum Quantity Validation
- Quantity must be at least 1
- Enforced in `save()` method
- Raises `ValueError` if less than 1

##### C. Stock Validation
- Quantity cannot exceed available product stock
- Checked against `product.stock` field
- Raises `ValueError` with stock information if exceeded

##### D. Price Snapshot
- Automatically captures product price when item is added
- Price preserved even if product price changes later
- Used for subtotal calculations to maintain historical pricing

#### Model Constraints:
- ✅ `unique_together = ('cart', 'product')` - Prevents duplicate products in same cart
- ✅ `ordering = ['-added_at']` - Most recent items appear first

#### Serialization:
The `to_dict()` method provides:
- Product details (full product object)
- Quantity
- Price at addition (historical)
- Current price (for comparison)
- Subtotal (calculated using price_at_addition)
- Added timestamp

---

## 3. Database Migration
**Migration File:** `0007_alter_cartitem_options_cart_created_at_and_more.py`

### Applied Changes:
- ✅ Added `is_active` field to Cart
- ✅ Added `created_at` field to Cart
- ✅ Added `updated_at` field to Cart
- ✅ Added `price_at_addition` field to CartItem
- ✅ Added `added_at` field to CartItem
- ✅ Updated CartItem Meta options (unique_together, ordering)

**Status:** ✅ Migration successfully applied to database

---

## 4. Django Admin Registration
**Location:** `backend/api/admin.py`

### Cart Admin Interface
Features:
- ✅ List view displays: ID, customer name, email, active status, item count, total, timestamps
- ✅ Filter by: is_active, created_at, updated_at
- ✅ Search by: customer name, email
- ✅ Ordering: Most recently updated first
- ✅ Inline CartItem display with all details
- ✅ Read-only cart total calculation

### CartItem Inline
Features:
- ✅ Shows product, quantity, price at addition, current price, added timestamp
- ✅ Read-only display of all fields
- ✅ Current price comparison column
- ✅ Deletable cart items

---

## 5. Comprehensive Test Suite
**Location:** `backend/api/tests/test_cart_model.py`

### Test Coverage (14 tests):

#### Cart Tests:
1. ✅ `test_cart_creation_with_defaults` - Verifies default field values
2. ✅ `test_cart_to_dict` - Tests serialization
3. ✅ `test_cart_inactive_flag` - Tests is_active toggle
4. ✅ `test_cart_with_multiple_items` - Multiple items in cart

#### CartItem Tests:
5. ✅ `test_cart_item_creation_with_price_snapshot` - Automatic price capture
6. ✅ `test_cart_item_price_snapshot_preserved` - Price preservation after product price change
7. ✅ `test_cart_item_to_dict` - Serialization with all fields
8. ✅ `test_cart_item_ordering` - Most recent first ordering

#### Validation Tests:
9. ✅ `test_cart_item_quantity_validation_minimum` - qty must be >= 1
10. ✅ `test_cart_item_quantity_validation_maximum` - qty must be <= 99
11. ✅ `test_cart_item_quantity_validation_against_stock` - qty cannot exceed available stock
12. ✅ `test_cart_item_unique_together_constraint` - No duplicate products in cart

#### Price Logic Tests:
13. ✅ `test_cart_item_subtotal_calculation_with_price_change` - Subtotal uses historical price
14. ✅ `test_cart_item_max_quantity_constant` - MAX_QUANTITY_PER_ITEM = 99

**Test Results:** All 14 tests PASSED ✅

---

## Technical Details

### Model Relationships
```
AppUser (1) ←→ (1) Cart
Cart (1) ←→ (N) CartItem
CartItem (N) ←→ (1) Product
```

### Price Snapshot Logic
```python
# Automatic price capture on save
if not self.price_at_addition:
    self.price_at_addition = self.product.price
```

This ensures:
- Price is captured when item is first added
- Price remains unchanged even if product price updates
- Customers pay the price they saw when adding to cart
- Subtotals are calculated with historical pricing

### Validation Flow
```python
def save(self, *args, **kwargs):
    1. Check qty >= 1
    2. Check qty <= MAX_QUANTITY_PER_ITEM (99)
    3. Check qty <= product.stock
    4. Set price_at_addition if not set
    5. Call super().save()
```

---

## Usage Examples

### Creating a Cart with Items
```python
# Get or create cart for user
cart, created = Cart.objects.get_or_create(user=user)

# Add item to cart
cart_item = CartItem.objects.create(
    cart=cart,
    product=product,
    qty=2
    # price_at_addition automatically set to product.price
)

# Get cart data
cart_data = cart.to_dict()
# Returns: {id, user_id, is_active, items[], created_at, updated_at}
```

### Updating Quantity
```python
cart_item.qty = 5
cart_item.save()  # Validates against MAX_QUANTITY_PER_ITEM and stock
```

### Price Comparison
```python
item_data = cart_item.to_dict()
original_price = item_data['price_at_addition']  # Price when added
current_price = item_data['current_price']       # Current product price
subtotal = item_data['subtotal']                 # qty * price_at_addition
```

---

## Error Handling

### ValueError Exceptions
The CartItem model raises `ValueError` in these cases:

1. **Quantity too low:**
   ```
   ValueError: Quantity must be at least 1
   ```

2. **Quantity too high:**
   ```
   ValueError: Quantity cannot exceed 99
   ```

3. **Exceeds stock:**
   ```
   ValueError: Quantity cannot exceed available stock (5)
   ```

### IntegrityError
Django raises `IntegrityError` when attempting to add duplicate product to same cart (unique_together constraint).

---

## Database Schema

### Cart Table
| Field      | Type         | Constraints                    |
|------------|--------------|--------------------------------|
| id         | Integer      | Primary Key, Auto-increment    |
| user_id    | Integer      | Foreign Key (AppUser), Unique  |
| is_active  | Boolean      | Default: True                  |
| created_at | DateTime     | Default: timezone.now          |
| updated_at | DateTime     | Auto-updated                   |

### CartItem Table
| Field             | Type         | Constraints                      |
|-------------------|--------------|----------------------------------|
| id                | Integer      | Primary Key, Auto-increment      |
| cart_id           | Integer      | Foreign Key (Cart)               |
| product_id        | Integer      | Foreign Key (Product)            |
| qty               | Integer      | Default: 1, Validated            |
| price_at_addition | Decimal      | 10 digits, 2 decimal places      |
| added_at          | DateTime     | Default: timezone.now            |

**Constraints:**
- Unique together: (cart_id, product_id)
- Order by: -added_at (descending)

---

## Files Modified/Created

### Modified:
1. ✅ `backend/api/models.py` - Enhanced Cart and CartItem models
2. ✅ `backend/api/admin.py` - Added Cart and CartItem admin registration

### Created:
3. ✅ `backend/api/migrations/0007_alter_cartitem_options_cart_created_at_and_more.py`
4. ✅ `backend/api/tests/test_cart_model.py` - 14 comprehensive tests

---

## Test Execution

### Run Cart Tests Only:
```bash
cd skincare-store-main/backend
python3 manage.py test api.tests.test_cart_model -v 2 --settings=skincare_backend.test_settings
```

### Run All Tests:
```bash
python3 manage.py test api.tests -v 2 --settings=skincare_backend.test_settings
```

### Current Test Status:
- **Total Tests:** 34
- **Cart Tests:** 14
- **All Tests Status:** ✅ PASSED

---

## Next Steps (Recommended)

### Backend API Implementation:
1. Create Cart API endpoints (GET, POST, PATCH, DELETE)
2. Add cart item management endpoints (add, update quantity, remove)
3. Implement cart checkout process
4. Add cart abandonment tracking

### Frontend Integration:
1. Create CartContext for state management
2. Build Cart UI components
3. Implement add-to-cart functionality
4. Show price comparison (original vs current)
5. Display stock availability warnings

### Additional Features:
1. Cart expiration after X days of inactivity
2. Save-for-later functionality
3. Cart merging (anonymous → logged in user)
4. Cart recovery emails
5. Price drop notifications

---

## Summary

✅ **All Requirements Completed:**
- Cart and CartItem models exist with proper fields (user, product, quantity, added_at)
- is_active field added to Cart model
- Maximum quantity validation (99 per item)
- Price snapshot field in CartItem preserves price at time of adding
- Stock validation prevents over-ordering
- Comprehensive test coverage (14 tests, all passing)
- Django admin interface with inline display
- Database migration successfully applied

**Status:** Production-ready ✅
