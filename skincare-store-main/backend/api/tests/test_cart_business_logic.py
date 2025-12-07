from django.test import TestCase, Client
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
import json
from api.models import Cart, CartItem, Product, AppUser
from api.utils import create_jwt


class CartBusinessLogicTestCase(TestCase):
    """Test suite for Cart business logic"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = AppUser.objects.create(
            name="Test User",
            email="test@example.com"
        )
        self.user.set_password("password123")
        self.user.save()
        
        # Create JWT token
        self.token = create_jwt({
            'user_id': self.user.id,
            'email': self.user.email
        })
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        
        # Create test products
        self.product_in_stock = Product.objects.create(
            title="In Stock Product",
            description="Product with stock",
            price=Decimal('50.00'),
            stock=10,
            category="skincare"
        )
        
        self.product_low_stock = Product.objects.create(
            title="Low Stock Product",
            description="Product with low stock",
            price=Decimal('30.00'),
            stock=2,
            category="makeup"
        )
        
        self.product_out_of_stock = Product.objects.create(
            title="Out of Stock Product",
            description="No stock available",
            price=Decimal('25.00'),
            stock=0,
            category="skincare"
        )
    
    # ===== Subtotal, Tax, and Total Calculations =====
    
    def test_cart_subtotal_calculation(self):
        """Test cart subtotal calculation"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=2)
        CartItem.objects.create(cart=cart, product=self.product_low_stock, qty=1)
        
        # Subtotal = (50 * 2) + (30 * 1) = 130
        expected_subtotal = Decimal('130.00')
        self.assertEqual(cart.get_subtotal(), expected_subtotal)
    
    def test_cart_tax_calculation(self):
        """Test cart tax calculation"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Subtotal = 50, Tax = 50 * 0.08 = 4.00
        expected_tax = Decimal('50.00') * Cart.TAX_RATE
        self.assertEqual(cart.get_tax(), expected_tax)
    
    def test_cart_total_calculation(self):
        """Test cart total calculation (subtotal + tax)"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=2)
        
        # Subtotal = 100, Tax = 8, Total = 108
        expected_total = Decimal('108.00')
        self.assertEqual(cart.get_total(), expected_total)
    
    def test_empty_cart_calculations(self):
        """Test calculations on empty cart"""
        cart = Cart.objects.create(user=self.user)
        
        self.assertEqual(cart.get_subtotal(), Decimal('0.00'))
        self.assertEqual(cart.get_tax(), Decimal('0.00'))
        self.assertEqual(cart.get_total(), Decimal('0.00'))
    
    # ===== Auto-merge Cart Items =====
    
    def test_add_same_product_increments_quantity(self):
        """Test adding same product multiple times increments quantity"""
        # Add product first time
        self.client.post(
            '/api/cart/add/',
            data=json.dumps({'product_id': self.product_in_stock.id, 'qty': 2}),
            content_type='application/json',
            **self.auth_headers
        )
        
        # Add same product again
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({'product_id': self.product_in_stock.id, 'qty': 3}),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Quantity should be merged: 2 + 3 = 5
        self.assertEqual(data['item']['qty'], 5)
        
        # Should still be one cart item, not two
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
    
    # ===== Stock Availability Checks =====
    
    def test_check_stock_before_adding(self):
        """Test stock is checked before adding to cart"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product_low_stock.id,
                'qty': 5  # More than available stock (2)
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('stock', data['error'].lower())
    
    def test_cannot_add_out_of_stock_product(self):
        """Test cannot add out-of-stock product to cart"""
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
        self.assertIn('stock', data['error'].lower())
    
    def test_cart_item_availability_status(self):
        """Test cart item availability status methods"""
        cart = Cart.objects.create(user=self.user)
        
        # In stock item
        item1 = CartItem.objects.create(
            cart=cart,
            product=self.product_in_stock,
            qty=2
        )
        self.assertTrue(item1.is_available())
        self.assertTrue(item1.is_in_stock())
        
        # Low stock item (qty exceeds stock)
        item2 = CartItem.objects.create(
            cart=cart,
            product=self.product_low_stock,
            qty=1
        )
        self.assertTrue(item2.is_available())
        
        # Change stock to 0
        self.product_low_stock.stock = 0
        self.product_low_stock.save()
        
        self.assertFalse(item2.is_available())
        self.assertFalse(item2.is_in_stock())
    
    # ===== Get Unavailable Items =====
    
    def test_get_unavailable_items_out_of_stock(self):
        """Test getting list of out-of-stock items"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Create item with stock available, then reduce to 0
        self.product_out_of_stock.stock = 1  # Temporarily set to 1
        self.product_out_of_stock.save()
        CartItem.objects.create(cart=cart, product=self.product_out_of_stock, qty=1)
        self.product_out_of_stock.stock = 0  # Now set back to 0
        self.product_out_of_stock.save()
        
        unavailable = cart.get_unavailable_items()
        
        self.assertEqual(len(unavailable), 1)
        self.assertEqual(unavailable[0]['status'], 'out_of_stock')
        self.assertEqual(unavailable[0]['product_id'], self.product_out_of_stock.id)
    
    def test_get_unavailable_items_insufficient_stock(self):
        """Test getting items with insufficient stock"""
        cart = Cart.objects.create(user=self.user)
        
        # Manually create item with qty > stock (bypassing validation for test)
        item = CartItem(cart=cart, product=self.product_low_stock, qty=1)
        item.save()
        
        # Change stock to less than quantity
        self.product_low_stock.stock = 0
        self.product_low_stock.save()
        
        unavailable = cart.get_unavailable_items()
        
        self.assertEqual(len(unavailable), 1)
        self.assertEqual(unavailable[0]['status'], 'out_of_stock')
    
    # ===== Remove Out-of-Stock Items =====
    
    def test_remove_out_of_stock_items(self):
        """Test removing out-of-stock items from cart"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Create item with stock available, then reduce to 0
        self.product_out_of_stock.stock = 1
        self.product_out_of_stock.save()
        CartItem.objects.create(cart=cart, product=self.product_out_of_stock, qty=1)
        self.product_out_of_stock.stock = 0
        self.product_out_of_stock.save()
        
        removed = cart.remove_out_of_stock_items()
        
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]['product_id'], self.product_out_of_stock.id)
        
        # Cart should only have in-stock item
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().product.id, self.product_in_stock.id)
    
    def test_remove_out_of_stock_api_endpoint(self):
        """Test API endpoint for removing out-of-stock items"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Create item with stock available, then reduce to 0
        self.product_out_of_stock.stock = 1
        self.product_out_of_stock.save()
        CartItem.objects.create(cart=cart, product=self.product_out_of_stock, qty=1)
        self.product_out_of_stock.stock = 0
        self.product_out_of_stock.save()
        
        response = self.client.delete(
            '/api/cart/remove-out-of-stock/',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('removed_items', data)
        self.assertEqual(data['count'], 1)
        
        # Verify cart only has in-stock item
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 1)
    
    # ===== Cart Expiration Logic =====
    
    def test_cart_is_expired_check(self):
        """Test checking if cart is expired"""
        cart = Cart.objects.create(user=self.user)
        
        # New cart should not be expired
        self.assertFalse(cart.is_expired())
        
        # Set updated_at to past expiration using database update to bypass auto_now
        old_date = timezone.now() - timedelta(days=Cart.CART_EXPIRATION_DAYS + 1)
        Cart.objects.filter(id=cart.id).update(updated_at=old_date)
        
        # Now cart should be expired
        self.assertTrue(cart.is_expired())
    
    def test_clear_if_expired(self):
        """Test cart is cleared if expired"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Set cart to expired using database update to bypass auto_now
        old_date = timezone.now() - timedelta(days=Cart.CART_EXPIRATION_DAYS + 1)
        Cart.objects.filter(id=cart.id).update(updated_at=old_date)
        
        # Clear if expired
        was_cleared = cart.clear_if_expired()
        
        self.assertTrue(was_cleared)
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)
    
    def test_get_cart_clears_expired_cart(self):
        """Test GET /api/cart/ auto-clears expired cart"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=2)
        
        # Set cart to expired using database update to bypass auto_now
        old_date = timezone.now() - timedelta(days=Cart.CART_EXPIRATION_DAYS + 1)
        Cart.objects.filter(id=cart.id).update(updated_at=old_date)
        
        response = self.client.get('/api/cart/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertIn('inactivity', data['message'])
        self.assertEqual(len(data['items']), 0)
    
    # ===== Cart Validate Endpoint =====
    
    def test_validate_cart_all_valid(self):
        """Test cart validation with all valid items"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        response = self.client.get('/api/cart/validate/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['is_valid'])
        self.assertFalse(data['is_expired'])
        self.assertEqual(len(data['unavailable_items']), 0)
    
    def test_validate_cart_with_unavailable_items(self):
        """Test cart validation with unavailable items"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Create item with stock available, then reduce to 0
        self.product_out_of_stock.stock = 1
        self.product_out_of_stock.save()
        CartItem.objects.create(cart=cart, product=self.product_out_of_stock, qty=1)
        self.product_out_of_stock.stock = 0
        self.product_out_of_stock.save()
        
        response = self.client.get('/api/cart/validate/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['is_valid'])
        self.assertEqual(len(data['unavailable_items']), 1)
        self.assertEqual(data['total_items'], 2)
        self.assertEqual(data['valid_items'], 1)
    
    # ===== Cart Summary Endpoint =====
    
    def test_cart_summary_endpoint(self):
        """Test cart summary endpoint with calculations"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=2)
        
        response = self.client.get('/api/cart/summary/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('subtotal', data)
        self.assertIn('tax', data)
        self.assertIn('total', data)
        self.assertIn('tax_rate', data)
        self.assertIn('item_count', data)
        self.assertIn('unique_items', data)
        
        # Verify calculations
        self.assertEqual(data['subtotal'], 100.00)  # 50 * 2
        self.assertEqual(data['tax'], 8.00)  # 100 * 0.08
        self.assertEqual(data['total'], 108.00)  # 100 + 8
        self.assertEqual(data['item_count'], 2)
        self.assertEqual(data['unique_items'], 1)
    
    # ===== Cart to_dict with Calculations =====
    
    def test_cart_to_dict_includes_calculations(self):
        """Test cart to_dict includes subtotal, tax, and total"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        cart_dict = cart.to_dict(include_calculations=True)
        
        self.assertIn('subtotal', cart_dict)
        self.assertIn('tax', cart_dict)
        self.assertIn('total', cart_dict)
        self.assertIn('tax_rate', cart_dict)
        self.assertIn('item_count', cart_dict)
        self.assertIn('unique_items', cart_dict)
    
    def test_cart_to_dict_without_calculations(self):
        """Test cart to_dict can exclude calculations"""
        cart = Cart.objects.create(user=self.user)
        
        cart_dict = cart.to_dict(include_calculations=False)
        
        self.assertNotIn('subtotal', cart_dict)
        self.assertNotIn('tax', cart_dict)
        self.assertNotIn('total', cart_dict)
    
    # ===== Get Cart with Unavailable Items Info =====
    
    def test_get_cart_includes_unavailable_items_info(self):
        """Test GET /api/cart/ includes unavailable items information"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        # Create item with stock available, then reduce to 0
        self.product_out_of_stock.stock = 1
        self.product_out_of_stock.save()
        CartItem.objects.create(cart=cart, product=self.product_out_of_stock, qty=1)
        self.product_out_of_stock.stock = 0
        self.product_out_of_stock.save()
        
        response = self.client.get('/api/cart/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['has_unavailable_items'])
        self.assertIn('unavailable_items', data)
        self.assertEqual(len(data['unavailable_items']), 1)
    
    def test_get_cart_no_unavailable_items(self):
        """Test GET /api/cart/ when all items are available"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_in_stock, qty=1)
        
        response = self.client.get('/api/cart/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['has_unavailable_items'])
    
    # ===== Cart Item Max Available Quantity =====
    
    def test_cart_item_max_available_quantity(self):
        """Test getting max available quantity for cart item"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product_low_stock,
            qty=1
        )
        
        # Stock is 2, max per item is 99, so should return 2
        self.assertEqual(item.get_max_available_qty(), 2)
        
        # Change stock to high number
        self.product_low_stock.stock = 150
        self.product_low_stock.save()
        
        # Should return MAX_QUANTITY_PER_ITEM (99)
        self.assertEqual(item.get_max_available_qty(), 99)
