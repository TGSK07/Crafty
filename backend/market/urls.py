from django.urls import path
from .views import (
    ProductListView, ProductDeleteView, SellerProductsView, ProductCreateView, 
    ProductUpdateView, ProductDetailView, ProductImageDeleteView, CreateOrEditArtistProfileView, ArtistProfileDetailView
)

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("product/<slug:slug>", ProductDetailView.as_view(), name="product_detail"),

    # Seller's Dashboard
    path("seller/products/", SellerProductsView.as_view(), name="seller_products"),
    path("seller/products/create/", ProductCreateView.as_view(), name="product_create"),
    path("seller/products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path("seller/products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("seller/product-image/<int:pk>/delete/", ProductImageDeleteView.as_view(), name="product_image_delete"),

    path("artist/profile/", CreateOrEditArtistProfileView.as_view(), name="artist_profile_manage"),
    path("artist/<slug:slug>/", ArtistProfileDetailView.as_view(), name="artist_profile_detail"),

]

