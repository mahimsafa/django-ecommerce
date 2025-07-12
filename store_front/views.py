from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from product.models import Product, Variant
from django.db.models import Prefetch

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