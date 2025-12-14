from django.core.management.base import BaseCommand
from api.models import AppUser

class Command(BaseCommand):
    help = 'Creates an admin user for Novacell'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='admin@example.com', help='Admin email')
        parser.add_argument('--password', type=str, default='admin123', help='Admin password')
        parser.add_argument('--name', type=str, default='Admin User', help='Admin name')

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        password = kwargs['password']
        name = kwargs['name']
        
        if AppUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists'))
            user = AppUser.objects.get(email=email)
            if not user.is_staff:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated {email} to admin'))
            return
        
        admin = AppUser.objects.create(
            name=name,
            email=email,
            is_staff=True,
            is_superuser=True
        )
        admin.set_password(password)
        admin.save()
        
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Admin user created successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.WARNING('Please login with these credentials to access the admin panel at /admin'))
