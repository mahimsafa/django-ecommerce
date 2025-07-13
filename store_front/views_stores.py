from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from store.models import Store
from product.models import Product
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import models


class StoreListView(ListView):
    model = Store
    template_name = 'store_front/store_list.html'
    context_object_name = 'stores'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Store.objects.filter()
        search_query = self.request.GET.get('q')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(slug__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tagline__icontains=search_query)
            )
        return queryset.order_by('name')


class StoreProductListView(ListView):
    template_name = 'store_front/store_products.html'
    context_object_name = 'products'
    paginate_by = 16
    
    def get_queryset(self):
        self.store = get_object_or_404(Store, slug=self.kwargs['store_slug'])
        queryset = Product.objects.filter(
            store=self.store,
            status='published',
            variants__isnull=False
        ).distinct()
        # Apply search if provided
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(variants__name__icontains=search_query) |
                Q(variants__sku__iexact=search_query)
            ).distinct()
            
        # # Apply category filter if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        return queryset.select_related('category').prefetch_related('images', 'variants')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.store
        
        # Initialize categories as an empty list by default
        categories = []
        
        # Only try to get categories if the store has products
        if hasattr(self.store, 'products'):
            categories = self.store.products.filter(
                status='published',
                variants__isnull=False
            ).values(
                'category__id', 
                'category__name', 
                'category__slug'
            ).annotate(
                product_count=Count('id', distinct=True)
            ).filter(category__isnull=False)
        
        context['categories'] = categories
        return context
