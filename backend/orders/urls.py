from django.urls import path
from .views import AddToCartView, CartView, CheckoutView, PaymentVerifyView, CartCountView

urlpatterns = [
    path("add/<int:product_id>/", AddToCartView.as_view(), name="add_to_cart"),
    path("count/", CartCountView.as_view(), name="cart_count"),
    path("", CartView.as_view(), name="cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("verify-payment/", PaymentVerifyView.as_view(), name="verify_payment"),
]
