from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Customer, Address
from order.models import Order


@login_required
def profile_view(request):
    """Customer profile view"""
    customer = get_object_or_404(Customer, user=request.user)
    return render(request, 'customer/profile.html', {'customer': customer})


class AddressListView(LoginRequiredMixin, ListView):
    """List all addresses for the current customer"""
    model = Address
    template_name = 'customer/address_list.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)


class AddressCreateView(LoginRequiredMixin, CreateView):
    """Create a new address"""
    model = Address
    fields = [
        'address_type', 'first_name', 'last_name', 'company',
        'street_address_1', 'street_address_2', 'city',
        'state', 'postal_code', 'country', 'phone', 'is_default'
    ]
    template_name = 'customer/address_form.html'
    success_url = reverse_lazy('customer:address_list')

    def form_valid(self, form):
        form.instance.customer = self.request.user.customer_profiles.first()
        messages.success(self.request, 'Address added successfully.')
        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing address"""
    model = Address
    fields = [
        'address_type', 'first_name', 'last_name', 'company',
        'street_address_1', 'street_address_2', 'city',
        'state', 'postal_code', 'country', 'phone', 'is_default'
    ]
    template_name = 'customer/address_form.html'
    success_url = reverse_lazy('customer:address_list')

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Address updated successfully.')
        return super().form_valid(form)


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an address"""
    model = Address
    template_name = 'customer/address_confirm_delete.html'
    success_url = reverse_lazy('customer:address_list')

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Address deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def set_default_address(request, pk, address_type):
    """Set an address as default for shipping or billing"""
    address = get_object_or_404(
        Address,
        pk=pk,
        customer__user=request.user,
        address_type=address_type
    )
    
    # Set this address as default and unset others of the same type
    Address.objects.filter(
        customer=address.customer,
        address_type=address_type,
        is_default=True
    ).update(is_default=False)
    
    address.is_default = True
    address.save()
    
    messages.success(request, f'Default {address_type} address updated.')
    return redirect('customer:address_list')


class OrderHistoryView(LoginRequiredMixin, ListView):
    """Display order history for the current customer"""
    model = Order
    template_name = 'customer/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(
            customer__user=self.request.user
        ).select_related('store').order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Display order details"""
    model = Order
    template_name = 'customer/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(customer__user=self.request.user)


class AccountSettingsView(LoginRequiredMixin, UpdateView):
    """Update account settings"""
    model = Customer
    fields = ['first_name', 'last_name', 'email', 'phone']
    template_name = 'customer/account_settings.html'
    success_url = reverse_lazy('customer:profile')

    def get_object(self):
        return self.request.user.customer_profiles.first()

    def form_valid(self, form):
        messages.success(self.request, 'Account settings updated successfully.')
        return super().form_valid(form)


# API Views
from rest_framework import generics, permissions
from .serializers import AddressSerializer


class AddressListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating addresses"""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = self.request.user.customer_profiles.first()
        serializer.save(customer=customer)


class AddressRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for retrieving, updating and deleting addresses"""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)
