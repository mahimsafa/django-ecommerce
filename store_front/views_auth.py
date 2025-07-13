from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from customer.models import Customer
from django.views.decorators.http import require_http_methods

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Get the default store
            from store.models import Store
            default_store = Store.objects.first()
            
            if not default_store:
                # If no store exists, create one (or handle this case as needed)
                default_store = Store.objects.create(name="Default Store")
            
            # Create a Customer profile for the new user
            Customer.objects.create(
                user=user,
                store=default_store,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            auth_login(request, user)  # Log the user in after registration
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('store_front:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@require_http_methods(['GET', 'POST'])
def logout(request):
    """
    Custom logout view that handles both GET and POST requests
    and properly logs the user out.
    """
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('store_front:home')
    
    # For GET requests, show a confirmation page
    return render(request, 'registration/logout_confirm.html')
