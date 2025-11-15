from django.contrib import admin
from .models import ArtistProfile, Category, Product, ProductImage


# Register your models here.

@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "city", "contact_number")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":("name",)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "price", "is_active", "created_at", "updated_at")
    prepopulated_fields = {"slug":("title",)}
    inlines = [ProductImageInline]