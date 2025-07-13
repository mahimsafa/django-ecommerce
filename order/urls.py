from django.urls import path
from . import views
from . import checkout_views

app_name = 'order'

urlpatterns = [
    path('', views.order_history, name='order_history'),
    path('checkout/', checkout_views.checkout_view, name='checkout'),
    path('checkout/process/', checkout_views.process_checkout, name='process_checkout'),
    path('order-confirmation/<int:order_id>/', checkout_views.order_confirmation, name='order_confirmation'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
]
