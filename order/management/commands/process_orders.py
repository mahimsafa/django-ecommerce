from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from order.models import Order

class Command(BaseCommand):
    help = 'Process orders (abandoned carts, pending payments, etc.)'

    def handle(self, *args, **options):
        self.process_abandoned_carts()
        self.process_pending_payments()
        self.process_expired_orders()

    def process_abandoned_carts(self):
        """
        Identify and handle abandoned carts (orders that have been created but not completed).
        """
        # Find orders that are older than 1 hour but still in 'pending' status
        time_threshold = timezone.now() - timedelta(hours=1)
        abandoned_orders = Order.objects.filter(
            status='pending',
            created_at__lte=time_threshold
        )
        
        count = abandoned_orders.count()
        if count > 0:
            self.stdout.write(self.style.WARNING(
                f'Found {count} abandoned cart(s) older than 1 hour.'
            ))
            
            # TODO: Send reminder emails for abandoned carts
            # for order in abandoned_orders:
            #     send_abandoned_cart_reminder(order)
            
            self.stdout.write(self.style.SUCCESS(
                f'Processed {count} abandoned cart(s).'
            ))
        else:
            self.stdout.write('No abandoned carts found.')

    def process_pending_payments(self):
        """
        Check for orders with pending payments and update their status if needed.
        """
        # Find orders with pending payment that are older than 30 minutes
        time_threshold = timezone.now() - timedelta(minutes=30)
        pending_orders = Order.objects.filter(
            payment_status='pending',
            status='pending',
            created_at__lte=time_threshold
        )
        
        count = pending_orders.count()
        if count > 0:
            self.stdout.write(self.style.WARNING(
                f'Found {count} pending payment(s) older than 30 minutes.'
            ))
            
            # TODO: Check payment status with payment gateway
            # For now, we'll just log them
            for order in pending_orders:
                self.stdout.write(f'  - Order #{order.id} from {order.created_at}')
            
            self.stdout.write(self.style.SUCCESS(
                f'Processed {count} pending payment(s).'
            ))
        else:
            self.stdout.write('No pending payments found.')

    def process_expired_orders(self):
        """
        Handle expired orders (e.g., orders that were not paid in time).
        """
        # Find orders that are older than 24 hours and still pending payment
        time_threshold = timezone.now() - timedelta(hours=24)
        expired_orders = Order.objects.filter(
            status='pending',
            payment_status='pending',
            created_at__lte=time_threshold
        )
        
        count = expired_orders.count()
        if count > 0:
            self.stdout.write(self.style.WARNING(
                f'Found {count} expired order(s) older than 24 hours.'
            ))

            # TODO: Send cancellation email to customers
            
            # Update status to cancelled
            updated = expired_orders.update(
                status='cancelled',
                payment_status='failed',
                notes='Order cancelled automatically due to non-payment.'
            )
            
            # TODO: Send cancellation email to customers
            
            self.stdout.write(self.style.SUCCESS(
                f'Cancelled {updated} expired order(s).'
            ))
        else:
            self.stdout.write('No expired orders found.')
