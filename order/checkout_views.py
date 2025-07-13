from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from cart.models import Cart, CartItem
from customer.models import Customer, Address
from store.models import Store
from .models import Order, OrderItem, OrderProduct, OrderProductVariant, OrderProductPrice

@login_required
def checkout_view(request):
    """
    Display the checkout page with the user's cart and shipping/billing information.
    """
    # Get the user's cart
    cart = Cart.objects.get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:view')
    
    # Get or create customer profile
    store = Store.objects.first()  # In a multi-store setup, you'd get the appropriate store
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        store=store,
        defaults={
            'email': request.user.email,
            'first_name': getattr(request.user, 'first_name', ''),
            'last_name': getattr(request.user, 'last_name', ''),
        }
    )
    
    # Get or create default addresses
    shipping_address = Address.objects.filter(customer=customer, address_type='shipping').first()
    billing_address = Address.objects.filter(customer=customer, address_type='billing').first()
    
    # Group cart items by store and calculate store totals
    items_by_store = cart.get_items_by_store()
    store_totals = {}
    
    # Calculate totals for each store
    for store, items in items_by_store.items():
        store_totals[store.id] = {
            'subtotal': cart.get_subtotal_for_store(store),
            'tax': cart.get_tax_for_store(store),
            'shipping': cart.get_shipping_for_store(store),
            'total': cart.get_total_for_store(store)
        }

    context = {
        'cart': cart,
        'items_by_store': items_by_store,
        'store_totals': store_totals,
        'grand_total': cart.get_grand_total(),
        'shipping_address': shipping_address,
        'billing_address': billing_address,
        'customer': customer,
    }
    
    return render(request, 'order/checkout.html', context)

@login_required
def process_checkout(request):
    """
    Process the checkout and create an order from the cart.
    """
    if request.method != 'POST':
        return redirect('cart:view')
    
    # Get the user's cart
    cart = Cart.objects.get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:view')
    
    # Get or create customer profile
    store = Store.objects.first()  # In a multi-store setup, you'd get the appropriate store
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        store=store,
        defaults={
            'email': request.user.email,
            'first_name': getattr(request.user, 'first_name', ''),
            'last_name': getattr(request.user, 'last_name', ''),
        }
    )
    
    # Get addresses from the form
    shipping_address_id = request.POST.get('shipping_address')
    billing_address_id = request.POST.get('billing_address')
    
    try:
        shipping_address = Address.objects.get(id=shipping_address_id, customer=customer)
        billing_address = Address.objects.get(id=billing_address_id, customer=customer)
    except (Address.DoesNotExist, ValueError):
        messages.error(request, "Please provide valid shipping and billing addresses.")
        return redirect('order:checkout')
    
    # Get email and phone from the request
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    
    if not email or not phone:
        messages.error(request, "Email and phone are required.")
        return redirect('order:checkout')
    
    # Start a transaction to ensure data consistency
    with transaction.atomic():
        try:
            # Calculate order totals
            subtotal = sum(item.get_subtotal() for item in cart.items.all())
            # tax = sum(cart.get_tax_for_store(store) for store in cart.get_stores())
            tax=0
            # shipping_cost = sum(cart.get_shipping_for_store(store) for store in cart.get_stores())
            shipping_cost=0
            total = cart.get_grand_total()
            
            # Create the order with the user object and contact info
            order = Order.objects.create(
                store=store,
                customer=request.user if request.user.is_authenticated else None,
                customer_email=email,
                customer_phone=phone,
                shipping_address=shipping_address,
                billing_address=billing_address,
                status='pending',
                placed_at=timezone.now(),
                subtotal=subtotal,
                tax=tax,
                shipping_cost=shipping_cost,
                total=total,
            )
            # Create order items from cart items
            for item in cart.items.all():
                # Create or get order product
                product, _ = OrderProduct.objects.get_or_create(
                    store=store,
                    sku=item.variant.sku,
                    defaults={
                        'name': item.variant.product.name,
                        'description': item.variant.product.description,
                    }
                )
                
                # Check if variant already exists
                variant, created = OrderProductVariant.objects.get_or_create(
                    sku=item.variant.sku,
                    defaults={
                        'product': product,
                        'name': item.variant.name,
                    }
                )
                
                # Create or update price for the variant
                OrderProductPrice.objects.update_or_create(
                    variant=variant,
                    defaults={
                        'amount': item.unit_price,
                        'currency': 'USD',  # You might want to make this dynamic
                    }
                )
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            # Clear the cart
            cart.items.all().delete()
            cart.updated_at = timezone.now()
            cart.save()
            
            # Redirect to order confirmation page
            messages.success(request, "Your order has been placed successfully!")
            return redirect('order:order_confirmation', order_id=order.id)
            
        except Exception as e:
            # Log the error
            print(f"Error during checkout: {str(e)}")
            messages.error(request, "An error occurred while processing your order. Please try again.")
            return redirect('order:checkout')

@login_required
def order_confirmation(request, order_id):
    """
    Display the order confirmation page after a successful checkout.
    """
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'order/order_confirmation.html', {'order': order})
