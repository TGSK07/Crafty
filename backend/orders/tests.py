from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Order, OrderItem
from market.models import Product


User = get_user_model()

# Create your tests here.
class OrdersTestcase(TestCase):
    def setUp(self):
        # create user buyer and seller
        self.buyer = User.objects.create_user(username="buyer1", password="pass@123", user_type="buyer")
        self.seller = User.objects.create_user(username="seller1", password="pass@123", user_type="seller")

        # create product by seller
        self.product = Product.objects.create(title="P", category_id=1, seller=self.seller, price=100.00, is_active=True)
        
        # cerate order
        self.order = Order.objects.create(buyer=self.buyer, total_amount_inr=100.00, status=Order.STATUS_PAID)
        OrderItem.objects.create(order=self.order, product=self.product, unit_price_int=100.00, quantity=1)

    def test_buyer_order_list(self):
        c = Client(); c.login(username="buyer1", password="pass@123")
        res = c.get(reverse("buyer_order_list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Order")

    def test_seller_order_lsit_permission(self):
        c = Client(); c.login(username="seller1", password="pass@123")
        res = c.get(reverse("seller_order_list"))
        self.assertEqual(res.status_code, 200)
        