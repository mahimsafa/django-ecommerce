from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from store.models import Store as StoreModel
from django.contrib.auth import get_user_model

User = get_user_model()


class Tenant(models.Model):
    """
    Represents a tenant (user account) in the multi-tenant system.
    Each tenant can own multiple stores.
    """
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant",
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Represents a customer's order in the system.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    store = models.ForeignKey(
        StoreModel,
        on_delete=models.PROTECT,
        related_name='orders',
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-placed_at']

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Ensure total is always calculated from subtotal, tax, and discount
        self.total = self.subtotal + self.tax_total - self.discount_total
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Represents an individual item within an order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    variant = models.ForeignKey(
        'order.OrderProductVariant',
        on_delete=models.PROTECT,
        related_name='order_items',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('order', 'variant')

    def __str__(self):
        return f"{self.quantity}x {self.variant} in Order #{self.order_id}"

    @property
    def line_total(self):
        return (self.unit_price * self.quantity) + self.tax_amount - self.discount_amount


class StoreStaff(models.Model):
    """
    Through model linking users to stores with specific roles.
    """
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("staff", "Staff Member"),
    ]

    store = models.ForeignKey(
        StoreModel,
        on_delete=models.CASCADE,
        related_name="staff_links",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store_links",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="invitations_sent",
        null=True,
        blank=True,
    )
    invited_at = models.DateTimeField(default=timezone.now)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("store", "user")

    def __str__(self):
        return f"{self.user} as {self.role} in {self.store}"


class OrderProduct(models.Model):
    """
    Order-specific product information within a store. 
    On creation, a default variant is generated.
    """
    store = models.ForeignKey(
        StoreModel,
        on_delete=models.CASCADE,
        related_name="order_products",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Generate a default variant on creation
        if is_new:
            OrderProductVariant.objects.create(
                product=self,
                name=f"{self.name} - Default",
                sku=f"{self.sku}-DEFAULT",
            )

    def __str__(self):
        return self.name


class OrderProductVariant(models.Model):
    """
    Variants of an order product (e.g., size/color). 
    Each variant gets its own price and optional image.
    """
    product = models.ForeignKey(
        OrderProduct,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class OrderProductPrice(models.Model):
    """
    Stores pricing information for each order product variant.
    """
    variant = models.OneToOneField(
        'order.OrderProductVariant',
        on_delete=models.CASCADE,
        related_name="price",
    )
    currency = models.CharField(max_length=10, default="USD")
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.variant} : {self.amount} {self.currency}"


class OrderProductImage(models.Model):
    """
    Images for order products or variants. A product can have multiple images, but a variant only one.
    """
    product = models.ForeignKey(
        'order.OrderProduct',
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
    )
    variant = models.OneToOneField(
        'order.OrderProductVariant',
        on_delete=models.CASCADE,
        related_name="image",
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="order_product_images/")
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        # Ensure that either product or variant is set, not both
        if bool(self.product) == bool(self.variant):
            raise ValidationError(
                "Image must be attached to either a product or a variant, exclusively."
            )

    def __str__(self):
        target = self.variant or self.product
        return f"Image for {target}"
