from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('variant_info', 'quantity', 'unit_price',
                       'tax_amount', 'discount_amount', 'line_total_display')
    fields = ('variant_info', 'quantity', 'unit_price',
              'tax_amount', 'discount_amount', 'line_total_display')

    def variant_info(self, obj):
        if obj.variant:
            return str(obj.variant)
        return "-"
    variant_info.short_description = 'Variant'

    def line_total_display(self, obj):
        return f"${obj.line_total:.2f}"
    line_total_display.short_description = 'Line Total'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_customer', 'store', 'status',
                    'total', 'placed_at', 'item_count')
    list_filter = ('status', 'store', 'placed_at')
    search_fields = ('id', 'customer__email',
                     'customer__first_name', 'customer__last_name')
    readonly_fields = (
        'placed_at', 'updated_at', 'get_customer', 'subtotal', 'tax',
        'discount_total', 'total', 'item_count', 'cancelled_at', 'cancelled_by',
        'shipping_address_display', 'billing_address_display', 'customer_display'
    )
    inlines = [OrderItemInline]
    date_hierarchy = 'placed_at'
    list_select_related = ('customer', 'store',
                           'shipping_address', 'billing_address')
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_cancelled']
    # change_form_template = 'admin/order/order/change_form.html'

    fieldsets = (
        (None, {
            'fields': ('store', 'get_customer', 'status')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'tax', 'discount_total', 'total')
        }),
        ('Customer Details', {
            'fields': ('customer_display',),
        }),
        ('Address', {
            'fields': ('shipping_address_display', 'billing_address_display'),
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('placed_at', 'updated_at', 'cancelled_at', 'cancelled_by'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

    def get_customer(self, obj):
        url = reverse('admin:customer_customer_change', args=[obj.customer.id])
        return mark_safe(f'<a href="{url}">{obj.customer}</a>')
    get_customer.short_description = 'Customer'
    get_customer.admin_order_field = 'customer__email'

    def customer_display(self, obj):
        customer = obj.customer
        if customer:
            # Get the associated user if it's an authenticated customer
            if hasattr(customer, 'user') and customer.user:
                first_name = customer.user.first_name
                last_name = customer.user.last_name
                email = customer.user.email
            else:
                # Fallback to customer model fields if user doesn't exist
                first_name = getattr(customer, 'first_name', '')
                last_name = getattr(customer, 'last_name', '')
                email = getattr(customer, 'email', 'Not provided')
                
            return format_html(
                '<div style="white-space: pre-line">'
                '<strong>Full Name:</strong> {} {}\n'
                '<strong>Email:</strong> {}\n'
                '<strong>Phone:</strong> {}'
                '</div>',
                first_name or '',
                last_name or '',
                email,
                getattr(customer, 'phone', 'Not provided'),
            )
        return 'No customer information available'

    customer_display.short_description = 'Customer Details'

    def shipping_address_display(self, obj):
        if obj.shipping_address:
            address = obj.shipping_address
            return format_html(
                '<div style="white-space: pre-line">'
                '<strong>Full Name:</strong> {} {}\n'
                '<strong>Company:</strong> {}\n'
                '<strong>Address Line 1:</strong> {}\n'
                '<strong>Address Line 2:</strong> {}\n'
                '<strong>City:</strong> {}\n'
                '<strong>State/Province:</strong> {}\n'
                '<strong>Postal Code:</strong> {}\n'
                '<strong>Country:</strong> {}\n'
                '<strong>Phone:</strong> {}'
                '</div>',
                address.first_name, address.last_name,
                address.company or 'Not provided',
                address.street_address_1,
                address.street_address_2 or 'Not provided',
                address.city,
                address.state,
                address.postal_code,
                address.get_country_display(),
                address.phone or 'Not provided'
            )
        return 'No shipping address'
    shipping_address_display.short_description = 'Shipping Address'

    def billing_address_display(self, obj):
        if obj.billing_address:
            address = obj.billing_address
            return format_html(
                '<div style="white-space: pre-line">'
                '<strong>Full Name:</strong> {} {}\n'
                '<strong>Company:</strong> {}\n'
                '<strong>Address Line 1:</strong> {}\n'
                '<strong>Address Line 2:</strong> {}\n'
                '<strong>City:</strong> {}\n'
                '<strong>State/Province:</strong> {}\n'
                '<strong>Postal Code:</strong> {}\n'
                '<strong>Country:</strong> {}\n'
                '<strong>Phone:</strong> {}'
                '</div>',
                address.first_name, address.last_name,
                address.company or 'Not provided',
                address.street_address_1,
                address.street_address_2 or 'Not provided',
                address.city,
                address.state,
                address.postal_code,
                address.get_country_display(),
                address.phone or 'Not provided'
            )
        return 'No billing address'
    billing_address_display.short_description = 'Billing Address'

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

    @admin.action(description='Mark selected orders as Processing')
    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(
            status__in=['pending', 'confirmed']).update(status='processing')
        self.message_user(request, f'{updated} orders marked as Processing.')

    @admin.action(description='Mark selected orders as Completed')
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(
            status__in=['processing', 'confirmed']).update(status='completed')
        self.message_user(request, f'{updated} orders marked as Completed.')

    @admin.action(description='Mark selected orders as Cancelled')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(
            status='cancelled').update(status='cancelled')
        self.message_user(request, f'{updated} orders marked as Cancelled.')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_order', 'get_variant',
                    'quantity', 'unit_price', 'get_line_total')
    list_filter = ('order__store', 'order__status')
    search_fields = ('order__id', 'variant__name', 'variant__sku')
    readonly_fields = ('get_order', 'get_variant', 'quantity',
                       'unit_price', 'tax_amount', 'discount_amount')
    list_select_related = (
        'order', 'variant', 'order__store', 'order__customer')

    def get_order(self, obj):
        url = reverse('admin:order_order_change', args=[obj.order.id])
        return mark_safe(f'<a href="{url}">Order {obj.order.id}</a>')
    get_order.short_description = 'Order'
    get_order.admin_order_field = 'order__id'

    def get_variant(self, obj):
        if obj.variant:
            url = reverse('admin:product_variant_change',
                          args=[obj.variant.id])
            return mark_safe(f'<a href="{url}">{obj.variant}</a>')
        return "-"
    get_variant.short_description = 'Variant'
    get_variant.admin_order_field = 'variant__name'

    def get_line_total(self, obj):
        return f"${obj.line_total:.2f}"
    get_line_total.short_description = 'Line Total'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
