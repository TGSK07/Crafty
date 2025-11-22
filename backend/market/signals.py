from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Product, ArtistProfile
from orders.models import OrderItem, Order


@receiver(pre_save, sender=ArtistProfile)
def artistprofile_generate_slug(sender, instance, **kwargs):
    if not instance.slug:
        base = instance.display_name or instance.user.username
        sl = slugify(base)[:120]
        unique = sl
        count = 0

        while ArtistProfile.objects.filter(slug=unique).exclude(pk=instance.pk).exists():
            count += 1
            unique = f"{sl}-{count}"

        instance.slug = unique


@receiver(pre_save, sender=Product)
def product_generate_slug(sender, instance, **kwargs):
    if not instance.slug:
        base = instance.title
        sl = slugify(base)[:120]
        unique = sl
        count = 0

        while Product.objects.filter(slug=unique).exclude(pk=instance.pk).exists():
            count += 1
            unique = f"{sl}-{count}"

        instance.slug = unique



@receiver(post_save, sender=Product.seller.field.model)
def create_artist_profile(sender, instance, created, **kwargs):
    """
    If a new seller signs up, automatically create an ArtistProfile.
    Does nothing for non-seller accounts.
    """
    if created and getattr(instance, "user_type", None) == "seller":
        ArtistProfile.objects.get_or_create(
            user=instance,
            defaults={"display_name": instance.username}
        )



@receiver(post_save, sender=OrderItem)
def recalc_order_status(sender, instance, **kwargs):
    order = instance.order

    # Fetch all item statuses
    statuses = list(order.items.values_list("status", flat=True))

    # Priority based logic
    if all(s == "delivered" for s in statuses):
        order.status = "delivered"

    elif all(s in ("delivered", "cancelled") for s in statuses):
        # Mixed delivered + cancelled → treat as delivered
        order.status = "delivered"

    elif any(s == "shipped" for s in statuses):
        order.status = "shipped"

    elif any(s == "processing" for s in statuses):
        order.status = "processing"

    else:
        order.status = "pending"

    order.save(update_fields=["status", "updated_at"])
