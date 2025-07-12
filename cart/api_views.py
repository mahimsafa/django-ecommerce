from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, CartItemSerializer
from product.models import Variant

class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get the user's active cart with all items"""
        # Get the most recent active cart for the user
        cart = Cart.objects.filter(
            user=request.user,
            is_active=True
        ).prefetch_related('items__variant__product').first()
        
        # If no active cart exists, return an empty response
        if not cart:
            return Response({
                'id': None,
                'items': [],
                'total': '0.00',
                'item_count': 0
            })
            
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
                
                # Get or create cart for the user and store
                cart, created = Cart.objects.get_or_create(
                    user=request.user,
                    store=variant.product.store,
                    defaults={'is_active': True}
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
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, item_id):
        """Remove item from cart"""
        try:
            cart_item = get_object_or_404(
                CartItem, 
                id=item_id, 
                cart__user=request.user,
                cart__is_active=True
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
                
            cart_item = get_object_or_404(
                CartItem, 
                id=item_id, 
                cart__user=request.user,
                cart__is_active=True
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
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Clear all items from cart"""
        try:
            cart = get_object_or_404(
                Cart, 
                user=request.user, 
                is_active=True
            )
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
