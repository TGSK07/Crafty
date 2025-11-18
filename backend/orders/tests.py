# backend/orders/tests.py
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Order, OrderItem
from market.models import Product, Category

User = get_user_model()

class TestOrdersBasic(TestCase):
    def setUp(self):
        # create a Category
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        # create users
        self.buyer = User.objects.create_user(username='buyer1', password='pass', user_type='buyer')
        self.seller = User.objects.create_user(username='seller1', password='pass', user_type='seller')
        # create product
        self.product = Product.objects.create(
            title='P',
            category=self.category,
            seller=self.seller,
            price=Decimal('100.00'),
            is_active=True,
            slug="test-product"
        )
        # create order & item
        self.order = Order.objects.create(buyer=self.buyer, total_amount_inr=Decimal('100.00'), status=Order.STATUS_PAID)
        OrderItem.objects.create(order=self.order, product=self.product, unit_price_inr=Decimal('100.00'), quantity=1)

    def test_buyer_order_list(self):
        c = Client()
        logged = c.login(username='buyer1', password='pass')
        self.assertTrue(logged, "Login failed for buyer1 in test setup")

        resp = c.get(reverse('buyer_order_list'))
        # view returned OK
        self.assertEqual(resp.status_code, 200)

        # Find orders queryset from one of the possible context keys
        ctx = resp.context
        orders_qs = None
        for key in ("orders", "order_list", "object_list"):
            if key in ctx:
                orders_qs = ctx[key]
                break
        self.assertIsNotNone(orders_qs, f"Orders queryset not found in response.context keys: {list(ctx.keys())}")

        # orders_qs may be a Page (has .object_list) or QuerySet
        order_iterable = getattr(orders_qs, "object_list", orders_qs)
        order_ids = [o.pk for o in order_iterable]
        self.assertIn(self.order.pk, order_ids, f"Order {self.order.pk} not found in buyer orders list (found {order_ids})")

    def test_seller_order_list_permission(self):
        c = Client()
        logged = c.login(username='seller1', password='pass')
        self.assertTrue(logged, "Login failed for seller1 in test setup")
        resp = c.get(reverse('seller_order_list'))
        self.assertEqual(resp.status_code, 200)

        # ensure seller sees orders that include their products
        ctx = resp.context
        orders_qs = None
        for key in ("orders", "order_list", "object_list"):
            if key in ctx:
                orders_qs = ctx[key]
                break
        self.assertIsNotNone(orders_qs, f"Orders queryset not found in response.context keys: {list(ctx.keys())}")
        order_iterable = getattr(orders_qs, "object_list", orders_qs)
        order_ids = [o.pk for o in order_iterable]
        self.assertIn(self.order.pk, order_ids)
