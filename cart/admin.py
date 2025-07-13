from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('get_variant_link', 'unit_price', 'get_subtotal')
    fields = ('get_variant_link', 'quantity', 'unit_price', 'get_subtotal')
    
    def get_variant_link(self, obj):
        if obj.variant:
            url = reverse('admin:product_variant_change', args=[obj.variant.id])
            return mark_safe(f'<a href="{url}">{obj.variant}</a>')
        return "-"
    get_variant_link.short_description = 'Variant'
    
    def get_subtotal(self, obj):
        return obj.get_subtotal()
    get_subtotal.short_description = 'Subtotal'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'store', 'item_count', 'get_total', 'created_at', 'is_active')
    list_filter = ('is_active', 'store', 'created_at')
    search_fields = ('user__username', 'user__email', 'session_key', 'id')
    readonly_fields = ('created_at', 'updated_at', 'get_user', 'get_total')
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'store')
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')
    
    def get_user(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return mark_safe(f'<a href="{url}">{obj.user}</a>')
        return f'Guest ({obj.session_key})'
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user__username'
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_cart', 'get_variant', 'quantity', 'unit_price', 'get_subtotal')
    list_filter = ('cart__store',)
    search_fields = ('cart__id', 'variant__name', 'variant__sku')
    readonly_fields = ('added_at', 'updated_at', 'get_subtotal')
    list_select_related = ('cart', 'variant', 'cart__store')
    
    def get_cart(self, obj):
        url = reverse('admin:cart_cart_change', args=[obj.cart.id])
        return mark_safe(f'<a href="{url}">Cart {obj.cart.id}</a>')
    get_cart.short_description = 'Cart'
    get_cart.admin_order_field = 'cart__id'
    
    def get_variant(self, obj):
        if obj.variant:
            url = reverse('admin:product_variant_change', args=[obj.variant.id])
            return mark_safe(f'<a href="{url}">{obj.variant}</a>')
        return "-"
    get_variant.short_description = 'Variant'
    get_variant.admin_order_field = 'variant__name'
    
    def get_subtotal(self, obj):
        return obj.get_subtotal()
    get_subtotal.short_description = 'Subtotal'
