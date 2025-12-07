from django.test import TestCase
from decimal import Decimal
from api.models import Cart, CartItem, Product, AppUser


class CartModelTestCase(TestCase):
    """Test suite for Cart and CartItem models"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = AppUser.objects.create(
            name="Test User",
            email="test@example.com"
        )
        self.user.set_password("password123")
        self.user.save()
        
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
        
        # Create cart for user
        self.cart = Cart.objects.create(user=self.user)
    
    def test_cart_creation_with_defaults(self):
        """Test cart is created with proper default values"""
        self.assertTrue(self.cart.is_active)
        self.assertIsNotNone(self.cart.created_at)
        self.assertIsNotNone(self.cart.updated_at)
        self.assertEqual(self.cart.user, self.user)
    
    def test_cart_to_dict(self):
        """Test cart serialization to dictionary"""
        cart_dict = self.cart.to_dict()
        self.assertIn('id', cart_dict)
        self.assertIn('user_id', cart_dict)
        self.assertIn('is_active', cart_dict)
        self.assertIn('items', cart_dict)
        self.assertIn('created_at', cart_dict)
        self.assertIn('updated_at', cart_dict)
        self.assertEqual(cart_dict['user_id'], self.user.id)
        self.assertTrue(cart_dict['is_active'])
        self.assertEqual(len(cart_dict['items']), 0)
    
    def test_cart_item_creation_with_price_snapshot(self):
        """Test cart item automatically captures price at time of addition"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            qty=2
        )
        
        self.assertEqual(cart_item.price_at_addition, self.product1.price)
        self.assertEqual(cart_item.qty, 2)
        self.assertIsNotNone(cart_item.added_at)
    
    def test_cart_item_price_snapshot_preserved(self):
        """Test price snapshot is preserved when product price changes"""
        # Create cart item with current price
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            qty=1
        )
        original_price = cart_item.price_at_addition
        
        # Change product price
        self.product1.price = Decimal('39.99')
        self.product1.save()
        
        # Reload cart item
        cart_item.refresh_from_db()
        
        # Price snapshot should remain unchanged
        self.assertEqual(cart_item.price_at_addition, original_price)
        self.assertNotEqual(cart_item.price_at_addition, self.product1.price)
    
    def test_cart_item_quantity_validation_minimum(self):
        """Test cart item quantity must be at least 1"""
        cart_item = CartItem(
            cart=self.cart,
            product=self.product1,
            qty=0  # Invalid quantity
        )
        
        with self.assertRaises(ValueError) as context:
            cart_item.save()
        
        self.assertIn("Quantity must be at least 1", str(context.exception))
    
    def test_cart_item_quantity_validation_maximum(self):
        """Test cart item quantity cannot exceed maximum limit"""
        cart_item = CartItem(
            cart=self.cart,
            product=self.product1,
            qty=100  # Exceeds MAX_QUANTITY_PER_ITEM (99)
        )
        
        with self.assertRaises(ValueError) as context:
            cart_item.save()
        
        self.assertIn("Quantity cannot exceed 99", str(context.exception))
    
    def test_cart_item_quantity_validation_against_stock(self):
        """Test cart item quantity cannot exceed available stock"""
        cart_item = CartItem(
            cart=self.cart,
            product=self.product2,  # Stock is 5
            qty=10  # Exceeds available stock
        )
        
        with self.assertRaises(ValueError) as context:
            cart_item.save()
        
        self.assertIn("Quantity cannot exceed available stock", str(context.exception))
        self.assertIn("(5)", str(context.exception))
    
    def test_cart_item_unique_together_constraint(self):
        """Test cart and product must be unique together"""
        # Create first cart item
        CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            qty=1
        )
        
        # Try to create duplicate (same cart and product)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                cart=self.cart,
                product=self.product1,
                qty=2
            )
    
    def test_cart_item_to_dict(self):
        """Test cart item serialization includes all necessary fields"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            qty=3
        )
        
        item_dict = cart_item.to_dict()
        
        self.assertIn('id', item_dict)
        self.assertIn('product', item_dict)
        self.assertIn('qty', item_dict)
        self.assertIn('price_at_addition', item_dict)
        self.assertIn('current_price', item_dict)
        self.assertIn('subtotal', item_dict)
        self.assertIn('added_at', item_dict)
        
        self.assertEqual(item_dict['qty'], 3)
        self.assertEqual(item_dict['price_at_addition'], float(self.product1.price))
        self.assertEqual(item_dict['current_price'], float(self.product1.price))
        self.assertEqual(item_dict['subtotal'], float(self.product1.price * 3))
    
    def test_cart_item_subtotal_calculation_with_price_change(self):
        """Test subtotal uses price_at_addition, not current price"""
        # Create cart item
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            qty=2
        )
        original_subtotal = float(cart_item.price_at_addition * cart_item.qty)
        
        # Change product price
        self.product1.price = Decimal('59.99')
        self.product1.save()
        
        # Get updated dict
        item_dict = cart_item.to_dict()
        
        # Subtotal should still use original price
        self.assertEqual(item_dict['subtotal'], original_subtotal)
        self.assertNotEqual(item_dict['current_price'], item_dict['price_at_addition'])
    
    def test_cart_with_multiple_items(self):
        """Test cart can contain multiple different items"""
        CartItem.objects.create(cart=self.cart, product=self.product1, qty=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, qty=1)
        
        cart_dict = self.cart.to_dict()
        
        self.assertEqual(len(cart_dict['items']), 2)
        self.assertEqual(self.cart.items.count(), 2)
    
    def test_cart_item_ordering(self):
        """Test cart items are ordered by added_at descending"""
        import time
        
        item1 = CartItem.objects.create(cart=self.cart, product=self.product1, qty=1)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        item2 = CartItem.objects.create(cart=self.cart, product=self.product2, qty=1)
        
        items = list(self.cart.items.all())
        
        # Most recently added should be first
        self.assertEqual(items[0].id, item2.id)
        self.assertEqual(items[1].id, item1.id)
    
    def test_cart_inactive_flag(self):
        """Test cart can be marked as inactive"""
        self.cart.is_active = False
        self.cart.save()
        
        self.cart.refresh_from_db()
        self.assertFalse(self.cart.is_active)
    
    def test_cart_item_max_quantity_constant(self):
        """Test MAX_QUANTITY_PER_ITEM constant is properly defined"""
        self.assertEqual(CartItem.MAX_QUANTITY_PER_ITEM, 99)
