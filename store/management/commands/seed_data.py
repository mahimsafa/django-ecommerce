"""
Django Management Command: Seed Database with Sample Data

This command populates the database with initial data for development and testing purposes.
It creates:
- A superuser (if none exists)
- Sample categories
- Two stores (Tech Haven and Fashion Forward)
- 12 products per store with variants and pricing

Usage:
    python manage.py seed_data

Requirements:
    - Faker package (pip install Faker)
    - All required Django apps must be in INSTALLED_APPS

Note: This command is idempotent - it can be run multiple times without creating duplicates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Store, Config, Settings
from product.models import Category, Product, Variant
from faker import Faker
from decimal import Decimal
from django.utils.text import slugify

User = get_user_model()

class Command(BaseCommand):
    """
    Management command to seed the database with initial data.
    
    This command performs the following actions:
    1. Creates a superuser if none exists
    2. Creates or uses existing categories
    3. Creates two stores (Tech Haven and Fashion Forward)
    4. Populates each store with 12 sample products
    5. Creates variants and pricing for each product
    
    The command is safe to run multiple times as it checks for existing data
    before creating new entries.
    """
    help = 'Seed database with sample data for stores, categories, and products'

    def handle(self, *args, **options):
        """
        Entry point for the management command.
        
        Args:
            *args: Variable length argument list
            **options: Arbitrary keyword arguments
            
        Returns:
            None
        """
        self.stdout.write('Seeding data...')
        
        # Create superuser if not exists
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating superuser...')
            user = User.objects.create_superuser(
                username='admin',
                email='admin@mahimsafa.com',
                password='admin',
                first_name='Store',
                last_name='Admin'
            )
        else:
            user = User.objects.filter(is_superuser=True).first()
            self.stdout.write('Using existing superuser...')

        # Create categories
        categories = [
            'Electronics', 'Clothing', 'Home & Kitchen', 
            'Books', 'Beauty & Personal Care'
        ]
        
        self.stdout.write('Creating categories...')
        category_objs = []
        for cat_name in categories:
            slug = slugify(cat_name)
            try:
                category = Category.objects.get(slug=slug)
                self.stdout.write(f'Using existing category: {category.name}')
            except Category.DoesNotExist:
                category = Category.objects.create(
                    name=cat_name,
                    slug=slug,
                    is_active=True
                )
                self.stdout.write(f'Created category: {category.name}')
            category_objs.append(category)

        # Create stores
        stores_data = [
            {
                'name': 'Tech Haven',
                'description': 'Your one-stop shop for all things tech',
                'tagline': 'Technology at your fingertips'
            },
            {
                'name': 'Fashion Forward',
                'description': 'Trendy clothing and accessories',
                'tagline': 'Wear the latest trends'
            }
        ]

        self.stdout.write('Creating stores...')
        store_objs = []
        for store_data in stores_data:
            store = Store.objects.create(
                name=store_data['name'],
                description=store_data['description'],
                tagline=store_data['tagline'],
                owner=user
            )
            
            # Create store config and settings
            Config.objects.create(store=store)
            Settings.objects.create(store=store)
            
            store_objs.append(store)
            self.stdout.write(f'Created store: {store.name}')

        # Sample product data
        tech_products = [
            {'name': 'Wireless Earbuds', 'price': 99.99, 'sale_price': 79.99},
            {'name': 'Smartphone', 'price': 699.99, 'sale_price': 649.99},
            {'name': 'Laptop', 'price': 999.99, 'sale_price': 899.99},
            {'name': 'Smart Watch', 'price': 199.99, 'sale_price': 179.99},
            {'name': 'Wireless Charger', 'price': 29.99, 'sale_price': None},
            {'name': 'Bluetooth Speaker', 'price': 129.99, 'sale_price': 99.99},
            {'name': 'Tablet', 'price': 349.99, 'sale_price': 299.99},
            {'name': 'Gaming Mouse', 'price': 59.99, 'sale_price': 49.99},
            {'name': 'Mechanical Keyboard', 'price': 129.99, 'sale_price': 109.99},
            {'name': 'External SSD', 'price': 149.99, 'sale_price': 129.99},
            {'name': 'Noise Cancelling Headphones', 'price': 299.99, 'sale_price': 249.99},
            {'name': 'Action Camera', 'price': 199.99, 'sale_price': 179.99}
        ]

        fashion_products = [
            {'name': 'Denim Jacket', 'price': 59.99, 'sale_price': 49.99},
            {'name': 'Summer Dress', 'price': 39.99, 'sale_price': 34.99},
            {'name': 'Sneakers', 'price': 89.99, 'sale_price': 79.99},
            {'name': 'Leather Wallet', 'price': 29.99, 'sale_price': 24.99},
            {'name': 'Sunglasses', 'price': 49.99, 'sale_price': 39.99},
            {'name': 'Wristwatch', 'price': 129.99, 'sale_price': 99.99},
            {'name': 'Backpack', 'price': 59.99, 'sale_price': 49.99},
            {'name': 'T-Shirt Pack', 'price': 34.99, 'sale_price': 29.99},
            {'name': 'Formal Shirt', 'price': 44.99, 'sale_price': 39.99},
            {'name': 'Running Shorts', 'price': 29.99, 'sale_price': 24.99},
            {'name': 'Winter Coat', 'price': 129.99, 'sale_price': 109.99},
            {'name': 'Leather Belt', 'price': 24.99, 'sale_price': 19.99}
        ]

        # Create products for each store
        self.stdout.write('Creating products...')
        
        # Tech Haven store (index 0)
        self.create_products_for_store(
            store_objs[0], 
            tech_products, 
            category_objs[0],  # Electronics
            user
        )
        
        # Fashion Forward store (index 1)
        self.create_products_for_store(
            store_objs[1], 
            fashion_products, 
            category_objs[1],  # Clothing
            user
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))
    
    def create_products_for_store(self, store, products, category, user):
        fake = Faker()
        
        for product_data in products:
            # Create product
            product = Product.objects.create(
                store=store,
                category=category,
                name=product_data['name'],
                description=fake.paragraph(nb_sentences=5),
                status='published'
            )
            
            # Create default variant
            variant = Variant.objects.create(
                product=product,
                name='Default',
                sku=f"{store.name[:3].upper()}-{product.id}-001",
                default_price=Decimal(str(product_data['price'])),
                sale_price=Decimal(str(product_data['sale_price'])) if product_data['sale_price'] else None,
                is_on_sale=product_data['sale_price'] is not None,
                currency='USD'
            )
            
            self.stdout.write(f'Created product: {product.name} for {store.name}')
            
        self.stdout.write(f'Created {len(products)} products for {store.name}')
