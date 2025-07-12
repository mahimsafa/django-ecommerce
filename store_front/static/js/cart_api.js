class CartAPI {
    static getCSRFToken() {
        // Use the global csrftoken variable if available, otherwise try to get it from cookies
        if (typeof csrftoken !== 'undefined') {
            return csrftoken;
        }
        
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    static async addToCart(variantId, quantity = 1) {
        try {
            const response = await fetch('/cart/api/cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    variant_id: variantId,
                    quantity: quantity
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to add item to cart');
            }

            return data;
        } catch (error) {
            console.error('Error adding to cart:', error);
            throw error;
        }
    }

    static async updateCartItem(itemId, quantity) {
        try {
            const response = await fetch(`/cart/api/cart/items/${itemId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ quantity })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to update cart item');
            }

            return data;
        } catch (error) {
            console.error('Error updating cart item:', error);
            throw error;
        }
    }

    static async removeCartItem(itemId) {
        try {
            const response = await fetch(`/cart/api/cart/items/${itemId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to remove item from cart');
            }

            return data;
        } catch (error) {
            console.error('Error removing cart item:', error);
            throw error;
        }
    }

    static async clearCart() {
        try {
            const response = await fetch('/cart/api/cart/clear/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to clear cart');
            }

            return data;
        } catch (error) {
            console.error('Error clearing cart:', error);
            throw error;
        }
    }

    static async getCart() {
        try {
            const response = await fetch('/cart/api/cart/', {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get cart');
            }

            return data;
        } catch (error) {
            console.error('Error getting cart:', error);
            throw error;
        }
    }

    static updateCartUI(data) {
        // Update cart count in navbar
        const cartCountElements = document.querySelectorAll('.cart-count, .cart-count-badge');
        const itemCount = data.item_count || data.count || 0;
        
        cartCountElements.forEach(el => {
            el.textContent = itemCount;
            el.style.display = itemCount > 0 ? 'inline-block' : 'none';
        });

        // Update any other UI elements as needed
        const cartItemsContainer = document.querySelector('.cart-items');
        if (cartItemsContainer && data.items) {
            // Update cart items if we're on the cart page
            // This is a simplified example - you might want to implement a more robust update
            cartItemsContainer.innerHTML = ''; // Clear existing items
            // Add code to render cart items from data.items
        }

        // Update total if available
        if (data.total) {
            const totalElement = document.querySelector('.cart-total');
            if (totalElement) {
                totalElement.textContent = `$${parseFloat(data.total).toFixed(2)}`;
            }
        }
    }

    static showNotification(message, type = 'success') {
        // You can implement a toast notification system here
        // For now, we'll just use alert
        alert(message);
    }
}
