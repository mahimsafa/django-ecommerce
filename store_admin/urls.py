from django.urls import path
from . import views

app_name = 'store_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/edit/<int:product_id>/', views.product_edit, name='product_edit'),
    path('products/add/', views.product_edit, name='product_add'),
    path('products/<int:product_id>/', views.product_edit, name='product_detail'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/edit/<int:order_id>/', views.order_edit, name='order_edit'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
] 