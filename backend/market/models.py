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
    contact_number = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    image = models.ImageField(upload_to="artists/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.get_full_name() or self.user.username

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
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

    def get_price_display(self):
        return f"₹{self.price:.2f}"
    
    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug":self.slug})
    
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