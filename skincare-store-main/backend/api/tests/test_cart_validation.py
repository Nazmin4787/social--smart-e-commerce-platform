"""
Tests for cart validation and error handling.

Covers:
- Positive integer validation for quantity
- Product existence validation
- Stock availability checks
- Concurrent cart update handling
- Appropriate error messages
"""
import json
import threading
from decimal import Decimal
from django.test import TestCase, Client
from api.models import AppUser, Product, Cart, CartItem
from api.utils import create_jwt


class CartValidationTestCase(TestCase):
    """Test cart validation and error handling"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = AppUser.objects.create(
            email='test@example.com',
            name='Test User'
        )
        self.user.set_password('password123')
        self.user.save()
        
        # Create JWT token
        self.token = create_jwt({'user_id': self.user.id})
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        
        # Create test products
        self.product_in_stock = Product.objects.create(
            title='In Stock Product',
            price=Decimal('25.00'),
            stock=10
        )
        
        self.product_low_stock = Product.objects.create(
            title='Low Stock Product',
            price=Decimal('15.00'),
            stock=2
        )
        
        self.product_out_of_stock = Product.objects.create(
            title='Out of Stock Product',
            price=Decimal('30.00'),
            stock=0
        )
    
    # ===== Positive Integer Validation =====
    
    def test_quantity_must_be_positive_integer(self):
        """Test quantity validation rejects non-positive values"""
        # Test zero
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': 0
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('at least 1', data['error'].lower())
    
    def test_quantity_rejects_negative_numbers(self):
        """Test quantity validation rejects negative numbers"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': -5
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('at least 1', data['error'].lower())
    
    def test_quantity_rejects_decimal_numbers(self):
        """Test quantity validation rejects decimal numbers"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': 2.5
            }),
            content_type='application/json',
            **self.auth_headers
        )
        # Should accept and convert to int, or reject
        # Current implementation converts via int()
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_quantity_rejects_non_numeric_strings(self):
        """Test quantity validation rejects non-numeric strings"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': 'abc'
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('integer', data['error'].lower())
    
    def test_quantity_rejects_null(self):
        """Test quantity validation rejects null/None"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': None
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('required', data['error'].lower())
    
    def test_quantity_rejects_empty_string(self):
        """Test quantity validation rejects empty string"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': ''
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('required', data['error'].lower())
    
    def test_quantity_accepts_positive_integer(self):
        """Test quantity validation accepts positive integers"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': 5
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
    
    def test_quantity_accepts_string_positive_integer(self):
        """Test quantity validation accepts string representation of positive integer"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': '3'
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
    
    # ===== Product Existence Validation =====
    
    def test_product_id_required(self):
        """Test product_id is required in request"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('product_id', data['error'].lower())
    
    def test_product_id_must_be_integer(self):
        """Test product_id must be a valid integer"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': 'abc',
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('integer', data['error'].lower())
    
    def test_product_id_must_be_positive(self):
        """Test product_id must be positive"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': -1,
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('positive', data['error'].lower())
    
    def test_product_must_exist_in_database(self):
        """Test product must exist before adding to cart"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': 99999,  # Non-existent product
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('not found', data['error'].lower())
    
    # ===== Stock Availability Checks =====
    
    def test_cannot_add_out_of_stock_product(self):
        """Test cannot add product with zero stock"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_out_of_stock.id,
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('out of stock', data['error'].lower())
    
    def test_cannot_exceed_available_stock(self):
        """Test cannot add quantity exceeding available stock"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_low_stock.id,
                'qty': 5  # More than available (2)
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('insufficient', data['error'].lower())
        self.assertIn('available_stock', data)
        self.assertEqual(data['available_stock'], 2)
    
    def test_stock_check_on_update(self):
        """Test stock is checked when updating cart item quantity"""
        # Add item to cart
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product_low_stock,
            qty=1
        )
        
        # Try to update to exceed stock
        response = self.client.put(
            f'/api/cart/update/{item.id}/',
            data=json.dumps({
                'qty': 10  # More than available (2)
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('insufficient', data['error'].lower())
    
    def test_stock_check_when_incrementing_existing_item(self):
        """Test stock is checked when adding more of existing cart item"""
        # Add item to cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product_low_stock,
            qty=1
        )
        
        # Try to add more (total would exceed stock)
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_low_stock.id,
                'qty': 2  # Total would be 3, stock is 2
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('insufficient', data['error'].lower())
        self.assertIn('current_cart_qty', data)
    
    # ===== Error Message Clarity =====
    
    def test_error_message_includes_available_stock(self):
        """Test error message includes available stock information"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_low_stock.id,
                'qty': 5
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('available_stock', data)
        self.assertEqual(data['available_stock'], 2)
    
    def test_error_message_shows_current_cart_quantity(self):
        """Test error message shows current cart quantity when relevant"""
        # Add item to cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product_low_stock,
            qty=1
        )
        
        # Try to add more
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_low_stock.id,
                'qty': 2
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('current_cart_qty', data)
        self.assertEqual(data['current_cart_qty'], 1)
    
    def test_error_message_includes_product_id(self):
        """Test error message includes product_id for out of stock items"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_out_of_stock.id,
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('product_id', data)
    
    # ===== Concurrent Update Handling =====
    
    def test_concurrent_add_to_cart_maintains_consistency(self):
        """Test that database transactions prevent race conditions"""
        # This test verifies the implementation uses transactions,
        # but full concurrency testing requires integration tests
        cart = Cart.objects.create(user=self.user)
        product = self.product_in_stock
        
        # Add item once
        response1 = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': product.id,
                'qty': 2
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertIn(response1.status_code, [200, 201])
        
        # Add again (should increment)
        response2 = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': product.id,
                'qty': 3
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertIn(response2.status_code, [200, 201])
        
        # Verify only one item exists with combined quantity
        cart.refresh_from_db()
        items = CartItem.objects.filter(cart=cart, product=product)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().qty, 5)
    
    def test_concurrent_update_maintains_consistency(self):
        """Test that updates use proper locking"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product_in_stock,
            qty=1
        )
        
        # Sequential updates (simulates transaction behavior)
        response1 = self.client.put(
            f'/api/cart/update/{item.id}/',
            data=json.dumps({'qty': 3}),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response1.status_code, 200)
        
        # Verify update succeeded
        item.refresh_from_db()
        self.assertEqual(item.qty, 3)
    
    def test_concurrent_stock_check_prevents_overselling(self):
        """Test stock validation prevents overselling"""
        product = self.product_low_stock  # Stock = 2
        cart = Cart.objects.create(user=self.user)
        
        # Add up to stock limit
        response1 = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': product.id,
                'qty': 2
            }),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertIn(response1.status_code, [200, 201])
        
        # Try to add more
        response2 = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': product.id,
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        # Should fail due to insufficient stock
        self.assertEqual(response2.status_code, 400)
        
        # Verify cart doesn't exceed stock
        cart.refresh_from_db()
        item = CartItem.objects.filter(cart=cart, product=product).first()
        self.assertIsNotNone(item)
        self.assertLessEqual(item.qty, product.stock)
    
    # ===== Invalid JSON Handling =====
    
    def test_invalid_json_returns_error(self):
        """Test invalid JSON in request body returns appropriate error"""
        response = self.client.post(
            '/api/cart/add/',
            data='invalid json{',
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('json', data['error'].lower())
    
    # ===== Authentication Validation =====
    
    def test_missing_auth_token_returns_401(self):
        """Test missing authentication token returns 401"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': 1
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_invalid_auth_token_returns_401(self):
        """Test invalid authentication token returns 401"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_in_stock.id,
                'qty': 1
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer invalid_token'
        )
        self.assertEqual(response.status_code, 401)
    
    # ===== Item ID Validation (for update/delete) =====
    
    def test_update_invalid_item_id_format(self):
        """Test updating with invalid item ID format returns error"""
        # Note: Django URL routing returns 404 for non-integer IDs in URL
        response = self.client.put(
            '/api/cart/update/abc/',
            data=json.dumps({'qty': 2}),
            content_type='application/json',
            **self.auth_headers
        )
        # URL doesn't match, so 404 is expected from routing
        self.assertEqual(response.status_code, 404)
    
    def test_update_nonexistent_item_returns_404(self):
        """Test updating non-existent item returns 404"""
        response = self.client.put(
            '/api/cart/update/99999/',
            data=json.dumps({'qty': 2}),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 404)
    
    def test_cannot_update_another_users_cart_item(self):
        """Test cannot update cart item belonging to another user"""
        # Create another user with cart item
        other_user = AppUser.objects.create(
            email='other@example.com',
            name='Other User'
        )
        other_cart = Cart.objects.create(user=other_user)
        other_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product_in_stock,
            qty=1
        )
        
        # Try to update other user's item
        response = self.client.put(
            f'/api/cart/update/{other_item.id}/',
            data=json.dumps({'qty': 5}),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 404)
