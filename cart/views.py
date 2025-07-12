from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.views.generic import View
from django.urls import reverse
from django.db import transaction

from product.models import Variant
from store.models import Store
from .models import Cart, CartItem

@login_required
@require_POST
def add_to_cart(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id)
    store = variant.product.store
    quantity = int(request.POST.get('quantity', 1))
    
    # Get or create active cart for user and store
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        store=store,
        is_active=True,
        defaults={'store': store}
    )
    
    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={
            'unit_price': variant.sale_price if variant.is_on_sale else variant.default_price,
            'quantity': 0
        }
    )
    
    # Update quantity
    cart_item.quantity += quantity
    cart_item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart',
            'cart_count': cart.items.count()
        })
    
    messages.success(request, 'Item added to cart')
    return redirect('store_front:home')

def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(cart__user=request.user, cart__is_active=True).count()
    else:
        count = 0
    return JsonResponse({'count': count})


class CartView(View):
    template_name = 'cart/cart.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to view your cart')
            return redirect('login')
            
        # Get user's active cart with items
        cart = Cart.objects.filter(
            user=request.user, 
            is_active=True
        ).prefetch_related('items__variant__product__images').first()
        
        context = {
            'cart': cart,
            'cart_items': cart.items.all() if cart else []
        }
        return render(request, self.template_name, context)


@login_required
@require_http_methods(["POST"])
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    with transaction.atomic():
        if action == 'update':
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                item.quantity = quantity
                item.save()
                messages.success(request, 'Cart updated successfully')
            else:
                item.delete()
                messages.success(request, 'Item removed from cart')
        elif action == 'remove':
            item.delete()
            messages.success(request, 'Item removed from cart')
    
    return HttpResponseRedirect(reverse('cart:view'))


@login_required
def clear_cart(request):
    Cart.objects.filter(user=request.user, is_active=True).delete()
    messages.success(request, 'Your cart has been cleared')
    return HttpResponseRedirect(reverse('cart:view'))
