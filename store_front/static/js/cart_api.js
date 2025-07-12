class CartAPI {
    static getCSRFToken() {
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
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
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
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
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
                    'X-Requested-With': 'XMLHttpRequest'
                }
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
        cartCountElements.forEach(el => {
            el.textContent = data.item_count || 0;
            el.style.display = data.item_count > 0 ? 'inline-block' : 'none';
        });

        // You can add more UI updates here as needed
    }

    static showNotification(message, type = 'success') {
        // You can implement a toast notification system here
        // For now, we'll just use alert
        alert(message);
    }
}
