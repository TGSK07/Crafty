from django import forms
from .models import Product, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["title", "categoyr", "description", "price", "stock", "is_active", "created_at", "updated_at"]

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["iamge", "alt_text", "order"]
    