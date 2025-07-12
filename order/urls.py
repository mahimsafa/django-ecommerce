from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('', views.order_history, name='order_history'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
]
