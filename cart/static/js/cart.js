document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart functionality
    initCart();
    
    // Update cart count on page load
    updateCartCount();
});

// Initialize cart functionality
function initCart() {
    // Handle quantity changes
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const itemId = this.dataset.itemId;
            const quantity = parseInt(this.value);
            
            if (quantity > 0) {
                updateCartItem(itemId, quantity);
            }
        });
    });
    
    // Handle remove item buttons
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            if (confirm('Are you sure you want to remove this item from your cart?')) {
                removeCartItem(itemId);
            }
        });
    });
    
    // Handle clear cart button
    const clearCartBtn = document.getElementById('clear-cart');
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to clear your cart?')) {
                clearCart();
            }
        });
    }
}

// Update cart count in the navbar
async function updateCartCount() {
    try {
        const response = await fetch('/cart/count/');
        const data = await response.json();
        
        // Update cart count in navbar
        const cartCountElements = document.querySelectorAll('.cart-count, .cart-count-badge');
        cartCountElements.forEach(el => {
            el.textContent = data.count || 0;
            el.style.display = data.count > 0 ? 'inline-block' : 'none';
        });
    } catch (error) {
        console.error('Error updating cart count:', error);
    }
}

// Update cart item quantity
async function updateCartItem(itemId, quantity) {
    try {
        const formData = new FormData();
        formData.append('quantity', quantity);
        formData.append('action', 'update');
        
        const response = await fetch(`/cart/update/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        if (response.ok) {
            // Reload the page to show updated cart
            window.location.reload();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to update cart');
        }
    } catch (error) {
        console.error('Error updating cart item:', error);
        alert('An error occurred while updating your cart');
    }
}

// Remove item from cart
async function removeCartItem(itemId) {
    try {
        const formData = new FormData();
        formData.append('action', 'remove');
        
        const response = await fetch(`/cart/update/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        if (response.ok) {
            // Reload the page to show updated cart
            window.location.reload();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to remove item');
        }
    } catch (error) {
        console.error('Error removing cart item:', error);
        alert('An error occurred while removing the item');
    }
}

// Clear the entire cart
async function clearCart() {
    try {
        const response = await fetch('/cart/clear/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            // Reload the page to show empty cart
            window.location.reload();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to clear cart');
        }
    } catch (error) {
        console.error('Error clearing cart:', error);
        alert('An error occurred while clearing your cart');
    }
}

// Helper function to get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
