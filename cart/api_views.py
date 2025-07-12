from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings

from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, CartItemSerializer
from product.models import Variant
from store.models import Store

class CartAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get the user's active cart with all items"""
        # Get the store - you might want to get this from the current store context
        store = Store.objects.first()
        if not store:
            return Response(
                {'error': 'No store available'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create cart for the user/session
        cart = Cart.objects.get_or_create_cart(request, store)
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        variant_id = serializer.validated_data['variant_id']
        quantity = serializer.validated_data['quantity']
        
        try:
            with transaction.atomic():
                variant = get_object_or_404(Variant, id=variant_id)
                store = variant.product.store
                
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
                if not created:
                    cart_item.quantity += quantity
                else:
                    cart_item.quantity = quantity
                cart_item.save()
                
                # Return updated cart
                cart_serializer = CartSerializer(cart)
                return Response({
                    'success': True,
                    'message': 'Item added to cart',
                    'cart': cart_serializer.data,
                    'item_count': cart.items.count()
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CartItemAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get_cart_item(self, request, item_id):
        """Helper method to get cart item with proper permissions"""
        if request.user.is_authenticated:
            return get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user,
                cart__is_active=True
            )
        else:
            if not request.session.session_key:
                return None
            return get_object_or_404(
                CartItem,
                id=item_id,
                cart__session_key=request.session.session_key,
                cart__is_active=True
            )
            
    def delete(self, request, item_id):
        """Remove item from cart"""
        try:
            cart_item = self.get_cart_item(request, item_id)
            if not cart_item:
                return Response(
                    {'error': 'No active session'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart = cart_item.cart
            cart_item.delete()
            
            return Response({
                'success': True,
                'message': 'Item removed from cart',
                'item_count': cart.items.count()
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, item_id):
        """Update cart item quantity"""
        try:
            quantity = int(request.data.get('quantity', 1))
            if quantity < 1:
                return Response(
                    {'error': 'Quantity must be at least 1'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            cart_item = self.get_cart_item(request, item_id)
            if not cart_item:
                return Response(
                    {'error': 'No active session or item not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = quantity
            cart_item.save()
            
            cart_serializer = CartSerializer(cart_item.cart)
            return Response({
                'success': True,
                'message': 'Cart updated',
                'cart': cart_serializer.data,
                'item_count': cart_item.cart.items.count()
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClearCartAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Clear all items from cart"""
        try:
            if request.user.is_authenticated:
                cart = Cart.objects.filter(
                    user=request.user, 
                    is_active=True
                ).first()
            else:
                if not request.session.session_key:
                    return Response({
                        'success': True,
                        'message': 'No active cart',
                        'item_count': 0
                    })
                cart = Cart.objects.filter(
                    session_key=request.session.session_key,
                    is_active=True
                ).first()
            
            if not cart:
                return Response({
                    'success': True,
                    'message': 'No active cart',
                    'item_count': 0
                })
                
            item_count = cart.items.count()
            cart.items.all().delete()
            
            return Response({
                'success': True,
                'message': f'Removed {item_count} items from cart',
                'item_count': 0
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
