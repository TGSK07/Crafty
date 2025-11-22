from django import forms
from .models import Product, ProductImage, ArtistProfile

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["title", "category", "description", "price", "stock", "is_active"]
        widgets = {
            "description":forms.Textarea(attrs={"rows":4})
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "order"]
    
class ArtistProfileForm(forms.ModelForm):
    class Meta:
        model = ArtistProfile
        fields = ["display_name", "bio", "contact_number", "city", "location_map_url", "image"]
        widgets = {
            "bio":forms.Textarea(attrs={"rows":4}),
            "display_name": forms.TextInput(attrs={"placeholder":"Your Public Name"}),
        }