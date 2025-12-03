# Create Admin User Script

Run this in Django shell or create a management command:

```python
# Method 1: Django Shell
python manage.py shell

from api.models import AppUser

# Create admin user
admin = AppUser.objects.create(
    name="Admin User",
    email="admin@example.com",
    is_staff=True,
    is_superuser=True
)
admin.set_password("admin123")
admin.save()

print(f"Admin user created: {admin.email}")
```

```python
# Method 2: Create management command
# File: backend/api/management/commands/createadmin.py

from django.core.management.base import BaseCommand
from api.models import AppUser

class Command(BaseCommand):
    help = 'Creates an admin user'

    def handle(self, *args, **kwargs):
        email = "admin@example.com"
        
        if AppUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return
        
        admin = AppUser.objects.create(
            name="Admin User",
            email=email,
            is_staff=True,
            is_superuser=True
        )
        admin.set_password("admin123")
        admin.save()
        
        self.stdout.write(self.style.SUCCESS(f'Admin user created: {email}'))
        self.stdout.write(self.style.SUCCESS('Password: admin123'))
```

Then run:
```bash
python manage.py createadmin
```

## Login Credentials
- **Email:** admin@example.com
- **Password:** admin123

After login, the Admin button will appear in the header next to the user icon.
