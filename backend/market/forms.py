from django import forms
from .models import Product, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["title", "category", "description", "price", "stock", "is_active"]

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "order"]
    