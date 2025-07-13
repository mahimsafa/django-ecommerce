from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from product.models import Product, Variant, Image, Category
from order.models import Order, OrderItem
from store.models import Store, StoreStaff
from django.db.models import Sum, F
from customer.models import Customer

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('store_admin:dashboard')
        else:
            return render(request, 'store_admin/login.html', {'error': 'Invalid credentials'})
    return render(request, 'store_admin/login.html')

def get_current_store_for_user(user):
    # Try to get the first store where the user is owner or staff
    store = Store.objects.filter(owner=user).first()
    if not store:
        staff_link = StoreStaff.objects.filter(user=user, accepted=True).select_related('store').first()
        if staff_link:
            store = staff_link.store
    return store

@login_required
def dashboard(request):
    store = get_current_store_for_user(request.user)
    if not store:
        return render(request, 'store_admin/dashboard.html', {'error': 'No store assigned.'})
    # Sales summary
    total_sales = Order.objects.filter(store=store, status__in=['completed', 'processing']).aggregate(total=Sum('total'))['total'] or 0
    order_count = Order.objects.filter(store=store).count()
    product_count = Product.objects.filter(store=store).count()
    recent_orders = Order.objects.filter(store=store).order_by('-placed_at')[:5]

    # New: order status counts and amounts
    pending_amount = Order.objects.filter(store=store, status='pending').aggregate(total=Sum('total'))['total'] or 0
    processing_amount = Order.objects.filter(store=store, status='processing').aggregate(total=Sum('total'))['total'] or 0
    completed_count = Order.objects.filter(store=store, status='completed').count()
    processing_count = Order.objects.filter(store=store, status='processing').count()
    pending_count = Order.objects.filter(store=store, status='pending').count()
    cancelled_count = Order.objects.filter(store=store, status='cancelled').count()

    # New: recent products and customers
    recent_products = Product.objects.filter(store=store).order_by('-created_at')[:5]
    recent_customers = Customer.objects.filter(store=store).order_by('-created_at')[:5]

    return render(request, 'store_admin/dashboard.html', {
        'store': store,
        'total_sales': total_sales,
        'order_count': order_count,
        'product_count': product_count,
        'recent_orders': recent_orders,
        'pending_amount': pending_amount,
        'processing_amount': processing_amount,
        'completed_count': completed_count,
        'processing_count': processing_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'recent_products': recent_products,
        'recent_customers': recent_customers,
    })

@login_required
def product_list(request):
    store = get_current_store_for_user(request.user)
    if not store:
        return render(request, 'store_admin/product_list.html', {'error': 'No store assigned.'})
    products = Product.objects.filter(store=store).prefetch_related('variants')
    return render(request, 'store_admin/product_list.html', {'products': products, 'store': store})

@login_required
def product_edit(request, product_id=None):
    store = get_current_store_for_user(request.user)
    if not store:
        return redirect('store_admin:product_list')
    categories = Category.objects.all()
    product = None
    variants = []
    images = []
    if product_id:
        product = Product.objects.filter(id=product_id, store=store).first()
        if not product:
            return redirect('store_admin:product_list')
        variants = product.variants.all()
        images = product.images.all()
    if request.method == 'POST':
        # --- VARIANT MODAL FORM (multi-add) ---
        if request.POST.get('variant_modal_form'):
            idx = 0
            created = 0
            while True:
                name = request.POST.get(f'modal_variant_name_{idx}')
                if not name:
                    break
                sku = request.POST.get(f'modal_variant_sku_{idx}')
                default_price = request.POST.get(f'modal_variant_default_price_{idx}') or 0
                sale_price = request.POST.get(f'modal_variant_sale_price_{idx}') or None
                stock = request.POST.get(f'modal_variant_stock_{idx}') or 0
                is_on_sale = bool(request.POST.get(f'modal_variant_is_on_sale_{idx}'))
                manage_stock = bool(request.POST.get(f'modal_variant_manage_stock_{idx}'))
                Variant.objects.create(
                    product=product,
                    name=name,
                    sku=sku,
                    default_price=default_price,
                    sale_price=sale_price,
                    stock=stock,
                    is_on_sale=is_on_sale,
                    manage_stock=manage_stock,
                )
                created += 1
                idx += 1
            return redirect('store_admin:product_edit', product.id)
        # --- IMAGE MODAL FORM (multi-upload) ---
        elif request.POST.get('image_modal_form'):
            files = request.FILES.getlist('new_images')
            alt_text = request.POST.get('new_images_alt', '')
            for f in files:
                Image.objects.create(product=product, image=f, alt_text=alt_text)
            return redirect('store_admin:product_edit', product.id)
        # --- VARIANT FORM ---
        if request.POST.get('variant_form'):
            # Update/delete existing variants
            for variant in variants:
                if request.POST.get(f'variant_delete_{variant.id}'):
                    variant.delete()
                    continue
                variant.name = request.POST.get(f'variant_name_{variant.id}', variant.name)
                variant.sku = request.POST.get(f'variant_sku_{variant.id}', variant.sku)
                # Handle numeric fields safely
                default_price_val = request.POST.get(f'variant_default_price_{variant.id}')
                variant.default_price = float(default_price_val) if default_price_val not in [None, ''] else 0
                sale_price_val = request.POST.get(f'variant_sale_price_{variant.id}')
                variant.sale_price = float(sale_price_val) if sale_price_val not in [None, ''] else None
                stock_val = request.POST.get(f'variant_stock_{variant.id}')
                variant.stock = int(stock_val) if stock_val not in [None, ''] else 0
                variant.is_on_sale = bool(request.POST.get(f'variant_is_on_sale_{variant.id}'))
                variant.manage_stock = bool(request.POST.get(f'variant_manage_stock_{variant.id}'))
                variant.save()
            # Add new variant
            new_name = request.POST.get('new_variant_name')
            if new_name:
                Variant.objects.create(
                    product=product,
                    name=new_name,
                    sku=request.POST.get('new_variant_sku'),
                    default_price=request.POST.get('new_variant_default_price') or 0,
                    sale_price=request.POST.get('new_variant_sale_price') or None,
                    stock=request.POST.get('new_variant_stock') or 0,
                    is_on_sale=bool(request.POST.get('new_variant_is_on_sale')),
                    manage_stock=bool(request.POST.get('new_variant_manage_stock')),
                )
            return redirect('store_admin:product_edit', product.id)
        # --- IMAGE UPLOAD FORM ---
        elif request.POST.get('image_form'):
            new_image = request.FILES.get('new_image')
            alt_text = request.POST.get('new_image_alt', '')
            if new_image:
                Image.objects.create(product=product, image=new_image, alt_text=alt_text)
            return redirect('store_admin:product_edit', product.id)
        # --- IMAGE DELETE FORM ---
        elif request.POST.get('delete_image_id'):
            img_id = request.POST.get('delete_image_id')
            img = Image.objects.filter(id=img_id, product=product).first()
            if img:
                img.delete()
            return redirect('store_admin:product_edit', product.id)
        # --- PRODUCT FIELDS FORM (default) ---
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        status = request.POST.get('status')
        category_id = request.POST.get('category')
        category = Category.objects.filter(id=category_id).first() if category_id else None
        if product:
            product.name = name
            product.slug = slug
            product.description = description
            product.status = status
            product.category = category
            product.save()
        else:
            product = Product.objects.create(
                store=store, name=name, slug=slug, description=description, status=status, category=category
            )
        return redirect('store_admin:product_edit', product.id)
    context = {
        'product_id': product_id,
        'store': store,
        'product': product,
        'categories': categories,
        'variants': variants,
        'images': images,
    }
    return render(request, 'store_admin/product_edit.html', context)

# Customer list and detail views
@login_required
def customer_list(request):
    store = get_current_store_for_user(request.user)
    if not store:
        return render(request, 'store_admin/customer_list.html', {'error': 'No store assigned.'})
    customers = Customer.objects.filter(store=store).order_by('-created_at')
    return render(request, 'store_admin/customer_list.html', {'customers': customers, 'store': store})

@login_required
def customer_detail(request, customer_id):
    store = get_current_store_for_user(request.user)
    if not store:
        return redirect('store_admin:customer_list')
    customer = get_object_or_404(Customer, id=customer_id, store=store)
    orders = Order.objects.filter(store=store, customer=customer.user).order_by('-placed_at')
    return render(request, 'store_admin/customer_detail.html', {'customer': customer, 'orders': orders, 'store': store})

@login_required
def order_list(request):
    store = get_current_store_for_user(request.user)
    if not store:
        return render(request, 'store_admin/order_list.html', {'error': 'No store assigned.'})
    orders = Order.objects.filter(store=store).select_related('customer').order_by('-placed_at')
    return render(request, 'store_admin/order_list.html', {'orders': orders, 'store': store})

@login_required
def order_edit(request, order_id):
    store = get_current_store_for_user(request.user)
    if not store:
        return redirect('store_admin:order_list')
    order = (
        Order.objects
        .filter(id=order_id, store=store)
        .select_related('customer', 'shipping_address', 'billing_address', 'store', 'cancelled_by')
        .prefetch_related('items', 'items__variant', 'items__variant__product')
        .first()
    )
    if not order:
        return redirect('store_admin:order_list')
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Order.STATUS_CHOICES):
            order.status = status
            order.save()
        return redirect('store_admin:order_list')
    # Get all order items
    items = order.items.all()
    return render(request, 'store_admin/order_edit.html', {
        'order_id': order_id,
        'order': order,
        'store': store,
        'items': items,
    })
