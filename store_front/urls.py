from django.urls import path
from . import views

app_name = 'store_front'

urlpatterns = [
    path('', views.StoreFrontView.as_view(), name='home'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
