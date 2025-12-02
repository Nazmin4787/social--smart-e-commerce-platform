import json
from django.test import TestCase, Client
from api.models import AppUser, Product, Order, OrderItem, Address


class AdminOrderAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create regular user
        self.user = AppUser.objects.create(name='Customer', email='customer@example.com')
        self.user.set_password('password')
        self.user.save()

        # Create admin user
        self.admin = AppUser.objects.create(name='Admin', email='admin@example.com', is_staff=True)
        self.admin.set_password('adminpass')
        self.admin.save()

        # Create tokens
        from api.utils import create_jwt
        self.user_token = create_jwt({'user_id': self.user.id, 'email': self.user.email})
        self.admin_token = create_jwt({'user_id': self.admin.id, 'email': self.admin.email})

        # Create test products
        self.product1 = Product.objects.create(
            title='Test Product 1',
            description='Product 1',
            price=29.99,
            stock=100,
            category='test'
        )
        self.product2 = Product.objects.create(
            title='Test Product 2',
            description='Product 2',
            price=49.99,
            stock=50,
            category='test'
        )

        # Create test address for user
        self.address = Address.objects.create(
            user=self.user,
            address_type='shipping',
            full_name='Customer Name',
            phone='1234567890',
            address_line1='123 Test St',
            city='Test City',
            state='Test State',
            postal_code='12345',
            country='USA',
            is_default=True
        )

        # Create test orders
        self.order1 = Order.objects.create(user=self.user, total=29.99, status='pending')
        OrderItem.objects.create(order=self.order1, product=self.product1, qty=1, price=29.99)

        self.order2 = Order.objects.create(user=self.user, total=99.98, status='processing')
        OrderItem.objects.create(order=self.order2, product=self.product1, qty=1, price=29.99)
        OrderItem.objects.create(order=self.order2, product=self.product2, qty=1, price=49.99)

    def test_admin_orders_list(self):
        """Test admin can view all orders with details"""
        resp = self.client.get('/api/admin/orders/', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        
        # Check order structure
        order = data[0]
        self.assertIn('id', order)
        self.assertIn('user', order)
        self.assertIn('total', order)
        self.assertIn('status', order)
        self.assertIn('items', order)
        self.assertIn('shipping_address', order)
        
        # Verify user details
        self.assertEqual(order['user']['email'], 'customer@example.com')
        
        # Verify items are included
        self.assertGreater(len(order['items']), 0)

    def test_admin_orders_filter_by_status(self):
        """Test filtering orders by status"""
        resp = self.client.get('/api/admin/orders/?status=pending', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['status'], 'pending')

    def test_admin_orders_filter_by_customer(self):
        """Test filtering orders by customer name/email"""
        resp = self.client.get('/api/admin/orders/?customer=Customer', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data), 2)

    def test_admin_orders_forbidden_for_non_admin(self):
        """Test non-admin users cannot access orders list"""
        resp = self.client.get('/api/admin/orders/', HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        self.assertIn(resp.status_code, (401, 403))

    def test_admin_update_order_status(self):
        """Test admin can update order status"""
        payload = {'status': 'shipped'}
        resp = self.client.patch(
            f'/api/admin/orders/{self.order1.id}/status/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'shipped')
        
        # Verify in database
        self.order1.refresh_from_db()
        self.assertEqual(self.order1.status, 'shipped')

    def test_admin_update_order_status_validation(self):
        """Test order status update validates allowed values"""
        payload = {'status': 'invalid_status'}
        resp = self.client.patch(
            f'/api/admin/orders/{self.order1.id}/status/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(resp.status_code, 400)

    def test_admin_update_order_status_not_found(self):
        """Test updating non-existent order returns 404"""
        payload = {'status': 'shipped'}
        resp = self.client.patch(
            '/api/admin/orders/99999/status/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(resp.status_code, 404)

    def test_admin_update_order_status_forbidden_for_non_admin(self):
        """Test non-admin users cannot update order status"""
        payload = {'status': 'shipped'}
        resp = self.client.patch(
            f'/api/admin/orders/{self.order1.id}/status/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_order_includes_shipping_address(self):
        """Test order response includes shipping address"""
        resp = self.client.get('/api/admin/orders/', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        
        order = data[0]
        self.assertIsNotNone(order['shipping_address'])
        self.assertIn('full_name', order['shipping_address'])
        self.assertEqual(order['shipping_address']['full_name'], 'Customer Name')

    def test_admin_update_order_missing_status(self):
        """Test updating order without status field returns error"""
        payload = {}
        resp = self.client.patch(
            f'/api/admin/orders/{self.order1.id}/status/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(resp.status_code, 400)
