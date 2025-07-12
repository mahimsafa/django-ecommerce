document.addEventListener('DOMContentLoaded', function() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const variantId = this.dataset.variantId;
            const quantity = this.dataset.quantity || 1;
            
            // Show loading state
            const originalText = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
            
            // Send AJAX request
            const formData = new FormData();
            formData.append('quantity', quantity);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
            
            fetch(`/cart/add/${variantId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update cart count
                    updateCartCount();
                    // Show success message
                    showToast('Success', data.message, 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error', 'Failed to add item to cart', 'danger');
            })
            .finally(() => {
                // Reset button state
                this.disabled = false;
                this.innerHTML = originalText;
            });
        });
    });
    
    // Update cart count on page load
    updateCartCount();
    
    // Function to update cart count in the navbar
    function updateCartCount() {
        fetch('/cart/count/')
            .then(response => response.json())
            .then(data => {
                const cartCountBadge = document.querySelector('.cart-count');
                if (cartCountBadge) {
                    cartCountBadge.textContent = data.count || '0';
                    cartCountBadge.style.display = data.count > 0 ? 'inline-block' : 'none';
                }
            });
    }
    
    // Function to show toast messages
    function showToast(title, message, type = 'info') {
        // You can implement a toast notification system here
        // For now, we'll just use the browser's alert
        alert(`${title}: ${message}`);
    }
    
    // Function to get CSRF token from cookies
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
});
