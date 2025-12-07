from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Cart


class Command(BaseCommand):
    help = 'Clear expired carts (carts inactive for more than CART_EXPIRATION_DAYS)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleared without actually clearing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all carts
        all_carts = Cart.objects.all()
        expired_count = 0
        cleared_items_count = 0
        
        for cart in all_carts:
            if cart.is_expired():
                items_count = cart.items.count()
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Would clear cart {cart.id} for user {cart.user.email} '
                            f'({items_count} items, last updated: {cart.updated_at})'
                        )
                    )
                else:
                    cart.items.all().delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Cleared cart {cart.id} for user {cart.user.email} '
                            f'({items_count} items removed)'
                        )
                    )
                
                expired_count += 1
                cleared_items_count += items_count
        
        if expired_count == 0:
            self.stdout.write(self.style.SUCCESS('No expired carts found.'))
        else:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n[DRY RUN] Would clear {expired_count} cart(s) '
                        f'with {cleared_items_count} total items.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully cleared {expired_count} expired cart(s) '
                        f'with {cleared_items_count} total items.'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCart expiration period: {Cart.CART_EXPIRATION_DAYS} days'
            )
        )
