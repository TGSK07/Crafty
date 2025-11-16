import os, hmac, hashlib, json, razorpay, traceback

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin

from .cart import add_to_cart, get_cart, cart_items_and_total, set_quantity, remove_from_cart, clear_cart, cart_total_quantity
from .models import Order, OrderItem, Payment

# Razorpay config
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID") or settings.RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET") or settings.RAZORPAY_KEY_SECRET
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Create your views here.
class AddToCartView(View):
    def post(self, request, product_id):
        qty = int(request.POST.get("qty", 1))
        add_to_cart(request.session, product_id, qty)
        total_qty = cart_total_quantity(request.session)

        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if is_ajax:
            return JsonResponse({"success": True, "count":total_qty})
        
        messages.success(request, "Added to cart.")
        return redirect("cart")

class CartCountView(View):
    def get(self, request):
        total_qty = cart_total_quantity(request.session)
        return JsonResponse({"count": total_qty})

class CartView(View):
    def get(self, request):
        items, total = cart_items_and_total(request.session)
        return render(request, "cart.html", {"items":items, "total":total})
    
    def post(self, request):
        # update quantities or remove
        action = request.POST.get("action")
        pid = request.POST.get("product_id")
        if action == "set":
            qty = int(request.POST.get("qty", 1))
            set_quantity(request.session, pid, qty)
        elif action == "remove":
            remove_from_cart(request.session, pid)
        
        # updated = False
        for k, v in request.POST.items():
            if k.startswith("qty_"):
                try:
                    product_id = k.split("_", 1)[1]
                    qty = int(v)
                    set_quantity(request.session, product_id, qty)
                    # updated = True
                except Exception as e:
                    print("ERROR:", str())
        
        # if updated:
        #     return redirect("cart")

        return redirect("cart")

class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        # shwo checkout page with order summary
        items, total = cart_items_and_total(request.session)
        if not items:
            messages.error(request, "Your cart is empty.")
            return redirect("product_list")
        
        return render(request, "checkout.html", {"items":items, "total":total, "razorpay_key_id":RAZORPAY_KEY_ID})

    def post(self, request):
        try:
            # create an Order and a Razorpay order
            items, total = cart_items_and_total(request.session)
            if not items:
                return JsonResponse({"error": "Cart is empty"}, status=400)
            
            # create order instance
            order = Order.objects.create(buyer=request.user, total_amount_inr=total, status=Order.STATUS_PENDING)
            for item in items:
                OrderItem.objects.create(order=order, product=item["product"], unit_price_inr=item["unit_price_inr"], quantity=item["quantity"])

            # create razorpay order
            razor_amount = int(float(total)*100)
            razor_order = client.order.create(dict(amount=razor_amount, currency="INR", receipt=f"order_{order.pk}", payment_capture=1))
            order.razorpay_order_id = razor_order.get("id")
            order.save()

            data = {
                "razorpay_order_id": order.razorpay_order_id,
                "order_id": order.pk,
                "amount": razor_amount,
                "currency": "INR",
                "razorpay_key_id": RAZORPAY_KEY_ID,
            }

            return JsonResponse(data)

        except Exception as e:
            traceback.print_exc()

            try:
                if 'order' in locals() and isinstance(order, Order) and order.status==Order.STATUS_PENDING:
                    order.delete()
            except Exception:
                pass

            return JsonResponse({"error": "Could not create order", "details":str(e)}, status=500)
    
class PaymentVerifyView(LoginRequiredMixin, View):
    def post(self, request):

        payload = json.loads(request.body.decode("utf-8"))
        razorpay_payment_id = payload.get("razorpay_payment_id")
        razorpay_order_id = payload.get("razorpay_order_id")
        razorpay_signature = payload.get("razorpay_signature")
        order_id = payload.get("order_id")

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, order_id]):
            return HttpResponseForbidden("Signature verification failed.")
        
        # verify signature
        generated_signature = hmac.new(RAZORPAY_KEY_SECRET.encode(), (razorpay_order_id + "|" + razorpay_payment_id).encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(generated_signature, razorpay_signature):
            return HttpResponseForbidden("Signature verification failed.")
        
        # get order and verify the amount
        order = get_object_or_404(Order, pk=order_id, razorpay_order_id=razorpay_order_id)
        try:
            payment_data  = client.payment.fetch(razorpay_payment_id)
            paid_amount = int(payment_data.get("amount", 0))/100

        except Exception:
            paid_amount = None
        
        if paid_amount is not None and paid_amount != order.total_amount_inr:
            return HttpResponseForbidden("Amount Mismatch") # amounts mismatch - suspicious
        
        Payment.objects.create(order=order, razorpay_payment_id=razorpay_payment_id, razorpay_signature=razorpay_signature, amount_inr=paid_amount or order.total_amount_inr)
        order.status = Order.STATUS_PAID
        order.save()

        clear_cart(request.session) # clear session cart
        
        return JsonResponse({"status":"ok", "order_id":order.pk})
    