# Generated migration for allergies and ingredients

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_review_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='allergies',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='product',
            name='ingredients',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
