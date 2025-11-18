from django.urls import path
from .views import (
    AddToCartView, CartView, CheckoutView, PaymentVerifyView, CartCountView, 
    BuyerOrderListView, BuyerOrderDeatilView, SellerOrderListView, SellerOrderDeatilView, SellerOrderStatusUpdateView
)

urlpatterns = [
    path("add/<int:product_id>/", AddToCartView.as_view(), name="add_to_cart"),
    path("count/", CartCountView.as_view(), name="cart_count"),
    path("", CartView.as_view(), name="cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("verify-payment/", PaymentVerifyView.as_view(), name="verify_payment"),
    
    # buyer
    path("my/", BuyerOrderListView.as_view(), name="buyer_order_list"),
    path("view/<int:pk>/", BuyerOrderDeatilView.as_view(), name="buyer_order_detail"),

    # seller
    path("seller/", SellerOrderListView.as_view(), name="seller_order_list"),
    path("seller/view/<int:pk>/", SellerOrderDeatilView.as_view(), name="seller_order_detail"),
    path("selelr/<int:pk>/update-status", SellerOrderStatusUpdateView.as_view(), name="seller_order_update_status"),
]
