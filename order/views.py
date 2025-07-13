from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Order, OrderItem
from customer.models import Customer
from store.models import Store

@login_required
def order_history(request):
    """
    Display a paginated list of the user's past orders.
    """
    # Get all orders for the current user
    orders_list = Order.objects.filter(customer=request.user)\
                              .select_related('store')\
                              .prefetch_related('items')\
                              .annotate(item_count=Sum('items__quantity'))\
                              .order_by('-placed_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders_list, 10)  # Show 10 orders per page
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'active_tab': 'orders',
        'paginator': paginator,
        'page_obj': orders,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'order/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """
    Display the details of a specific order.
    """
    # Get the order with related data
    order = get_object_or_404(
        Order.objects.select_related(
            'customer', 'shipping_address', 'billing_address', 'store'
        ).prefetch_related(
            'items',
            'items__variant',
            'items__variant__product',
            'items__variant__product__store'
        ),
        id=order_id,
        customer=request.user  # Filter by the user instead of customer profile
    )
    
    # Get or create customer profile for the current user
    store = Store.objects.first()
    customer_profile = None
    if store:
        customer_profile, created = Customer.objects.get_or_create(
            user=request.user,
            store=store,
            defaults={
                'email': request.user.email,
                'first_name': getattr(request.user, 'first_name', ''),
                'last_name': getattr(request.user, 'last_name', ''),
            }
        )
    
    # Group items by store
    items_by_store = {}
    for item in order.items.all():
        store = item.variant.product.store
        if store not in items_by_store:
            items_by_store[store] = []
        items_by_store[store].append(item)
    
    context = {
        'order': order,
        'customer': customer_profile,  # Add customer profile to context
        'items_by_store': items_by_store,
        'active_tab': 'orders',
    }
    return render(request, 'order/order_detail.html', context)


@login_required
@require_POST
def cancel_order(request, order_id):
    """
    Cancel an order if it's in a cancellable state.
    """
    # Get the order
    order = get_object_or_404(
        Order.objects.select_related('customer__user'),
        id=order_id,
        customer__user=request.user
    )
    
    # Check if order can be cancelled
    if not order.can_cancel():
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('order:order_detail', order_id=order.id)
    
    # Update order status
    order.status = 'cancelled'
    order.save(update_fields=['status'])
    
    # TODO: Add logic to handle inventory restocking if needed
    # TODO: Send order cancellation email
    
    messages.success(request, f'Order #{order.id} has been cancelled.')
    return redirect('order:order_detail', order_id=order.id)
