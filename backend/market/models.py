from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from decimal import Decimal

# Create your models here.
User = settings.AUTH_USER_MODEL

class ArtistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="artist_profile")
    display_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    contact_number = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    location_map_url = models.URLField(blank=True)
    image = models.ImageField(upload_to="artists/", blank=True, null=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.get_full_name() or self.user.username
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.display_name or self.user.username}"
            sl = slugify(base)[:120]
            count = 0
            unique = sl
            while ArtistProfile.objects.filter(slug=unique).exclude(pk=self.pk).exists():
                count += 1
                unique = f"{sl}-{count}"
            self.slug = unique
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _generate_unique_slug(self):
        base = self.title or "product"
        sl = slugify(base)[:200] or "product"
        unique = sl
        count = 0
        while Product.objects.filter(slug=unique).exclude(pk=self.pk).exists():
            count += 1
            unique = f"{sl}-{count}"
        return unique

    def save(self, *args, **kwargs):
        # populate slug if empty
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product/")
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ("order",)
    
    def __str__(self):
        return f"Image for {self.product.title}"