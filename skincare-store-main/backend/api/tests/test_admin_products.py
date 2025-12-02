import json
from django.test import TestCase, Client
from api.models import AppUser, Product


class AdminProductAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # regular user
        self.user = AppUser.objects.create(name='User', email='userprod@example.com')
        self.user.set_password('password')
        self.user.save()

        # admin user
        self.admin = AppUser.objects.create(name='Admin', email='adminprod@example.com', is_staff=True)
        self.admin.set_password('adminpass')
        self.admin.save()

        from api.utils import create_jwt
        self.user_token = create_jwt({'user_id': self.user.id, 'email': self.user.email})
        self.admin_token = create_jwt({'user_id': self.admin.id, 'email': self.admin.email})

    def test_create_product_and_admin_list(self):
        # Create product via public create endpoint
        payload = {
            'title': 'Test Product Admin',
            'description': 'A product created during tests',
            'price': 19.99,
            'stock': 10,
            'images': [],
            'category': 'testing'
        }
        resp = self.client.post('/api/products/create/', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        # create_product does not enforce admin, but should succeed
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertIn('id', data)

        # Admin list should include the product
        resp2 = self.client.get('/api/admin/products/list/', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp2.status_code, 200)
        data2 = json.loads(resp2.content)
        self.assertIn('results', data2)
        titles = [p['title'] for p in data2.get('results', [])]
        self.assertIn('Test Product Admin', titles)

    def test_admin_list_forbidden_for_non_admin(self):
        # non-admin should not be allowed to access admin product list
        resp = self.client.get('/api/admin/products/list/', HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        self.assertIn(resp.status_code, (401, 403))

    def test_create_product_validation(self):
        # Missing price should fail
        payload = {
            'title': 'Bad Prod',
            'stock': 5,
        }
        resp = self.client.post('/api/products/create/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
