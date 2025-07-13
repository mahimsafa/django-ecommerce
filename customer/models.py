from django.db import models
from django.conf import settings
from django.db.models import Q, UniqueConstraint
from django.core.validators import RegexValidator
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


class Address(models.Model):
    """
    Represents a customer's address for shipping or billing.
    """
    # Address types
    ADDRESS_TYPES = (
        ('shipping', 'Shipping Address'),
        ('billing', 'Billing Address'),
    )
    
    # Countries list (you might want to use django-countries in production)
    COUNTRIES = (
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('GB', 'United Kingdom'),
        ('AU', 'Australia'),
        ('BD', 'Bangladesh'),
        # Add more countries as needed
    )
    
    customer = models.ForeignKey(
        Customer,
        related_name='addresses',
        on_delete=models.CASCADE,
        help_text='The customer this address belongs to'
    )
    address_type = models.CharField(
        max_length=10,
        choices=ADDRESS_TYPES,
        help_text='Type of address (shipping/billing)'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Set as default address of this type'
    )
    first_name = models.CharField(
        max_length=150,
        help_text='Recipient first name'
    )
    last_name = models.CharField(
        max_length=150,
        help_text='Recipient last name'
    )
    company = models.CharField(
        max_length=255,
        blank=True,
        help_text='Company name (optional)'
    )
    street_address_1 = models.CharField(
        max_length=255,
        help_text='Street address, line 1'
    )
    street_address_2 = models.CharField(
        max_length=255,
        blank=True,
        help_text='Street address, line 2 (optional)'
    )
    city = models.CharField(
        max_length=100,
        help_text='City'
    )
    state = models.CharField(
        max_length=100,
        help_text='State/Province/Region'
    )
    postal_code = models.CharField(
        max_length=20,
        help_text='ZIP/Postal code'
    )
    country = models.CharField(
        max_length=2,
        choices=COUNTRIES,
        default='BD',
        help_text='Country'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text='Contact phone number (optional)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-updated_at']
        constraints = [
            UniqueConstraint(
                fields=['customer', 'address_type', 'is_default'],
                condition=Q(is_default=True),
                name='unique_default_address_per_type'
            ),
        ]

    def __str__(self):
        return f"{self.get_address_type_display()} - {self.first_name} {self.last_name}, {self.city}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address of each type per customer
        if self.is_default:
            # Update other addresses of the same type to non-default
            Address.objects.filter(
                customer=self.customer,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        address_parts = [
            self.street_address_1,
            self.street_address_2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.get_country_display()
        ]
        return ', '.join(part for part in address_parts if part)