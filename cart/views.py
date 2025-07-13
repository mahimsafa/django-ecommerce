from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.views.generic import View
from django.urls import reverse
from django.db import transaction
from django.conf import settings

from product.models import Variant, Image as ProductImage
from store.models import Store
from .models import Cart, CartItem

@require_POST
def add_to_cart(request, variant_id):
    try:
        variant = get_object_or_404(Variant, id=variant_id)
        store = variant.product.store
        quantity = int(request.POST.get('quantity', 1))
        
        # Store the current store ID in session for future requests
        request.session['current_store_id'] = store.id
        
        # Get or create cart for the user/session
        cart = Cart.objects.get_or_create_cart(request, store)
        
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
        
        # Update cart timestamp
        cart.save()
        
        # Debug output
        print(f"Added to cart - Product: {variant.product.name}, Qty: {quantity}, Cart ID: {cart.id}")
        print(f"Current cart items: {cart.items.count()}")
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': 'Item added to cart',
                'cart_count': cart.items.count(),
                'cart_total': str(cart.get_total())
            })
        
        messages.success(request, f'Added {variant.product.name} to your cart')
        return redirect(request.META.get('HTTP_REFERER', 'store_front:home'))
        
    except Exception as e:
        import traceback
        print(f"Error in add_to_cart: {str(e)}")
        print(traceback.format_exc())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error adding item to cart: {str(e)}'
            }, status=400)
            
        messages.error(request, 'Error adding item to cart. Please try again.')
        return redirect(request.META.get('HTTP_REFERER', 'store_front:home'))

from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def cart_count(request):
    try:
        if request.user.is_authenticated:
            count = CartItem.objects.filter(cart__user=request.user, cart__is_active=True).count()
        else:
            if not request.session.session_key:
                request.session.create()  # Ensure session exists for guest users
                count = 0
            else:
                count = CartItem.objects.filter(
                    cart__session_key=request.session.session_key, 
                    cart__is_active=True
                ).count()
        return JsonResponse({'count': count, 'status': 'success'})
    except Exception as e:
        return JsonResponse({'count': 0, 'status': 'error', 'message': str(e)})

class CartView(View):
    template_name = 'cart/cart.html'
    
    def get(self, request, *args, **kwargs):
        try:
            # Get store from session or use the first available store
            store_id = request.session.get('current_store_id')
            if store_id:
                store = Store.objects.filter(id=store_id).first()
            
            # If no store in session or not found, get the first store
            if not store_id or not store:
                store = Store.objects.first()
                if store:
                    request.session['current_store_id'] = store.id
            
            if not store:
                messages.error(request, "No store available. Please try again later.")
                return render(request, self.template_name, {'cart': None, 'items': []})
            
            # Get or create cart for the current user/session
            cart = Cart.objects.get_or_create_cart(request, store)
            
            # Get items with product and variant details
            items = cart.items.select_related('variant__product').all()
            
            # Debug output
            print(f"Cart ID: {cart.id}")
            print(f"Items in cart: {items.count()}")
            for item in items:
                print(f"- {item.variant.product.name} (Qty: {item.quantity})")
            
            context = {
                'cart': cart,
                'items': items,
                'store': store
            }
            return render(request, self.template_name, context)
            
        except Exception as e:
            import traceback
            print(f"Error in CartView: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Error loading cart. Please try again.")
            return render(request, self.template_name, {'cart': None, 'items': [], 'store': None})

@require_http_methods(["POST"])
def update_cart_item(request, item_id):
    try:
        if request.user.is_authenticated:
            cart_item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user,
                cart__is_active=True
            )
        else:
            if not request.session.session_key:
                return JsonResponse({'error': 'No active session'}, status=400)
                
            cart_item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__session_key=request.session.session_key,
                cart__is_active=True
            )
        
        action = request.POST.get('action')
    
        with transaction.atomic():
            if action == 'update':
                try:
                    quantity = int(request.POST.get('quantity', 1))
                    if quantity > 0:
                        cart_item.quantity = quantity
                        cart_item.save()
                        messages.success(request, 'Cart updated successfully')
                    else:
                        cart_item.delete()
                        messages.success(request, 'Item removed from cart')
                except (ValueError, TypeError):
                    messages.error(request, 'Invalid quantity')
                    return HttpResponseRedirect(reverse('cart:view'))
                    
            elif action == 'remove':
                cart_item.delete()
                messages.success(request, 'Item removed from cart')
    
        return HttpResponseRedirect(reverse('cart:view'))
        
    except Exception as e:
        messages.error(request, f'Error updating cart: {str(e)}')
        return HttpResponseRedirect(reverse('cart:view'))

@require_http_methods(["POST"])
def clear_cart(request):
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user, is_active=True).delete()
    elif request.session.session_key:
        Cart.objects.filter(
            session_key=request.session.session_key, 
            is_active=True
        ).delete()
    messages.success(request, "Your cart has been cleared.")
    return redirect('cart:view')
