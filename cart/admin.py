from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('get_variant_link', 'unit_price_display', 'get_subtotal_display')
    fields = ('get_variant_link', 'quantity', 'unit_price_display', 'get_subtotal_display')
    
    def get_variant_link(self, obj):
        if obj and obj.variant:
            url = reverse('admin:product_variant_change', args=[obj.variant.id])
            return mark_safe(f'<a href="{url}">{obj.variant}</a>')
        return "-"
    get_variant_link.short_description = 'Variant'
    
    def unit_price_display(self, obj):
        if obj and obj.unit_price is not None:
            return f"${obj.unit_price:.2f}"
        return "Not set"
    unit_price_display.short_description = 'Unit Price'
    
    def get_subtotal_display(self, obj):
        if obj:
            subtotal = obj.get_subtotal()
            return f"${subtotal:.2f}" if subtotal is not None else "N/A"
        return "N/A"
    get_subtotal_display.short_description = 'Subtotal'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'store_list', 'item_count', 'get_grand_total_display', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'session_key', 'id')
    readonly_fields = ('created_at', 'updated_at', 'get_user', 'get_grand_total_display', 'store_list')
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'
    list_select_related = ('user',)
    
    def store_list(self, obj):
        stores = obj.get_stores()
        if stores.exists():
            return ", ".join([store.name for store in stores])
        return "No stores"
    store_list.short_description = 'Stores'
    
    def get_grand_total_display(self, obj):
        return f"${obj.get_grand_total():.2f}" if obj.get_grand_total() is not None else "N/A"
    get_grand_total_display.short_description = 'Grand Total'
    
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


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make unit_price read-only if variant is set
        if 'variant' in self.data and 'unit_price' in self.fields:
            try:
                variant_id = self.data.get('variant')
                if variant_id:
                    from product.models import Variant
                    variant = Variant.objects.get(id=variant_id)
                    self.fields['unit_price'].initial = variant.price
            except (ValueError, Variant.DoesNotExist):
                pass
        elif self.instance and self.instance.variant_id and 'unit_price' in self.fields:
            self.fields['unit_price'].initial = self.instance.variant.price

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    form = CartItemForm
    list_display = ('id', 'get_cart', 'get_variant', 'get_store', 'quantity', 'unit_price', 'get_subtotal')
    list_filter = ('variant__product__store',)
    search_fields = ('cart__id', 'variant__name', 'variant__sku')
    readonly_fields = ('added_at', 'updated_at', 'get_subtotal', 'get_store')
    list_select_related = ('cart', 'variant', 'variant__product__store')
    
    def get_store(self, obj):
        if obj and obj.variant and obj.variant.product.store:
            return obj.variant.product.store.name
        return "-"
    get_store.short_description = 'Store'
    get_store.admin_order_field = 'variant__product__store__name'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.variant:
            form.base_fields['unit_price'].help_text = f'Price from variant: {obj.variant.price}'
        return form
    
    def save_model(self, request, obj, form, change):
        # Set unit price from variant if not set
        if obj.variant and (not obj.unit_price or not change):
            obj.unit_price = obj.variant.price
        super().save_model(request, obj, form, change)
    
    def get_cart(self, obj):
        url = reverse('admin:cart_cart_change', args=[obj.cart_id])
        return mark_safe(f'<a href="{url}">Cart #{obj.cart_id}</a>')
    get_cart.short_description = 'Cart'
    get_cart.admin_order_field = 'cart__id'
    
    def get_variant(self, obj):
        if obj.variant:
            url = reverse('admin:product_variant_change', args=[obj.variant_id])
            return mark_safe(f'<a href="{url}">{obj.variant}</a>')
        return "-"
    get_variant.short_description = 'Variant'
    get_variant.admin_order_field = 'variant__name'
    
    def get_subtotal(self, obj):
        return obj.get_subtotal()
    get_subtotal.short_description = 'Subtotal'
