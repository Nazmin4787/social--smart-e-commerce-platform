import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import Product

# Mark the first 3 products as trending
products = Product.objects.all()[:3]
for product in products:
    product.is_trending = True
    product.save()
    print(f"Marked '{product.title}' as trending")

print(f"\nTotal trending products: {Product.objects.filter(is_trending=True).count()}")
