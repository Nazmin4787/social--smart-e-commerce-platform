import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import Product

Product.objects.all().delete()
products = [
    {
        'title': 'Hydrating Face Serum', 
        'description': 'Lightweight hyaluronic serum that deeply hydrates and plumps skin', 
        'price': 7.99, 
        'stock': 120, 
        'images': ['https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop'],
        'category': 'GENERAL'
    },
    {
        'title': 'Vitamin C Brightening Cream', 
        'description': 'Brightens and evens skin tone with powerful vitamin C', 
        'price': 9.99, 
        'stock': 80, 
        'images': ['https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400&h=400&fit=crop'],
        'category': 'GENERAL'
    },
    {
        'title': 'Gentle Cleanser', 
        'description': 'Daily gentle face wash for all skin types', 
        'price': 4.99, 
        'stock': 200, 
        'images': ['https://images.unsplash.com/photo-1571875257727-256c39da42af?w=400&h=400&fit=crop'],
        'category': 'CLEANSERS'
    },
    {
        'title': 'Test Product', 
        'description': 'A premium skincare product for testing', 
        'price': 15.99, 
        'stock': 50, 
        'images': ['https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=400&h=400&fit=crop'],
        'category': 'SKINCARE'
    },
    {
        'title': 'Vitamin C Cream', 
        'description': 'Rich moisturizing cream with vitamin C for radiant skin', 
        'price': 12.99, 
        'stock': 100, 
        'images': ['https://images.unsplash.com/photo-1570554886111-e80fcca6a029?w=400&h=400&fit=crop'],
        'category': 'MOISTURIZERS'
    },
    {
        'title': 'Retinol Night Cream', 
        'description': 'Anti-aging night cream with retinol for smooth, youthful skin', 
        'price': 18.99, 
        'stock': 75, 
        'images': ['https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=400&h=400&fit=crop'],
        'category': 'MOISTURIZERS'
    },
    {
        'title': 'Niacinamide Serum', 
        'description': 'Pore-refining serum that minimizes appearance of pores', 
        'price': 14.99, 
        'stock': 90, 
        'images': ['https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=400&h=400&fit=crop'],
        'category': 'SERUMS'
    },
    {
        'title': 'SPF 50 Sunscreen', 
        'description': 'Broad spectrum sun protection for daily use', 
        'price': 16.99, 
        'stock': 150, 
        'images': ['https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=400&h=400&fit=crop'],
        'category': 'SUNSCREEN'
    },
]

for p in products:
    Product.objects.create(
        title=p['title'],
        description=p['description'],
        price=p['price'],
        stock=p['stock'],
        images=p['images'],
        category=p['category'],
    )

print('Seeded products')
