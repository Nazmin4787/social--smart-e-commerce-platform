import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare_backend.settings')
django.setup()

from api.models import AppUser

# Create demo users if they don't exist
demo_users = [
    {
        'name': 'Demo User',
        'email': 'demo@example.com',
        'password': 'demo123',
        'bio': 'Skincare enthusiast and beauty blogger',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Sarah Johnson',
        'email': 'sarah@example.com',
        'password': 'demo123',
        'bio': 'Natural beauty advocate | Sensitive skin expert',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Emily Chen',
        'email': 'emily@example.com',
        'password': 'demo123',
        'bio': 'K-beauty lover | Sharing my skincare journey',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Jessica Williams',
        'email': 'jessica@example.com',
        'password': 'demo123',
        'bio': 'Acne warrior | Finding the best products for you',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Maya Patel',
        'email': 'maya@example.com',
        'password': 'demo123',
        'bio': 'Clean beauty enthusiast | Eco-friendly skincare',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Rachel Green',
        'email': 'rachel@example.com',
        'password': 'demo123',
        'bio': 'Makeup artist | Skincare first approach',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Lisa Martinez',
        'email': 'lisa@example.com',
        'password': 'demo123',
        'bio': 'Anti-aging specialist | Retinol advocate',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'name': 'Amanda Brown',
        'email': 'amanda@example.com',
        'password': 'demo123',
        'bio': 'Hydration queen | Glass skin achiever',
        'is_staff': False,
        'is_superuser': False
    },
]

for user_data in demo_users:
    email = user_data['email']
    # Check if user already exists
    if not AppUser.objects.filter(email=email).exists():
        user = AppUser.objects.create(
            name=user_data['name'],
            email=email,
            bio=user_data['bio'],
            is_staff=user_data['is_staff'],
            is_superuser=user_data['is_superuser']
        )
        user.set_password(user_data['password'])
        user.save()
        print(f'Created user: {user.name} ({user.email})')
    else:
        print(f'User already exists: {email}')

print(f'\nTotal non-admin users in database: {AppUser.objects.filter(is_staff=False, is_superuser=False).count()}')
