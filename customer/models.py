from django.db import models
from django.conf import settings
from django.db.models import Q, UniqueConstraint
from store.models import Store

# Create your models here.


class CustomerManager(models.Manager):
    def get_for_user(self, user, store):
        """
        Return an existing customer linked to this authenticated user & store,
        or create it if missing.
        """
        customer, created = self.get_or_create(
            store=store,
            user=user,
            defaults={
                'email': user.email,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
            }
        )
        return customer

    def get_for_guest(self, email, store, first_name=None, last_name=None, phone=None):
        """
        Return or create a guest customer by email for the given store.
        """
        customer, created = self.get_or_create(
            store=store,
            user=None,
            email=email,
            defaults={
                'first_name': first_name or '',
                'last_name': last_name or '',
                'phone': phone or '',
            }
        )
        return customer


class Customer(models.Model):
    """
    Represents a customer for a store, either an authenticated user or a guest (email).
    """
    store = models.ForeignKey(
        Store,
        related_name='customers',
        on_delete=models.CASCADE
    )
    # Link to auth user, or null for guests
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='customer_profiles',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    email = models.EmailField(
        help_text='Email address for contact/receipts'
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomerManager()

    class Meta:
        constraints = [
            # Each authenticated user has one profile per store
            UniqueConstraint(
                fields=['store', 'user'],
                condition=Q(user__isnull=False),
                name='unique_store_user_customer'
            ),
            # Each guest (no user) uniquely identified by email per store
            UniqueConstraint(
                fields=['store', 'email'],
                condition=Q(user__isnull=True),
                name='unique_store_guest_email'
            ),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        if self.user:
            return f"{self.user.username} @ {self.store.name}"
        return f"Guest {self.email} @ {self.store.name}"