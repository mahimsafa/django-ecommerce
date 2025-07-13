from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse

User = get_user_model()

# Create your models here.

class Store(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='store_thumbnails/', blank=True, null=True)
    tagline = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name='stores', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('store_front:store_products', kwargs={'store_slug': self.slug})

class StoreStaff(models.Model):
    """
    Staff or sub-admin for a store.
    """
    store = models.ForeignKey(Store, related_name='staff_members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='store_roles', on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('store', 'user')

    def __str__(self):
        role = 'Admin' if self.is_admin else 'Staff'
        return f"{self.user.username} - {role} at {self.store.name}"

class Config(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.store.name

class Settings(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.store.name