from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order

@receiver(pre_save, sender=Order)
def update_order_status_on_payment(sender, instance, **kwargs):
    """
    Update order status based on payment status changes.
    """
    if not instance.pk:
        return  # New order being created
    
    try:
        old_instance = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return  # No existing order found
    
    # Check if payment status has changed
    if old_instance.payment_status != instance.payment_status:
        # If payment is marked as paid, update order status to processing
        if instance.payment_status == 'paid' and instance.status == 'pending':
            instance.status = 'processing'
        # If payment failed and order is still pending, update status
        elif instance.payment_status == 'failed' and instance.status == 'pending':
            instance.status = 'cancelled'
            # TODO: Send notification to admin about failed payment

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    Handle actions when order status changes.
    """
    if created:
        return  # Skip for new orders
    
    try:
        old_instance = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return  # No existing order found
    
    # Check if status has changed
    if old_instance.status != instance.status:
        # TODO: Send email notification about status change
        # TODO: Update inventory based on status change
        pass
