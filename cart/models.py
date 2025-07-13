from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from store.models import Store
from product.models import Variant


class CartManager(models.Manager):
    def get_or_create_cart(self, request):
        """
        Get or create a cart for the current session/user.
        Now handles items from multiple stores in a single cart.
        """
        if not request.session.session_key:
            request.session.save()
            
        session_key = request.session.session_key
        
        if request.user.is_authenticated:
            # For authenticated users, get their active cart
            cart = self.filter(
                user=request.user,
                is_active=True
            ).first()
            
            # If no active cart, check for a session cart to merge
            if not cart:
                session_cart = self.filter(
                    session_key=session_key,
                    is_active=True
                ).first()
                
                if session_cart:
                    # Convert session cart to user cart
                    session_cart.user = request.user
                    session_cart.session_key = None
                    session_cart.save()
                    cart = session_cart
                else:
                    # Create new cart for the user
                    cart = self.create(
                        user=request.user,
                        is_active=True
                    )
        else:
            # For anonymous users, get or create cart with session key
            cart = self.filter(
                session_key=session_key,
                is_active=True
            ).first()
            
            if not cart:
                cart = self.create(
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
        blank=True, 
        null=True,
        help_text='Session key for guest users',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text='If false, this cart is archived after checkout or cancellation.'
    )
    
    objects = CartManager()

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username} (ID: {self.id})"
        return f"Session cart {self.session_key} (ID: {self.id})"

    def get_stores(self):
        """Get all unique stores in this cart"""
        store_ids = self.items.values_list('variant__product__store', flat=True).distinct()
        from store.models import Store
        return Store.objects.filter(id__in=store_ids)

    def get_items_by_store(self):
        """Group cart items by store"""
        from collections import defaultdict
        store_items = defaultdict(list)
        for item in self.items.select_related('variant__product__store').all():
            store_items[item.variant.product.store].append(item)
        return dict(store_items)

    def get_subtotal_for_store(self, store):
        """Get subtotal for items from a specific store"""
        return sum(
            item.get_subtotal()
            for item in self.items.filter(variant__product__store=store)
        )

    def get_tax_for_store(self, store):
        """Calculate tax for items from a specific store"""
        subtotal = self.get_subtotal_for_store(store)
        store.tax_rate = 0.5
        # return subtotal * (store.tax_rate / 100) if store.tax_rate else 0
        return subtotal * 1

    def get_shipping_for_store(self, store):
        """Get shipping cost for a specific store"""
        # return store.shipping_cost or 0
        return 0

    def get_total_for_store(self, store):
        """Get total for items from a specific store"""
        subtotal = self.get_subtotal_for_store(store)
        tax = self.get_tax_for_store(store)
        shipping = self.get_shipping_for_store(store)
        return subtotal + tax + shipping

    def get_grand_total(self):
        """Get grand total for all items in cart across all stores"""
        return sum(
            self.get_total_for_store(store)
            for store in self.get_stores()
        )

    @property
    def total_items(self):
        return self.items.count()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'session_key', 'is_active']),
            models.Index(fields=['is_active']),
        ]


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
        Returns 0 if unit_price is not set.
        """
        if self.unit_price is None or self.quantity is None:
            return 0
        return self.unit_price * self.quantity
