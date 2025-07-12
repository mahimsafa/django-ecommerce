from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Prefetch, Q
from product.models import Product, Variant, Category

# Create your views here.

class StoreFrontView(ListView):
    model = Product
    template_name = "store_front/home.html"
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        # Get all variants that are either on sale or not (since we don't have is_active)
        # We'll use is_on_sale as a proxy for active status
        available_variants = Variant.objects.all()
        
        # Get products that are published and have at least one variant
        return Product.objects.filter(
            status='published',
            variants__isnull=False  # Ensure product has at least one variant
        ).distinct().prefetch_related(
            Prefetch('variants', queryset=available_variants)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'store_front/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(
            status='published'
        ).prefetch_related(
            'variants',
            'images'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Get all variants for the product
        variants = product.variants.all()
        
        # Get related products (products from the same category)
        related_products = Product.objects.filter(
            category=product.category,
            status='published'
        ).exclude(id=product.id).prefetch_related('variants')[:4]
        
        # Get default variant (first variant)
        default_variant = variants.first()
        
        context.update({
            'variants': variants,
            'default_variant': default_variant,
            'related_products': related_products,
            'in_wishlist': False,  # You can implement wishlist functionality later
        })
        
        return context