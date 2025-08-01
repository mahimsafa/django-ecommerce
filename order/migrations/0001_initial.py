# Generated by Django 5.1.4 on 2025-07-13 14:59

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer', '0001_initial'),
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_email', models.EmailField(help_text='Customer email address for order notifications', max_length=254)),
                ('customer_phone', models.CharField(blank=True, help_text='Customer phone number for order updates', max_length=20, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('cancelled_at', models.DateTimeField(blank=True, help_text='When the order was cancelled', null=True)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('tax', models.DecimalField(decimal_places=2, default=0, help_text='Tax amount for the order', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, help_text='Shipping cost for the order', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('discount_total', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('payment_method', models.CharField(blank=True, help_text='Payment method used for this order', max_length=50, null=True)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True, help_text='Additional notes for the order')),
                ('placed_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('billing_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='billing_orders', to='customer.address')),
                ('cancelled_by', models.ForeignKey(blank=True, help_text='User who cancelled the order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cancelled_orders', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(blank=True, help_text='User who placed the order (null for guest checkouts)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to=settings.AUTH_USER_MODEL)),
                ('shipping_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='shipping_orders', to='customer.address')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='store.store')),
            ],
            options={
                'ordering': ['-placed_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_products', to='store.store')),
            ],
        ),
        migrations.CreateModel(
            name='OrderProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='order.orderproduct')),
            ],
        ),
        migrations.CreateModel(
            name='OrderProductPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('variant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='price', to='order.orderproductvariant')),
            ],
        ),
        migrations.CreateModel(
            name='OrderProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='order_product_images/')),
                ('alt_text', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='order.orderproduct')),
                ('variant', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='image', to='order.orderproductvariant')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='order.order')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='order.orderproductvariant')),
            ],
            options={
                'verbose_name': 'Order Item',
                'verbose_name_plural': 'Order Items',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='StoreStaff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Administrator'), ('staff', 'Staff Member')], default='staff', max_length=20)),
                ('invited_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('accepted', models.BooleanField(default=False)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitations_sent', to=settings.AUTH_USER_MODEL)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_links', to='store.store')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_links', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('store', 'user')},
            },
        ),
    ]
