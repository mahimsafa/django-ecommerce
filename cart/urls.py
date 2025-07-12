from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import CartAPIView, CartItemAPIView, ClearCartAPIView

app_name = 'cart'

# API URLs
urlpatterns = [
    # Cart operations
    path('api/cart/', CartAPIView.as_view(), name='api_cart'),
    path('api/cart/clear/', ClearCartAPIView.as_view(), name='api_clear_cart'),
    path('api/cart/items/<int:item_id>/', CartItemAPIView.as_view(), name='api_cart_item'),
    
    # Keep the old URLs for backward compatibility
    path('', views.CartView.as_view(), name='view'),
    path('add/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('count/', views.cart_count, name='cart_count'),
]
