from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
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
    
    # Start a transaction to ensure data consistency
    with transaction.atomic():
        try:
            # Create the order
            order = Order.objects.create(
                store=store,
                customer=customer,
                shipping_address=shipping_address,
                billing_address=billing_address,
                status='pending',
                placed_at=timezone.now(),
                subtotal=cart.get_subtotal(),
                tax=cart.get_tax(),
                shipping_cost=cart.get_shipping_cost(),
                total=cart.get_total(),
            )
            
            # Create order items from cart items
            for item in cart.items.all():
                # Create or get order product
                product, _ = OrderProduct.objects.get_or_create(
                    store=store,
                    name=item.variant.product.name,
                    sku=item.variant.sku,
                    defaults={
                        'description': item.variant.product.description,
                    }
                )
                
                # Create order product variant
                variant = OrderProductVariant.objects.create(
                    product=product,
                    name=item.variant.name,
                    sku=item.variant.sku,
                    stock=item.variant.stock,
                )
                
                # Create price for the variant
                OrderProductPrice.objects.create(
                    variant=variant,
                    amount=item.unit_price,
                    currency='USD',  # You might want to make this dynamic
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

def order_confirmation(request, order_id):
    """
    Display the order confirmation page after a successful checkout.
    """
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, 'order/order_confirmation.html', {'order': order})
