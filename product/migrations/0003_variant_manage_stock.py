# Generated by Django 5.1.4 on 2025-07-13 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_variant_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='variant',
            name='manage_stock',
            field=models.BooleanField(default=True),
        ),
    ]
