import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Product


class Command(BaseCommand):
    help = "Remove all Product records and associated product media files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm deletion without interactive prompt",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without making changes",
        )

    def handle(self, *args, **options):
        yes = options.get("yes")
        dry_run = options.get("dry_run")

        total = Product.objects.count()
        products_dir = os.path.join(settings.MEDIA_ROOT, "products")

        self.stdout.write(f"Products to remove: {total}")
        self.stdout.write(f"Product media directory: {products_dir}")

        if dry_run:
            self.stdout.write("Dry run: no changes will be made.")
            if os.path.exists(products_dir):
                for root, dirs, files in os.walk(products_dir):
                    for f in files:
                        self.stdout.write(os.path.join(root, f))
            return

        if not yes:
            confirm = input("Type 'DELETE' to confirm removing all products and their media files: ")
            if confirm != "DELETE":
                self.stdout.write(self.style.ERROR("Aborted by user."))
                return

        # Attempt to remove product media files first
        files_removed = 0
        try:
            if os.path.exists(products_dir):
                shutil.rmtree(products_dir)
                files_removed = 1
                self.stdout.write(self.style.SUCCESS(f"Removed product media directory: {products_dir}"))
            else:
                self.stdout.write("No product media directory found; skipping file removal.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to remove media files: {e}"))
            self.stdout.write(self.style.ERROR("Aborting to avoid partial data loss."))
            return

        # Delete products in the database
        try:
            with transaction.atomic():
                deleted_count, _ = Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} product-related rows."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to delete products from database: {e}"))
            # Note: media files may have been removed already
