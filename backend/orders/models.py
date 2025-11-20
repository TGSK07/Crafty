from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

User = settings.AUTH_USER_MODEL

# Create your models here.
class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders", null=True, blank=True)
    total_amount_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.pk} - {self.get_status_display()}"
    
    def recalc_status_from_items(self):
        '''
        Aggregate order status from related OrderItem statuses:
        - If any item is cancelled and all others cancelled -> order cancelled
        - If all items delivered -> delivered
        - If any item shipped and none pending/processing -> shipped
        - If any item processing -> processing
        Otherwise leave as paid/pending depending.
        '''

        items = list(self.items.all())
        if not items: return
        statuses = {item.status for item in items}
        if statuses <= {OrderItem.STATUS_CANCELLED}:
            new = Order.STATUS_CANCELLED
        elif statuses == {OrderItem.STATUS_DELIVERED}:
            new = Order.STATUS_DELIVERED
        elif OrderItem.STATUS_SHIPPED in statuses and not (OrderItem.STATUS_PROCESSING in statuses):
            new = Order.STATUS_SHIPPED
        elif OrderItem.STATUS_PROCESSING in statuses:
            new = Order.STATUS_PROCESSING
        elif self.status == Order.STATUS_PENDING:
            new = Order.STATUS_PENDING
        else:
            new = self.status
        
        if new != self.status:
            self.status = new 
            self.save()


class OrderItem(models.Model):    
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("market.Product", on_delete=models.SET_NULL, null=True)
    unit_price_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSING)

    def get_total(self):
        return self.unit_price_inr * self.quantity
    
    def __str__(self):
        return f"{self.product} x {self.quantity}"
    
class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, related_name="status_logs", on_delete=models.CASCADE)
    item = models.models.ForeignKey(OrderItem, related_name="status_logs", null=True, blank=True, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    note = models.CharField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    razorpay_payment_id = models.CharField(max_length=200)
    razorpay_signature = models.CharField(max_length=300)
    amount_inr = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.razorpay_payment_id} for Order {self.order.pk}"