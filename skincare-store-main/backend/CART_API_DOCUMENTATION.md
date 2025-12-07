# Cart API Endpoints Documentation

## Overview
Complete REST API implementation for shopping cart management with JWT authentication, validation, and price snapshot features.

## Implementation Date
December 2, 2025

---

## Authentication
All Cart API endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

Unauthorized requests return `401 Unauthorized`.

---

## Endpoints

### 1. GET /api/cart/
**Fetch user's cart with all items**

#### Request
- Method: `GET`
- Headers: `Authorization: Bearer <token>`
- Body: None

#### Success Response (200 OK)
```json
{
  "id": 1,
  "user_id": 123,
  "is_active": true,
  "items": [
    {
      "id": 1,
      "product": {
        "id": 5,
        "title": "Product Name",
        "description": "Product description",
        "price": 29.99,
        "stock": 10,
        "images": [],
        "category": "skincare",
        "average_rating": 4.5,
        "reviews": []
      },
      "qty": 2,
      "price_at_addition": 29.99,
      "current_price": 29.99,
      "subtotal": 59.98,
      "added_at": "2025-12-02T10:30:00Z"
    }
  ],
  "created_at": "2025-12-01T08:00:00Z",
  "updated_at": "2025-12-02T10:30:00Z"
}
```

#### Error Response (401 Unauthorized)
```json
{
  "error": "Unauthorized"
}
```

#### Features
- Returns complete cart data with all items
- Each item includes price snapshot (price_at_addition) and current price
- Items ordered by most recently added first
- Automatically creates cart if doesn't exist

---

### 2. POST /api/cart/add/
**Add product to cart**

#### Request
- Method: `POST`
- Headers: 
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- Body:
```json
{
  "product_id": 5,
  "qty": 2
}
```

#### Parameters
- `product_id` (integer, required): ID of product to add
- `qty` (integer, optional): Quantity to add (default: 1)

#### Success Response - New Item (201 Created)
```json
{
  "message": "Item added to cart",
  "item": {
    "id": 1,
    "product": { /* full product object */ },
    "qty": 2,
    "price_at_addition": 29.99,
    "current_price": 29.99,
    "subtotal": 59.98,
    "added_at": "2025-12-02T10:30:00Z"
  }
}
```

#### Success Response - Updated Item (200 OK)
```json
{
  "message": "Cart item quantity updated",
  "item": {
    "id": 1,
    "product": { /* full product object */ },
    "qty": 5,
    "price_at_addition": 29.99,
    "current_price": 29.99,
    "subtotal": 149.95,
    "added_at": "2025-12-02T10:30:00Z"
  }
}
```

#### Error Responses

**Missing product_id (400 Bad Request)**
```json
{
  "error": "product_id is required"
}
```

**Product not found (404 Not Found)**
```json
{
  "error": "Product not found"
}
```

**Invalid quantity (400 Bad Request)**
```json
{
  "error": "Quantity must be at least 1"
}
```

**Exceeds stock (400 Bad Request)**
```json
{
  "error": "Quantity cannot exceed available stock (5)"
}
```

**Exceeds maximum (400 Bad Request)**
```json
{
  "error": "Quantity cannot exceed 99"
}
```

#### Behavior
- If product already in cart, quantity is **incremented**
- Validates against available stock
- Maximum 99 units per item
- Minimum 1 unit
- Captures price snapshot at time of adding

---

### 3. PUT /api/cart/update/<item_id>/
**Update cart item quantity**

#### Request
- Method: `PUT`
- Headers: 
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- URL Parameter: `item_id` (integer) - Cart item ID
- Body:
```json
{
  "qty": 5
}
```

#### Parameters
- `qty` (integer, required): New quantity (1-99)

#### Success Response (200 OK)
```json
{
  "message": "Cart item updated",
  "item": {
    "id": 1,
    "product": { /* full product object */ },
    "qty": 5,
    "price_at_addition": 29.99,
    "current_price": 29.99,
    "subtotal": 149.95,
    "added_at": "2025-12-02T10:30:00Z"
  }
}
```

#### Error Responses

**Cart item not found (404 Not Found)**
```json
{
  "error": "Cart item not found"
}
```

**Missing qty (400 Bad Request)**
```json
{
  "error": "qty is required"
}
```

**Invalid quantity (400 Bad Request)**
```json
{
  "error": "Quantity must be at least 1"
}
```

**Exceeds stock (400 Bad Request)**
```json
{
  "error": "Quantity cannot exceed available stock (5)"
}
```

#### Behavior
- Updates quantity to exact value (not incremental)
- Validates against stock and limits
- User can only update their own cart items

---

### 4. DELETE /api/cart/remove/<item_id>/
**Remove item from cart**

#### Request
- Method: `DELETE`
- Headers: `Authorization: Bearer <token>`
- URL Parameter: `item_id` (integer) - Cart item ID
- Body: None

#### Success Response (200 OK)
```json
{
  "message": "Item removed from cart"
}
```

#### Error Response (404 Not Found)
```json
{
  "error": "Cart item not found"
}
```

#### Behavior
- Permanently deletes cart item
- User can only delete their own cart items
- Safe to call on non-existent items (returns 404)

---

### 5. DELETE /api/cart/clear/
**Clear entire cart**

#### Request
- Method: `DELETE`
- Headers: `Authorization: Bearer <token>`
- Body: None

#### Success Response (200 OK)
```json
{
  "message": "Cart cleared",
  "items_removed": 3
}
```

#### Empty Cart Response (200 OK)
```json
{
  "message": "Cart cleared",
  "items_removed": 0
}
```

#### Error Response (401 Unauthorized)
```json
{
  "error": "Unauthorized"
}
```

#### Behavior
- Removes all items from user's cart
- Returns count of items removed
- Safe to call on empty cart
- Cart itself remains (only items are deleted)

---

### 6. GET /api/cart/count/
**Get total items count in cart**

#### Request
- Method: `GET`
- Headers: `Authorization: Bearer <token>`
- Body: None

#### Success Response (200 OK)
```json
{
  "count": 5,
  "unique_items": 2
}
```

#### Empty Cart Response (200 OK)
```json
{
  "count": 0,
  "unique_items": 0
}
```

#### Error Response (401 Unauthorized)
```json
{
  "error": "Unauthorized"
}
```

#### Response Fields
- `count`: Total quantity across all items (sum of quantities)
- `unique_items`: Number of different products in cart

#### Use Case
Perfect for displaying cart badge count in navigation/header without fetching full cart data.

---

## Validation Rules

### Quantity Validation
- **Minimum**: 1
- **Maximum**: 99 (CartItem.MAX_QUANTITY_PER_ITEM)
- **Stock Check**: Cannot exceed available product stock
- **Type**: Must be integer

### Cart Item Constraints
- **Unique Constraint**: One product per cart (cart, product) unique together
- **Ownership**: Users can only access/modify their own cart items
- **Price Snapshot**: Price is captured when item is first added and preserved

---

## Price Snapshot Feature

### How It Works
When a product is added to cart:
1. Current product price is saved in `price_at_addition` field
2. This price remains unchanged even if product price changes later
3. Subtotal calculations always use `price_at_addition`

### Benefits
- **Customer Protection**: Customers pay the price they saw when adding to cart
- **Transparency**: API returns both `price_at_addition` and `current_price`
- **Price Comparison**: Frontend can show if price increased/decreased

### Example
```json
{
  "qty": 2,
  "price_at_addition": 29.99,  // Price when added to cart
  "current_price": 39.99,       // Current product price (increased)
  "subtotal": 59.98             // Calculated using price_at_addition
}
```

---

## Error Handling

### Common HTTP Status Codes
- `200 OK`: Successful GET, PUT, DELETE operations
- `201 Created`: Successful POST (new item created)
- `400 Bad Request`: Validation errors, invalid data
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Resource not found (product, cart item)

### Error Response Format
All errors return JSON with `error` key:
```json
{
  "error": "Error message description"
}
```

---

## Security Features

### Authentication
- All endpoints require valid JWT token
- Tokens verified and decoded for each request
- User ID extracted from token for cart ownership

### Authorization
- Users can only access their own cart
- Cart items filtered by user ownership
- Prevents cross-user cart access

### Validation
- Input validation on all parameters
- Stock availability checks
- Quantity limit enforcement
- Product existence verification

---

## Testing

### Test Coverage
**26 comprehensive tests** covering:
- ✅ Successful operations (GET, POST, PUT, DELETE)
- ✅ Authentication requirements
- ✅ Validation (quantity, stock, limits)
- ✅ Error handling (404, 400, 401)
- ✅ Price snapshot preservation
- ✅ Cart count calculations
- ✅ Edge cases (empty cart, duplicates)

### Run Tests
```bash
cd backend
python3 manage.py test api.tests.test_cart_api -v 2 --settings=skincare_backend.test_settings
```

**Test Result**: All 26 tests PASSING ✅

---

## Integration with Models

### Database Models Used
- `Cart`: User's shopping cart (one-to-one with AppUser)
- `CartItem`: Individual items in cart (many-to-one with Cart)
- `Product`: Product information (referenced by CartItem)
- `AppUser`: User authentication (owns Cart)

### Model Validation
All model-level validations are enforced:
- Quantity min/max checks
- Stock availability
- Price snapshot capture
- Unique constraints

---

## Usage Examples

### Example 1: Add Product to Cart
```bash
curl -X POST http://localhost:8000/api/cart/add/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 5, "qty": 2}'
```

### Example 2: Fetch Cart
```bash
curl http://localhost:8000/api/cart/ \
  -H "Authorization: Bearer <your_token>"
```

### Example 3: Update Item Quantity
```bash
curl -X PUT http://localhost:8000/api/cart/update/1/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"qty": 5}'
```

### Example 4: Remove Item
```bash
curl -X DELETE http://localhost:8000/api/cart/remove/1/ \
  -H "Authorization: Bearer <your_token>"
```

### Example 5: Clear Cart
```bash
curl -X DELETE http://localhost:8000/api/cart/clear/ \
  -H "Authorization: Bearer <your_token>"
```

### Example 6: Get Cart Count
```bash
curl http://localhost:8000/api/cart/count/ \
  -H "Authorization: Bearer <your_token>"
```

---

## Frontend Integration Tips

### Display Cart Badge Count
```javascript
// Fetch count for navigation badge
const response = await fetch('/api/cart/count/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { count } = await response.json();
// Display count in cart icon badge
```

### Add to Cart with Feedback
```javascript
const addToCart = async (productId, qty = 1) => {
  const response = await fetch('/api/cart/add/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ product_id: productId, qty })
  });
  
  if (response.ok) {
    const data = await response.json();
    // Show success message
    alert(data.message);
    // Update cart count
    updateCartBadge();
  } else {
    const error = await response.json();
    alert(error.error);
  }
};
```

### Show Price Changes
```javascript
// Display if price changed since added to cart
const CartItem = ({ item }) => {
  const priceChanged = item.price_at_addition !== item.current_price;
  const priceIncreased = item.current_price > item.price_at_addition;
  
  return (
    <div>
      <h3>{item.product.title}</h3>
      <p>Price: ${item.price_at_addition}</p>
      {priceChanged && (
        <p className={priceIncreased ? 'text-red' : 'text-green'}>
          Current price: ${item.current_price}
          {priceIncreased ? ' (increased)' : ' (decreased)'}
        </p>
      )}
      <p>Subtotal: ${item.subtotal}</p>
    </div>
  );
};
```

---

## Files Modified/Created

### Modified Files
1. `backend/api/views.py` - Implemented 6 cart endpoints
2. `backend/api/urls.py` - Added cart URL patterns

### Created Files
3. `backend/api/tests/test_cart_api.py` - 26 comprehensive tests

---

## Summary

✅ **All Requirements Completed:**
- GET /api/cart/ - Fetch user's cart with all items
- POST /api/cart/add/ - Add product to cart
- PUT /api/cart/update/<item_id>/ - Update item quantity
- DELETE /api/cart/remove/<item_id>/ - Remove item from cart
- DELETE /api/cart/clear/ - Clear entire cart
- GET /api/cart/count/ - Get total items count in cart

**Features:**
- ✅ JWT authentication on all endpoints
- ✅ Comprehensive validation (quantity, stock, limits)
- ✅ Price snapshot preservation
- ✅ Proper error handling with descriptive messages
- ✅ Model-level validation enforcement
- ✅ Cart ownership security
- ✅ 26 tests covering all scenarios (100% passing)

**Status:** Production-ready ✅
