from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Log the user in after registration
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('store_front:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})
