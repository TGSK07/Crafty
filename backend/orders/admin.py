from django.contrib import admin
from .models import Order, OrderItem, Payment


# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "unit_price_inr", "quantity", "line_total_inr")
    fields = ("product", "unit_price_inr", "quantity", "line_total_inr")
    can_delete = False

    def line_total_inr(self, obj):
        if not obj:
            return "-"
        # format to 2 decimals
        try:
            return f"₹{obj.get_total():.2f}"
        except Exception:
            return "-"

    line_total_inr.short_description = "Line total"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "razorpay_payment_id", "amount_inr", "created_at")
    search_fields = ("razorpay_payment_id", "order__id")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ("id", "buyer", "total_amount_inr", "status", "razorpay_order_id", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("buyer__username", "razorpay_order_id")
    readonly_fields = ("created_at", )