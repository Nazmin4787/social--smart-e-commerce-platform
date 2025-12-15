import os
import shutil
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings

from api.models import Product


class RemoveAllProductsCommandTest(TestCase):

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_remove_all_products_deletes_rows_and_files(self):
        media_root = os.environ.get('DJANGO_MEDIA_ROOT')
        # Use the overridden MEDIA_ROOT from settings via django.test.override_settings
        from django.conf import settings
        products_dir = os.path.join(settings.MEDIA_ROOT, "products")
        os.makedirs(products_dir, exist_ok=True)

        # create dummy files
        open(os.path.join(products_dir, "img1.jpg"), "w").close()
        open(os.path.join(products_dir, "img2.jpg"), "w").close()

        # create two products
        p1 = Product.objects.create(title="A", price=10, stock=1)
        p2 = Product.objects.create(title="B", price=20, stock=2)

        # Ensure setup is correct
        self.assertTrue(os.path.exists(products_dir))
        self.assertEqual(Product.objects.count(), 2)

        # Run command
        call_command("remove_all_products", "--yes")

        # Assertions
        self.assertEqual(Product.objects.count(), 0)
        self.assertFalse(os.path.exists(products_dir))
