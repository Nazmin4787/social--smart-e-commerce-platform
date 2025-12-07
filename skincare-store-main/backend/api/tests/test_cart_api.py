from django.test import TestCase, Client
from decimal import Decimal
import json
from api.models import Cart, CartItem, Product, AppUser
from api.utils import create_jwt


class CartAPITestCase(TestCase):
    """Test suite for Cart API endpoints"""
    
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
        self.product1 = Product.objects.create(
            title="Test Product 1",
            description="Test description",
            price=Decimal('29.99'),
            stock=10,
            category="skincare"
        )
        
        self.product2 = Product.objects.create(
            title="Test Product 2",
            description="Another product",
            price=Decimal('49.99'),
            stock=5,
            category="makeup"
        )
        
        self.product3 = Product.objects.create(
            title="Out of Stock Product",
            description="No stock",
            price=Decimal('19.99'),
            stock=0,
            category="skincare"
        )
    
    def test_get_empty_cart(self):
        """Test fetching an empty cart"""
        response = self.client.get('/api/cart/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('id', data)
        self.assertIn('items', data)
        self.assertIn('is_active', data)
        self.assertEqual(len(data['items']), 0)
        self.assertTrue(data['is_active'])
    
    def test_get_cart_unauthorized(self):
        """Test fetching cart without authentication"""
        response = self.client.get('/api/cart/')
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)
    
    def test_add_to_cart_success(self):
        """Test adding a product to cart successfully"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product1.id,
                'qty': 2
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertIn('item', data)
        self.assertEqual(data['item']['qty'], 2)
        self.assertEqual(data['item']['price_at_addition'], float(self.product1.price))
    
    def test_add_to_cart_increment_quantity(self):
        """Test adding same product twice increments quantity"""
        # Add first time
        self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product1.id,
                'qty': 2
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        # Add second time
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product1.id,
                'qty': 3
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['item']['qty'], 5)  # 2 + 3
    
    def test_add_to_cart_invalid_product(self):
        """Test adding non-existent product to cart"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': 99999,
                'qty': 1
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Product not found', data['error'])
    
    def test_add_to_cart_exceeds_stock(self):
        """Test adding quantity that exceeds available stock"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product2.id,  # Stock is 5
                'qty': 10
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('stock', data['error'].lower())
    
    def test_add_to_cart_zero_quantity(self):
        """Test adding zero quantity to cart"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product1.id,
                'qty': 0
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_add_to_cart_exceeds_max_quantity(self):
        """Test adding quantity exceeding MAX_QUANTITY_PER_ITEM"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product1.id,
                'qty': 100  # Exceeds MAX_QUANTITY_PER_ITEM (99)
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_add_to_cart_missing_product_id(self):
        """Test adding to cart without product_id"""
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
        self.assertIn('error', data)
        self.assertIn('product_id', data['error'])
    
    def test_update_cart_item_success(self):
        """Test updating cart item quantity"""
        # Add item first
        cart = Cart.objects.get_or_create(user=self.user)[0]
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            qty=2
        )
        
        # Update quantity
        response = self.client.put(
            f'/api/cart/update/{cart_item.id}/',
            data=json.dumps({
                'qty': 5
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertEqual(data['item']['qty'], 5)
    
    def test_update_cart_item_not_found(self):
        """Test updating non-existent cart item"""
        response = self.client.put(
            '/api/cart/update/99999/',
            data=json.dumps({
                'qty': 5
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
    
    def test_update_cart_item_invalid_quantity(self):
        """Test updating cart item with invalid quantity"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            qty=2
        )
        
        response = self.client.put(
            f'/api/cart/update/{cart_item.id}/',
            data=json.dumps({
                'qty': 0  # Invalid
            }),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_update_cart_item_missing_qty(self):
        """Test updating cart item without qty field"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            qty=2
        )
        
        response = self.client.put(
            f'/api/cart/update/{cart_item.id}/',
            data=json.dumps({}),
            content_type='application/json',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('qty', data['error'])
    
    def test_remove_cart_item_success(self):
        """Test removing item from cart"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            qty=2
        )
        
        response = self.client.delete(
            f'/api/cart/remove/{cart_item.id}/',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        
        # Verify item is deleted
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())
    
    def test_remove_cart_item_not_found(self):
        """Test removing non-existent cart item"""
        response = self.client.delete(
            '/api/cart/remove/99999/',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
    
    def test_clear_cart_success(self):
        """Test clearing entire cart"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        CartItem.objects.create(cart=cart, product=self.product1, qty=2)
        CartItem.objects.create(cart=cart, product=self.product2, qty=1)
        
        response = self.client.delete(
            '/api/cart/clear/',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertIn('items_removed', data)
        self.assertEqual(data['items_removed'], 2)
        
        # Verify cart is empty
        self.assertEqual(cart.items.count(), 0)
    
    def test_clear_empty_cart(self):
        """Test clearing an already empty cart"""
        response = self.client.delete(
            '/api/cart/clear/',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['items_removed'], 0)
    
    def test_get_cart_count(self):
        """Test getting cart item count"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        CartItem.objects.create(cart=cart, product=self.product1, qty=3)
        CartItem.objects.create(cart=cart, product=self.product2, qty=2)
        
        response = self.client.get('/api/cart/count/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('count', data)
        self.assertIn('unique_items', data)
        self.assertEqual(data['count'], 5)  # 3 + 2
        self.assertEqual(data['unique_items'], 2)
    
    def test_get_cart_count_empty(self):
        """Test cart count for empty cart"""
        response = self.client.get('/api/cart/count/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['unique_items'], 0)
    
    def test_get_cart_with_items(self):
        """Test fetching cart with multiple items"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        CartItem.objects.create(cart=cart, product=self.product1, qty=2)
        CartItem.objects.create(cart=cart, product=self.product2, qty=1)
        
        response = self.client.get('/api/cart/', **self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data['items']), 2)
        
        # Check item structure
        first_item = data['items'][0]
        self.assertIn('product', first_item)
        self.assertIn('qty', first_item)
        self.assertIn('price_at_addition', first_item)
        self.assertIn('current_price', first_item)
        self.assertIn('subtotal', first_item)
    
    def test_cart_price_snapshot_preserved(self):
        """Test that price snapshot is preserved in cart items"""
        cart = Cart.objects.get_or_create(user=self.user)[0]
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            qty=1
        )
        
        original_price = cart_item.price_at_addition
        
        # Change product price
        self.product1.price = Decimal('99.99')
        self.product1.save()
        
        # Fetch cart
        response = self.client.get('/api/cart/', **self.auth_headers)
        data = response.json()
        
        # Price at addition should be original price
        item_data = data['items'][0]
        self.assertEqual(item_data['price_at_addition'], float(original_price))
        self.assertEqual(item_data['current_price'], 99.99)
        self.assertNotEqual(item_data['price_at_addition'], item_data['current_price'])
    
    def test_add_to_cart_unauthorized(self):
        """Test adding to cart without authentication"""
        response = self.client.post(
            '/api/cart/add/',
            data=json.dumps({
                'product_id': self.product1.id,
                'qty': 1
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_update_cart_item_unauthorized(self):
        """Test updating cart item without authentication"""
        response = self.client.put(
            '/api/cart/update/1/',
            data=json.dumps({'qty': 5}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_remove_cart_item_unauthorized(self):
        """Test removing cart item without authentication"""
        response = self.client.delete('/api/cart/remove/1/')
        
        self.assertEqual(response.status_code, 401)
    
    def test_clear_cart_unauthorized(self):
        """Test clearing cart without authentication"""
        response = self.client.delete('/api/cart/clear/')
        
        self.assertEqual(response.status_code, 401)
    
    def test_cart_count_unauthorized(self):
        """Test getting cart count without authentication"""
        response = self.client.get('/api/cart/count/')
        
        self.assertEqual(response.status_code, 401)
