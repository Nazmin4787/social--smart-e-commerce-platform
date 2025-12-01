import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import Product

Product.objects.all().delete()
products = [
    {'title': 'Hydrating Face Serum', 'description': 'Lightweight hyaluronic serum', 'price': 7.99, 'stock': 120, 'images': ['https://via.placeholder.com/400']},
    {'title': 'Vitamin C Brightening Cream', 'description': 'Brightens and evens skin tone', 'price': 9.99, 'stock': 80, 'images': ['https://via.placeholder.com/400']},
    {'title': 'Gentle Cleanser', 'description': 'Daily gentle face wash', 'price': 4.99, 'stock': 200, 'images': ['https://via.placeholder.com/400']},
]

for p in products:
    Product.objects.create(
        title=p['title'],
        description=p['description'],
        price=p['price'],
        stock=p['stock'],
        images=p['images'],
    )

print('Seeded products')
