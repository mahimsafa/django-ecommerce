from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from django.urls import reverse
from django.utils import timezone

from .models import Order, OrderItem
from customer.models import Customer
from store.models import Store

@login_required
def order_history(request):
    """
    Display a list of the user's past orders.
    """
    # Get or create customer profile for the current user
    # Using first store for now - in a multi-store setup, you'd want to get the appropriate store
    store = Store.objects.first()
    if not store:
        messages.error(request, 'No store available.')
        return redirect('store_front:home')
    
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        store=store,
        defaults={
            'email': request.user.email,
            'first_name': getattr(request.user, 'first_name', ''),
            'last_name': getattr(request.user, 'last_name', ''),
        }
    )
    
    orders = Order.objects.filter(customer=customer).select_related('store')
    
    # Annotate each order with total items count
    orders = orders.annotate(
        total_items=Sum('items__quantity')
    ).order_by('-placed_at')
    
    context = {
        'orders': orders,
        'active_tab': 'orders',
    }
    return render(request, 'order/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """
    Display the details of a specific order.
    """
    # Get or create customer profile for the current user
    store = Store.objects.first()
    if not store:
        messages.error(request, 'No store available.')
        return redirect('store_front:home')
        
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        store=store,
        defaults={
            'email': request.user.email,
            'first_name': getattr(request.user, 'first_name', ''),
            'last_name': getattr(request.user, 'last_name', ''),
        }
    )
    
    order = get_object_or_404(
        Order.objects.select_related('store', 'customer__user')
                    .prefetch_related('items__variant__product'),
        id=order_id,
        customer=customer
    )
    
    context = {
        'order': order,
        'active_tab': 'orders',
    }
    return render(request, 'order/order_detail.html', context)
