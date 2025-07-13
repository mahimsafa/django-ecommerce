from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'get_name', 'get_user_link', 'store', 'order_count', 'created_at')
    list_filter = ('store', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'get_user_link', 'order_count')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'store')
    fieldsets = (
        (None, {
            'fields': ('store', 'user', 'get_user_link', 'email', 'first_name', 'last_name', 'phone')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('orders')
    
    def get_user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return mark_safe(f'<a href="{url}">{obj.user}</a>')
        return "-"
    get_user_link.short_description = 'User Account'
    
    def get_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else "-"
    get_name.short_description = 'Name'
    get_name.admin_order_field = 'first_name'
    
    def order_count(self, obj):
        count = obj.orders.count()
        url = (
            reverse('admin:order_order_changelist')
            + f'?customer__id__exact={obj.id}'
        )
        return mark_safe(f'<a href="{url}">{count} orders</a>')
    order_count.short_description = 'Orders'


admin.site.register(Customer, CustomerAdmin)
