from django.db import models
from django.conf import settings
from store.models import Store
from customer.models import Customer
from product.models import Variant

# Create your models here.




class Order(models.Model):
    """
    Represents a customer's order for a specific store (multi-tenant aware).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    store = models.ForeignKey(
        Store,
        related_name='orders',
        on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        Customer,
        related_name='orders',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    # Snapshot of totals at the time of order
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-placed_at']

    def __str__(self):
        return f"Order {self.pk} ({self.get_status_display()}) for {self.customer}"

    def recalculate_totals(self):
        """
        Recompute subtotal, tax_total, discount_total and total from items.
        """
        items = self.items.all()
        self.subtotal = sum(item.get_line_total() for item in items)
        # Placeholder: implement tax and discount logic as needed
        # self.tax_total = ...
        # self.discount_total = ...
        self.total = self.subtotal + self.tax_total - self.discount_total
        self.save()


class OrderItem(models.Model):
    """
    An item within an Order, mapping a Variant to quantity and price snapshot.
    """
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        Variant,
        related_name='order_items',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('order', 'variant')

    def __str__(self):
        return f"{self.quantity}×{self.variant} in Order {self.order.pk}"

    def get_line_total(self):
        """
        Returns (unit_price + tax_amount - discount_amount) × quantity.
        """
        unit_net = self.unit_price + self.tax_amount - self.discount_amount
        return unit_net * self.quantity
