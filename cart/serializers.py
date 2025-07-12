from rest_framework import serializers
from .models import Cart, CartItem
from product.models import Variant

class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=Variant.objects.all(), 
        source='variant',
        write_only=True
    )
    name = serializers.CharField(source='variant.product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'variant_id', 'quantity', 'name', 'variant_name', 
            'unit_price', 'subtotal', 'image'
        ]
        read_only_fields = ['id', 'name', 'variant_name', 'unit_price', 'subtotal', 'image']

    def get_image(self, obj):
        if obj.variant.product.images.exists():
            return obj.variant.product.images.first().image.url
        return None

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'items', 'total', 'item_count']
        read_only_fields = ['id', 'created_at', 'items', 'total', 'item_count']

class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_variant_id(self, value):
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid variant ID")
        return value
