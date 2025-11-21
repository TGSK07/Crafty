from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.urls import reverse
from .models import OrderItem


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_item_status_change_mail(self, oid):
    """
    Send mail to Buyer whenever seller change an Order Item status changes.
    """

    try:
        item = OrderItem.objects.select_related("order__buyer", "product_seller").get(pk=oid)
    except OrderItem.DoesNotExist:
        return False
    
    order = item.order
    buyer = order.buyer
    
    # Prepare Context
    ctx = {
        "order":order,
        "item": item,
        "buyer": buyer,
        "site_name": getattr(settings, "SITE_NAME", "Crafty"),
        "logo_url": "",
        "order_url": settings.SITE_URL.rstrip("/") + reverse("buyer_order_detail", args=[order.pk]),
    }

    # Send to buyer
    subject = f"[{ctx['site_name']}] Update: Your Order # {order.pk} - {item.get_status_display}"
    html_body = render_to_string("emails/order_item_status_changed.html", ctx)
    text_body = strip_tags(html_body)
    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [buyer.email])
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send()
    except Exception as e:
        raise self.retry(exc=e)
    
    return True
