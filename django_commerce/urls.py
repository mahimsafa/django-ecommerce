"""
URL configuration for django_commerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import LogoutView, LoginView
from store_front.views_auth import register, logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('store_admin/', include('store_admin.urls', namespace='store_admin')),
    path('', include('store_front.urls')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('order.urls', namespace='order')),  # Order management
    path('customer/', include('customer.urls', namespace='customer')),  # Customer management
    # Authentication URLs
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', logout, name='logout'),  # Using our custom logout view
    path('register/', register, name='register'),  # Custom registration view
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, these should be served by the web server (e.g., Nginx, Apache)
    urlpatterns += staticfiles_urlpatterns()
