from django.urls import path
from . import views
from .views_stores import StoreListView, StoreProductListView

app_name = 'store_front'

urlpatterns = [
    path('', views.StoreFrontView.as_view(), name='home'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Store URLs
    path('stores/', StoreListView.as_view(), name='store_list'),
    path('stores/<slug:store_slug>/', StoreProductListView.as_view(), name='store_products'),
]
