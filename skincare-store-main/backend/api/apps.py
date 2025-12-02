from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Seed a demo product so frontend demo auto-add always has a product.
        # Guard with try/except to avoid issues during migrations.
        try:
            from django.db.utils import OperationalError, ProgrammingError
            from .models import Product

            # Only run when DB tables are ready
            try:
                if Product.objects.exists():
                    return
            except (OperationalError, ProgrammingError):
                # Database tables not created yet (migrations pending)
                return

            demo_title = 'Demo Skincare Product'
            demo_desc = 'This is a demo product created automatically for development and testing.'
            demo_images = [
                'https://via.placeholder.com/400x400.png?text=Demo+Product'
            ]

            Product.objects.get_or_create(
                title=demo_title,
                defaults={
                    'description': demo_desc,
                    'price': 9.99,
                    'stock': 50,
                    'images': demo_images,
                    'category': 'demo',
                }
            )
        except Exception:
            # Fail silently — we don't want to block app startup for non-critical seeding errors
            pass
