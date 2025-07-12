from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('add/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('count/', views.cart_count, name='cart_count'),
]
