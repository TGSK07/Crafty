from django.shortcuts import render, get_list_or_404, redirect, get_object_or_404
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, ProductImage, ArtistProfile
from .forms import ProductForm, ProductImageForm
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model

from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView

from django.http import Http404
from django.db.models.query import QuerySet

from django.db import models
from .models import Product, ProductImage, ArtistProfile, Category

ALLOWED_IMAGE_CONTENT_TYPES = ("image/png", "image/jpeg", "image/jpg", "image/webp")
MAX_IMAGE_SIZE = 2 * 1024 * 1024

User = get_user_model()

def validate_image_file(f):
    if f.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        return False, "Unsupported file type."
    if f.size > MAX_IMAGE_SIZE:
        return False, "File too large (max 4MB)"
    return True, ""


# Create your views here.
PAGE_CACHE_TTL  = getattr(settings, "HOME_CACHE_TTL", 30)  # seconds (set to e.g. 60 in dev, 300+ in prod)

@method_decorator(cache_page(PAGE_CACHE_TTL ), name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Featured products (explicitly flagged) fallback to latest if none
        featured_qs = Product.objects.filter(is_active=True).order_by("-created_at")
        if not featured_qs.exists():
            featured_qs = Product.objects.filter(is_active=True).order_by("-created_at")

        # Latest products (limit)
        latest_qs = Product.objects.filter(is_active=True).order_by("-created_at")

        # Top artisans: ArtistProfile with product counts (prefetch/products)
        artisans_qs = ArtistProfile.objects.select_related("user").annotate(
            product_count=models.Count("user__product")
        ).order_by("-product_count", "-id")

        # Optimize product queries: select_related for seller & category, prefetch images
        featured_products = featured_qs.select_related("seller", "category").prefetch_related("images")[:6]
        latest_products = latest_qs.select_related("seller", "category").prefetch_related("images")[:8]
        top_artisans = artisans_qs[:6]

        # Optional: paginate latest products on homepage (example)
        page = self.request.GET.get("page", 1)
        paginator = Paginator(latest_products, 6)
        try:
            latest_page = paginator.page(page)
        except PageNotAnInteger:
            latest_page = paginator.page(1)
        except EmptyPage:
            latest_page = paginator.page(paginator.num_pages)

        ctx.update({
            "featured_products": featured_products,
            "trending_products": latest_page,      # page object (iterable)
            "top_artisans": top_artisans,
            # helpful meta for SEO / template
            "meta_title": "Crafty — Handmade by Local Artisans",
            "meta_description": "Discover and buy authentic handmade products from local artisans.",
        })
        return ctx
    

@method_decorator(cache_page(PAGE_CACHE_TTL), name="dispatch")
class AboutView(TemplateView):
    template_name = "static/about.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "meta_title": "About — Crafty",
            "meta_description": "Learn about Crafty — mission, values and how we support local artisans.",
            # extra context values you might want in template
            "founding_year": 2024,
            "mission": "To connect local artisans with customers who value handmade, sustainable goods."
        })
        return ctx


@method_decorator(cache_page(PAGE_CACHE_TTL), name="dispatch")
class HelpCenterView(TemplateView):
    template_name = "static/help_center.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "meta_title": "Help Center — Crafty",
            "meta_description": "Find FAQs, guides and contact info for support at Crafty.",
            "faqs": [
                {"q": "How do I place an order?", "a": "Add items to cart, checkout with Razorpay and you'll receive an order confirmation."},
                {"q": "Can I cancel an order?", "a": "Cancellations depend on order status and seller policies. Contact support with your order id."},
                {"q": "How do I become a seller?", "a": "Sign up and select seller account type, then complete your profile and create listings."},
            ]
        })
        return ctx


@method_decorator(cache_page(PAGE_CACHE_TTL), name="dispatch")
class ShippingView(TemplateView):
    template_name = "static/shipping.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "meta_title": "Shipping & Delivery — Crafty",
            "meta_description": "Shipping policies, delivery timelines and costs for Crafty orders.",
            "shipping_policies": [
                {"title": "Domestic Shipping", "text": "Standard delivery 3-7 business days depending on location and seller."},
                {"title": "Shipping Charges", "text": "Each seller sets shipping charges per product. You will see shipping at checkout."},
                {"title": "International Shipping", "text": "International shipping availability depends on the seller — check product listing."},
            ],
            "contact_email": getattr(settings, "SUPPORT_EMAIL", "support@crafty.example")
        })
        return ctx
    

class ProductListView(View):
    def get(self, request):
        q = request.GET.get("q", "")
        products = Product.objects.filter(is_active=True).order_by("-created_at")
        if q:
            products = products.filter(title__icontains=q)
        paginator = Paginator(products, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, "market/product_list.html", {"page_obj":page_obj, "q":q})
    

class ProductDetailView(View):
    def get(self, request, slug):
        product = get_list_or_404(Product, slug=slug, is_active=True)
        seller_profile = None
        # if hasattr(product.seller, "artist_profile"):
        #     seller_profile = product.seller.artist_profile
        # images = product.images.all()
        if isinstance(product, (list, tuple, QuerySet)):
            try:
                product = product[0]
            except Exception:
                raise Http404("Product not found")

        # Safely get seller profile (works even if seller or artist_profile missing)
        seller_profile = None
        seller = getattr(product, "seller", None)
        if seller:
            seller_profile = getattr(seller, "artist_profile", None)

        images = product.images.all() if hasattr(product, "images") else []
        return render(request, "market/product_detail.html", {"product":product, "seller_profile":seller_profile, "images":images})
    
class SellerProductsView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.user_type != request.user.SELLER:
            messages.error(request, "Only sellers can access the seller dashboard")
        products = Product.objects.filter(seller=request.user).order_by("-created_at")
        return render(request, "market/seller/products.html", {"products":products})
    
class ProductCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.user_type != request.user.SELLER:
            messages.error(request, "Only seller can create product.")
            return redirect("/")
        form = ProductForm()
        return render(request, "market/seller/product_form.html", {"form":form})
    
    def post(self, request):
        if request.user.user_type != request.user.SELLER:
            messages.error(request, "Only sellers can create product")
            return redirect("home")
        form = ProductForm(request.POST)
        files = request.FILES.getlist("images")
        if form.is_valid():
            with transaction.atomic():
                product = form.save(commit=False)
                product.seller = request.user
                product.save()

                for idx, f in enumerate(files):
                    ok, err = validate_image_file(f)
                    if not ok:
                        transaction.set_rollback(True)
                        messages.error(request, f"Image error: {err}")
                        return render(request, "market/seller/product_form.html", {"form":form})
                    ProductImage.objects.create(product=product, image=f, order=idx)
            messages.success(request, "Product created with images.")
            return redirect("seller_products")
            
            # product = form.save(commit=False)
            # product.seller = request.user
            # product.save()
            # messages.success(request, "Product created. You can upload inages from admin or edit it.")
            # return redirect("seller_products")
        return render(request, "market/seller/product_form.html", {"form":form})
    
class ProductUpdateView(LoginRequiredMixin, View):
    def get_product_or_404(self, pk, user):
        product_qs = Product.objects.filter(pk=pk, seller=user)
        product_obj = product_qs.first()
        if not product_obj:
            raise Http404("Product not found")
        return product_obj

    def get(self, request, pk):
        product = self.get_product_or_404(pk, request.user)
        form = ProductForm(instance=product)
        return render(request, "market/seller/product_form.html", {"form": form, "product": product})

    def post(self, request, pk):
        product = self.get_product_or_404(pk, request.user)
        form = ProductForm(request.POST, instance=product)
        files = request.FILES.getlist("images")

        # For debugging: if invalid, we will show errors (no silent failure)
        if form.is_valid():
            try:
                with transaction.atomic():
                    product = form.save()
                    # Handle new uploads (append)
                    for idx, f in enumerate(files, start=product.images.count()):
                        ok, err = validate_image_file(f)
                        if not ok:
                            # rollback and show message
                            transaction.set_rollback(True)
                            messages.error(request, f"Image error: {err}")
                            return render(request, "market/seller/product_form.html", {"form": form, "product": product})
                        ProductImage.objects.create(product=product, image=f, order=idx)
                messages.success(request, "Product updated.")
                return redirect("seller_products")
            except Exception as e:
                # unexpected server error: show message + errors in template
                messages.error(request, f"An error occurred: {str(e)}")
                # fallthrough to render form with errors
        else:
            # show validation errors
            messages.error(request, "Please fix the errors below.")
            # (form.errors will be displayed in template via {{ form.non_field_errors }} and field errors)

        return render(request, "market/seller/product_form.html", {"form": form, "product": product})

    
class ProductDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # robust retrieval
        product_qs = Product.objects.filter(pk=pk, seller=request.user)
        if isinstance(product_qs, (list, tuple, QuerySet)):
            product = product_qs.first()
        else:
            product = product_qs
        if not product:
            raise Http404("Product not found")

        # final permission check
        if product.seller != request.user:
            return HttpResponseForbidden("Not allowed")

        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("seller_products")

class ProductImageDeleteView(LoginRequiredMixin, View):
    @method_decorator(require_POST)
    def post(self, request, pk):
        img = get_object_or_404(ProductImage, pk=pk)
        if img.product.seller != request.user:
            return HttpResponseForbidden("Not Allowed")
        img.delete()
        messages.success(request, "Image removed.")
        return redirect("product_edit", pk=img.product.pk)
    
class SellerDashboardView(LoginRequiredMixin, View):
    """
    Seller dashboard: shows quick actions and counts.
    Only accessible to users with user_type == 'seller'.
    """
    def get(self, request):
        # guard: only sellers allowed
        if getattr(request.user, "user_type", None) != User.SELLER:
            messages.error(request, "Only sellers can access the seller dashboard.")
            return redirect("home")

        # product count for this seller
        products_count = Product.objects.filter(seller=request.user).count()

        # orders_count placeholder (Module 3 will replace with real data)
        orders_count = 0
        # if you have an Order model, set orders_count = Order.objects.filter(seller=request.user).count()

        context = {
            "products_count": products_count,
            "orders_count": orders_count,
        }
        return render(request, "seller/dashboard.html", context)