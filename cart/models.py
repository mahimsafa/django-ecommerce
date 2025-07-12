from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from store.models import Store
from product.models import Variant


class Cart(models.Model):
    """
    A shopping cart for a user scoped to a specific store.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='carts',
        on_delete=models.CASCADE
    )
    store = models.ForeignKey(
        Store,
        related_name='carts',
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(
        default=True,
        help_text='If false, this cart is archived after checkout or cancellation.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'store', 'is_active')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Cart {self.pk} for {self.user.username} @ {self.store.name}"

    def get_total(self):
        """
        Calculate total cost of all items in the cart.
        """
        return sum(item.get_subtotal() for item in self.items.all())


class CartItem(models.Model):
    """
    An item in a shopping cart, linking a Variant with quantity and snapshot of price.
    """
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        Variant,
        related_name='cart_items',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text='Number of units of this variant in the cart.'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Snapshot of variant price when added to cart.'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'variant')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity} × {self.variant} in cart {self.cart.pk}"

    def get_subtotal(self):
        """
        Returns price × quantity for this item.
        """
        return self.unit_price * self.quantity
