from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from store.models import Store as StoreModel
from django.contrib.auth import get_user_model

User = get_user_model()


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
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the order was cancelled"
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_orders',
        help_text="User who cancelled the order"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Tax amount for the order'
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Shipping cost for the order'
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
    shipping_address = models.ForeignKey(
        'customer.Address',
        on_delete=models.PROTECT,
        related_name='shipping_orders',
        null=True,
        blank=True
    )
    billing_address = models.ForeignKey(
        'customer.Address',
        on_delete=models.PROTECT,
        related_name='billing_orders',
        null=True,
        blank=True
    )
    payment_method = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Payment method used for this order'
    )
    payment_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ]
    )
    notes = models.TextField(blank=True, help_text='Additional notes for the order')
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-placed_at']

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Ensure total is always calculated from subtotal, tax, shipping, and discount
        self.total = self.subtotal + self.tax + self.shipping_cost - self.discount_total
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('order:order_detail', args=[str(self.id)])
    
    def update_totals(self):
        """
        Update the order's subtotal and total based on its items.
        """
        # Calculate subtotal by summing up all line totals
        self.subtotal = sum(
            item.unit_price * item.quantity 
            for item in self.items.all()
        )
        
        # Calculate total including tax, shipping, and discounts
        self.total = (
            self.subtotal + 
            (self.tax or 0) + 
            (self.shipping_cost or 0) - 
            (self.discount_total or 0)
        )
        self.save(update_fields=['subtotal', 'total'])
        
    def can_cancel(self):
        """
        Check if the order can be cancelled.
        Orders can only be cancelled if they are in 'pending' or 'processing' status.
        """
        return self.status in ['pending', 'processing']
    
    def cancel(self, user=None):
        """
        Cancel the order if possible.
        Returns (success, message) tuple.
        """
        if not self.can_cancel():
            return False, "This order cannot be cancelled."
            
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if user:
            self.cancelled_by = user
        self.save(update_fields=['status', 'cancelled_at', 'cancelled_by'])
        
        # Restore product stock if needed
        for item in self.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save(update_fields=['stock'])
        
        return True, "Order has been cancelled successfully."
    
    def mark_as_paid(self, payment_method=None):
        """Mark the order as paid."""
        if payment_method:
            self.payment_method = payment_method
        self.payment_status = 'paid'
        if self.status == 'pending':
            self.status = 'processing'
        self.save()
    
    def get_items_by_store(self):
        """Group order items by store."""
        from collections import defaultdict
        items_by_store = defaultdict(list)
        
        for item in self.items.all():
            store = item.variant.product.store
            items_by_store[store].append(item)
            
        return dict(items_by_store)


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
        ordering = ['id']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity}x {self.variant} (Order #{self.order_id})"
    
    @property
    def line_total(self):
        """
        Calculate the total price for this line item (quantity * unit_price).
        """
        return (self.unit_price * self.quantity) + self.tax_amount - self.discount_amount
    
    def save(self, *args, **kwargs):
        """
        Override save to update order totals when an item is saved.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        # Update order totals if this is a new item or quantity/price changed
        if is_new or self.order.items.count() == 1:
            self.order.update_totals()
    
    def delete(self, *args, **kwargs):
        """
        Override delete to update order totals when an item is removed.
        """
        order = self.order
        super().delete(*args, **kwargs)
        order.update_totals()


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
