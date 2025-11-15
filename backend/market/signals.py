from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product
from django.utils.text import slugify
import random
import string


def unique_slugify(instance, value, slug_field_name="slug"):
    slug = slugify(value)[:200]
    Klass = instance.__class__
    original = slug
    counter = 1

    while Klass.objects.filter(**{slug_field_name: slug}).exclude(pk=instance.pk).exists():
        slug = f"{original}-{counter}"
        counter += 1
    return slug

@receiver(pre_save, sender=Product)
def set_product_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = unique_slugify(instance, instance.title)
