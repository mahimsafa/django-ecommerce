from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from store.models import Store
from product.models import Variant


class CartManager(models.Manager):
    def get_or_create_cart(self, request, store):
        """Get or create a cart for the current session/user."""
        if request.user.is_authenticated:
            # For authenticated users, get or create cart for the user
            cart, created = self.get_or_create(
                user=request.user,
                store=store,
                is_active=True,
                session_key=None  # Clear session key if user logs in
            )
        else:
            # For anonymous users, use session key
            if not request.session.session_key:
                request.session.create()
            
            session_key = request.session.session_key
            
            # Try to get existing cart for this session
            cart = self.filter(
                session_key=session_key,
                store=store,
                is_active=True
            ).first()
            
            if not cart:
                # Create new cart for this session
                cart = self.create(
                    user=None,
                    store=store,
                    session_key=session_key,
                    is_active=True
                )
        
        return cart

class Cart(models.Model):
    """
    A shopping cart for a user or guest session, scoped to a specific store.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='carts',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text='Session key for guest users',
        db_index=True
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
    
    objects = CartManager()

    class Meta:
        unique_together = ('user', 'store', 'is_active')
        ordering = ['-updated_at']

    def __str__(self):
        user_display = f"user {self.user.username}" if self.user else "guest user"
        return f"Cart {self.pk} for {user_display} @ {self.store.name if self.store else 'No Store'}"

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
