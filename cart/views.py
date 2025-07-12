from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from product.models import Variant
from store.models import Store
from .models import Cart, CartItem

@login_required
@require_POST
def add_to_cart(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id, is_active=True)
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
