import io
import json
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import AppUser, Banner
from django.conf import settings
import os

@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
class BannerAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a regular user
        self.user = AppUser.objects.create(name='User', email='user@example.com')
        self.user.set_password('password')
        self.user.save()

        # Create an admin user (is_staff=True)
        self.admin = AppUser.objects.create(name='Admin', email='admin@example.com', is_staff=True)
        self.admin.set_password('adminpass')
        self.admin.save()

        # Create tokens using the project's utils (import lazily to avoid circular import on test discovery)
        from api.utils import create_jwt
        self.user_token = create_jwt({'user_id': self.user.id, 'email': self.user.email})
        self.admin_token = create_jwt({'user_id': self.admin.id, 'email': self.admin.email})

    def tearDown(self):
        # cleanup any uploaded files
        media_root = os.path.join(settings.BASE_DIR, 'test_media')
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except Exception:
                        pass

    def test_public_get_banners_empty(self):
        resp = self.client.get('/api/banners/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_admin_create_banner_json_no_image(self):
        payload = {
            'title': 'Test Banner',
            'link': 'https://example.com',
            'position': 1,
            'is_active': True
        }
        resp = self.client.post('/api/admin/banners/', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertIn('banner', data)
        banner = Banner.objects.get(pk=data['banner']['id'])
        self.assertEqual(banner.title, 'Test Banner')
        self.assertTrue(banner.is_active)

    def test_admin_create_banner_multipart_with_image(self):
        image_content = io.BytesIO(b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B")
        image_file = SimpleUploadedFile('test.gif', image_content.getvalue(), content_type='image/gif')
        resp = self.client.post('/api/admin/banners/', {'title': 'WithImage', 'position': 2, 'is_active': 'true', 'image': image_file}, HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertIn('banner', data)
        banner = Banner.objects.get(pk=data['banner']['id'])
        self.assertIsNotNone(banner.image)

    def test_admin_update_banner(self):
        b = Banner.objects.create(title='Old', position=5, is_active=True)
        payload = {'id': b.id, 'title': 'Updated', 'position': 10, 'is_active': False}
        resp = self.client.put('/api/admin/banners/', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.title, 'Updated')
        self.assertEqual(b.position, 10)
        self.assertFalse(b.is_active)

    def test_admin_delete_banner(self):
        b = Banner.objects.create(title='ToDelete')
        payload = {'id': b.id}
        resp = self.client.delete('/api/admin/banners/', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Banner.objects.filter(pk=b.id).exists())

    def test_non_admin_cannot_manage(self):
        payload = {'title': 'X'}
        resp = self.client.post('/api/admin/banners/', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        self.assertIn(resp.status_code, (401, 403))

    def test_public_get_only_active(self):
        Banner.objects.create(title='A', is_active=True, position=1)
        Banner.objects.create(title='B', is_active=False, position=2)
        resp = self.client.get('/api/banners/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        titles = [b['title'] for b in data]
        self.assertIn('A', titles)
        self.assertNotIn('B', titles)
