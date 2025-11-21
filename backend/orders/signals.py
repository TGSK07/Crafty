from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderItem, OrderStatusLog
from .tasks import send_item_status_change_mail

@receiver(post_save, sender=OrderItem)
def order_item_post_save(sender, instance: OrderItem, created, **kwargs):
    """
    Only trigger when status changed or cerated with status not default.
    """
    if created:
        pass

    try:
        send_item_status_change_mail(instance.pk)
    except Exception:
        pass