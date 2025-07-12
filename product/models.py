from django.db import models
from store.models import Store
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.


class Category(MPTTModel):
    """
    Hierarchical category model that can have parent and children categories.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product within a store.
    """
    store = models.ForeignKey(Store, related_name='products', on_delete=models.CASCADE)
    category = TreeForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[
            ('published', 'Published'), 
            ('draft', 'Draft'), 
            ('inactive', 'Inactive')
        ], 
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        # This will be called during model validation
        if not self.pk:  # New instance
            return
            
        # if not self.variants.exists():
        #     raise ValidationError('A product must have at least one variant.')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Variant(models.Model):
    """
    Product variant. Default variant created after product is saved.
    """
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    # Price fields
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(default='bdt', max_length=3)
    is_on_sale = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.name}"




class Image(models.Model):
    """
    Images attached to either products or variants.
    One variant can have only one image; products can have multiple.
    """
    product = models.ForeignKey(Product, related_name='images', null=True, blank=True, on_delete=models.CASCADE)
    variant = models.OneToOneField(Variant, related_name='image', null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images')
    alt_text = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        target = self.variant if self.variant else self.product
        return f"Image for {target}"