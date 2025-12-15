import os
import django
from dotenv import load_dotenv
from datetime import date

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import Product

Product.objects.all().delete()
products = [
    {
        'title': 'Hydrating Face Serum', 
        'description': 'Lightweight hyaluronic acid serum that deeply hydrates and plumps your skin for a dewy, youthful glow', 
        'price': 7.99, 
        'stock': 120, 
        'category': 'Serums',
        'manufacturing_date': date(2024, 1, 15),
        'expiry_date': date(2026, 1, 15),
        'images': [
            'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'Vitamin C Brightening Cream', 
        'description': 'Brightens and evens skin tone with powerful antioxidants for radiant, luminous skin', 
        'price': 9.99, 
        'stock': 80, 
        'category': 'Moisturizers',
        'manufacturing_date': date(2024, 2, 10),
        'expiry_date': date(2026, 2, 10),
        'images': [
            'https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1556229010-aa8d0e0ca0d8?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'Gentle Cleanser', 
        'description': 'Daily gentle face wash that removes impurities without stripping natural oils, perfect for all skin types', 
        'price': 4.99, 
        'stock': 200, 
        'category': 'Cleansers',
        'manufacturing_date': date(2024, 3, 5),
        'expiry_date': date(2027, 3, 5),
        'images': [
            'https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1556228994-230e546d4c74?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'SPF 50 Glow Sunscreen', 
        'description': 'Broad spectrum protection with a dewy finish. Protects against UVA/UVB rays while giving skin a natural glow', 
        'price': 12.99, 
        'stock': 150, 
        'category': 'Sunscreens',
        'manufacturing_date': date(2024, 4, 20),
        'expiry_date': date(2026, 4, 20),
        'images': [
            'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1556228994-230e546d4c74?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'Niacinamide Serum', 
        'description': '10% Niacinamide + Zinc formula reduces pores, controls oil, and improves skin texture', 
        'price': 8.99, 
        'stock': 95, 
        'category': 'Serums',
        'manufacturing_date': date(2024, 5, 12),
        'expiry_date': date(2026, 5, 12),
        'images': [
            'https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'Retinol Night Cream', 
        'description': 'Anti-aging night cream with retinol to reduce fine lines, wrinkles, and improve skin elasticity', 
        'price': 14.99, 
        'stock': 70, 
        'category': 'Moisturizers',
        'manufacturing_date': date(2024, 6, 8),
        'expiry_date': date(2026, 6, 8),
        'images': [
            'https://images.unsplash.com/photo-1570554886111-e80fcca6a029?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'Clay Face Mask', 
        'description': 'Detoxifying clay mask that draws out impurities, minimizes pores, and leaves skin refreshed', 
        'price': 6.99, 
        'stock': 110, 
        'category': 'Face Masks',
        'manufacturing_date': date(2024, 7, 25),
        'expiry_date': date(2026, 7, 25),
        'images': [
            'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1556228994-230e546d4c74?w=500&h=500&fit=crop'
        ]
    },
    {
        'title': 'Hyaluronic Acid Moisturizer', 
        'description': 'Intense hydration cream with hyaluronic acid for plump, supple, and healthy-looking skin', 
        'price': 11.99, 
        'stock': 88, 
        'category': 'Moisturizers',
        'manufacturing_date': date(2024, 8, 18),
        'expiry_date': date(2026, 8, 18),
        'images': [
            'https://images.unsplash.com/photo-1556229010-aa8d0e0ca0d8?w=500&h=500&fit=crop',
            'https://images.unsplash.com/photo-1570554886111-e80fcca6a029?w=500&h=500&fit=crop'
        ]
    },
]

for p in products:
    Product.objects.create(
        title=p['title'],
        description=p['description'],
        price=p['price'],
        stock=p['stock'],
        category=p['category'],
        manufacturing_date=p.get('manufacturing_date'),
        expiry_date=p.get('expiry_date'),
        images=p['images']
    )

print('Seeded products with expiry dates')
