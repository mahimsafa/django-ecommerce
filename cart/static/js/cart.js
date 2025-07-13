document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart functionality
    initCart();
    
    // Update cart count on page load
    updateCartCount();
    
    // Set up event delegation for add to cart buttons
    document.body.addEventListener('click', function(e) {
        // Handle add to cart button clicks
        if (e.target.closest('.add-to-cart')) {
            e.preventDefault();
            const button = e.target.closest('.add-to-cart');
            const variantId = button.dataset.variantId;
            const quantity = button.closest('form')?.querySelector('input[name="quantity"]')?.value || 1;
            
            addToCart(variantId, quantity);
        }
    });
});

// Initialize cart functionality
function initCart() {
    // Handle quantity changes with debounce
    document.querySelectorAll('.quantity-input').forEach(input => {
        let debounceTimer;
        
        input.addEventListener('change', function() {
            const itemId = this.dataset.itemId;
            const variantId = this.dataset.variantId;
            let quantity = parseInt(this.value);
            const maxQuantity = parseInt(this.max) || 99;
            
            // Validate quantity
            if (isNaN(quantity) || quantity < 1) {
                quantity = 1;
                this.value = 1;
            } else if (quantity > maxQuantity) {
                quantity = maxQuantity;
                this.value = maxQuantity;
                showToast(`Maximum available quantity is ${maxQuantity}`, 'warning');
            }
            
            // Debounce to prevent rapid firing
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                updateCartItem(itemId, quantity, variantId);
            }, 500);
        });
        
        // Prevent form submission on Enter
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur(); // Triggers the change event
            }
        });
    });
    
    // Handle remove item buttons
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            const variantId = this.dataset.variantId;
            
            // Show confirmation dialog
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            const confirmBtn = document.getElementById('confirmRemoveBtn');
            
            // Set up one-time event listener
            const confirmHandler = () => {
                removeCartItem(itemId, variantId);
                confirmBtn.removeEventListener('click', confirmHandler);
                modal.hide();
            };
            
            confirmBtn.addEventListener('click', confirmHandler);
            modal.show();
        });
    });
    
    // Handle clear cart button
    const clearCartBtn = document.getElementById('clear-cart');
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show confirmation dialog
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            const confirmBtn = document.getElementById('confirmRemoveBtn');
            
            // Update modal content
            document.getElementById('modalTitle').textContent = 'Clear Cart';
            document.getElementById('modalBody').textContent = 'Are you sure you want to remove all items from your cart?';
            
            // Set up one-time event listener
            const confirmHandler = () => {
                clearCart();
                confirmBtn.removeEventListener('click', confirmHandler);
                modal.hide();
            };
            
            confirmBtn.addEventListener('click', confirmHandler);
            modal.show();
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
async function updateCartItem(itemId, quantity, variantId = null) {
    try {
        // Show loading state
        const input = document.querySelector(`.quantity-input[data-item-id="${itemId}"]`);
        if (input) {
            input.disabled = true;
            input.classList.add('disabled');
        }
        
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
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Update the UI without reloading
            updateCartItemUI(itemId, data);
            updateCartTotals(data.cart_total, data.item_count);
            showToast('Cart updated successfully', 'success');
        } else {
            const errorMsg = data.error || 'Failed to update cart';
            showToast(errorMsg, 'error');
            
            // Revert the input value if there was an error
            if (input && data.original_quantity) {
                input.value = data.original_quantity;
            }
        }
    } catch (error) {
        console.error('Error updating cart item:', error);
        showToast('An error occurred while updating your cart', 'error');
    } finally {
        // Re-enable input
        if (input) {
            input.disabled = false;
            input.classList.remove('disabled');
        }
    }
}

// Update the UI for a single cart item
function updateCartItemUI(itemId, data) {
    const itemRow = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
    if (!itemRow) return;
    
    // Update quantity input
    const quantityInput = itemRow.querySelector('.quantity-input');
    if (quantityInput) {
        quantityInput.value = data.quantity;
    }
    
    // Update subtotal
    const subtotalElement = itemRow.querySelector('.item-subtotal');
    if (subtotalElement) {
        subtotalElement.textContent = `$${parseFloat(data.subtotal).toFixed(2)}`;
    }
    
    // Update any other relevant UI elements
    const availabilityBadge = itemRow.querySelector('.availability-badge');
    if (availabilityBadge && data.in_stock !== undefined) {
        if (data.in_stock) {
            availabilityBadge.className = 'badge bg-success availability-badge';
            availabilityBadge.textContent = 'In Stock';
        } else {
            availabilityBadge.className = 'badge bg-warning text-dark availability-badge';
            availabilityBadge.textContent = 'Low Stock';
        }
    }
}

// Update cart totals in the UI
function updateCartTotals(total, itemCount) {
    // Update cart total
    const totalElements = document.querySelectorAll('.cart-total, .order-total-amount');
    totalElements.forEach(el => {
        el.textContent = `$${parseFloat(total).toFixed(2)}`;
    });
    
    // Update item count
    const countElements = document.querySelectorAll('.cart-count, .cart-item-count');
    countElements.forEach(el => {
        el.textContent = itemCount;
        el.style.display = itemCount > 0 ? 'inline-block' : 'none';
    });
}

// Add item to cart
async function addToCart(variantId, quantity) {
    try {
        const formData = new FormData();
        formData.append('quantity', quantity);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        const response = await fetch(`/cart/add/${variantId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            body: formData,
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Update cart count
            await updateCartCount();
            
            // Show success message with product name if available
            const productName = document.querySelector(`[data-variant-id="${variantId}"]`)?.dataset.productName || 'Item';
            showToast(`${productName} added to cart`, 'success');
            
            // Update any mini-cart if present
            updateMiniCart();
        } else {
            showToast(data.message || 'Failed to add item to cart', 'error');
        }
    } catch (error) {
        console.error('Error adding to cart:', error);
        showToast('Error adding item to cart. Please try again.', 'error');
    }
}

// Remove item from cart
async function removeCartItem(itemId, variantId = null) {
    try {
        // Show loading state
        const removeButton = document.querySelector(`.remove-item[data-item-id="${itemId}"]`);
        if (removeButton) {
            const originalText = removeButton.innerHTML;
            removeButton.disabled = true;
            removeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Removing...';
            
            const response = await fetch(`/cart/update/${itemId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams({
                    'action': 'remove'
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Remove the item row from the UI
                const itemRow = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
                if (itemRow) {
                    // Add fade out animation
                    itemRow.style.transition = 'opacity 0.3s ease';
                    itemRow.style.opacity = '0';
                    
                    // Remove the row after animation completes
                    setTimeout(() => {
                        itemRow.remove();
                        
                        // Update cart totals
                        updateCartTotals(data.cart_total, data.item_count);
                        
                        // Show empty cart message if no items left
                        if (data.item_count === 0) {
                            showEmptyCart();
                        }
                    }, 300);
                }
                
                showToast('Item removed from cart', 'success');
            } else {
                const errorMsg = data.error || 'Failed to remove item';
                showToast(errorMsg, 'error');
            }
            
            // Re-enable button
            removeButton.disabled = false;
            removeButton.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error removing cart item:', error);
        showToast('An error occurred while removing the item', 'error');
        
        // Re-enable button on error
        if (removeButton) {
            removeButton.disabled = false;
            removeButton.innerHTML = originalText;
        }
    }
}

// Show empty cart message
function showEmptyCart() {
    const cartContainer = document.querySelector('.cart-container');
    if (cartContainer) {
        cartContainer.innerHTML = `
            <div class="empty-cart text-center py-5">
                <i class="fas fa-shopping-cart fa-4x text-muted mb-4"></i>
                <h3>Your cart is empty</h3>
                <p class="text-muted">Browse our products and add some items to your cart</p>
                <a href="/" class="btn btn-primary mt-3">
                    <i class="fas fa-arrow-left me-2"></i> Continue Shopping
                </a>
            </div>
        `;
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

// Update mini-cart if present on the page
async function updateMiniCart() {
    try {
        const miniCart = document.querySelector('.mini-cart');
        if (!miniCart) return;
        
        const response = await fetch('/cart/view/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, 'text/html');
            const miniCartContent = doc.querySelector('.mini-cart-content');
            
            if (miniCartContent) {
                miniCart.querySelector('.mini-cart-content').innerHTML = miniCartContent.innerHTML;
            }
        }
    } catch (error) {
        console.error('Error updating mini-cart:', error);
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Check if toast container exists, if not create it
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
    
    // Add click handler to close button
    const closeButton = toast.querySelector('.btn-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
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
