from django.contrib import admin
from .models import Product, Variant, Image
from django.utils.html import format_html
from django import forms


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any custom form initialization here


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1
    fields = ('image', 'alt_text')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No Image"
    preview.short_description = 'Preview'


class VariantInline(admin.TabularInline):
    model = Variant
    form = VariantForm
    extra = 1
    show_change_link = True
    fields = ('name', 'sku', 'default_price', 'sale_price', 'is_on_sale')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'created_at', 'updated_at', 'variant_count')
    list_filter = ('store', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [VariantInline, ImageInline]
    date_hierarchy = 'created_at'
    list_select_related = ('store',)
    readonly_fields = ('created_at', 'updated_at')
    
    def variant_count(self, obj):
        return obj.variants.count()
    variant_count.short_description = 'Variants'


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'sku', 'get_price_display', 'is_on_sale', 'created_at')
    list_filter = ('product__store', 'is_on_sale', 'created_at', 'updated_at')
    search_fields = ('name', 'sku', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('product', 'product__store')
    
    def get_price_display(self, obj):
        if obj.is_on_sale and obj.sale_price is not None:
            return f"${obj.sale_price} {obj.currency} (Sale, was ${obj.default_price})"
        return f"${obj.default_price} {obj.currency}"
    get_price_display.short_description = 'Price'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'preview', 'product', 'variant', 'uploaded_at')
    list_filter = ('uploaded_at', 'updated_at')
    search_fields = ('product__name', 'variant__name', 'alt_text')
    readonly_fields = ('preview', 'uploaded_at', 'updated_at')
    list_select_related = ('product', 'variant', 'product__store')
    
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.image.url
            )
        return "No Image"
    preview.short_description = 'Preview'



