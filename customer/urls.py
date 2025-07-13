from django.urls import path
from . import views
from . import views_debug

app_name = 'customer'

urlpatterns = [
    # Customer profile
    path('profile/', views.profile_view, name='profile'),
    
    # Address management
    path('addresses/', views.AddressListView.as_view(), name='address_list'),
    path('addresses/add/', views.AddressCreateView.as_view(), name='address_create'),
    path('addresses/<int:pk>/edit/', views.AddressUpdateView.as_view(), name='address_update'),
    path('addresses/<int:pk>/delete/', views.AddressDeleteView.as_view(), name='address_delete'),
    path('addresses/<int:pk>/set-default/<str:address_type>/', views.set_default_address, name='set_default_address'),
    
    # Orders
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Account settings
    path('settings/', views.AccountSettingsView.as_view(), name='account_settings'),
    
    # API endpoints
    path('api/addresses/', views.AddressListCreateAPIView.as_view(), name='api_address_list_create'),
    path('api/addresses/<int:pk>/', views.AddressRetrieveUpdateDestroyAPIView.as_view(), name='api_address_detail'),
    
    # Debug URLs
    path('debug/template/', views_debug.debug_template_loading, name='debug_template'),
]
