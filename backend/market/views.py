from django.shortcuts import render, get_list_or_404, redirect, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, ProductImage, ArtistProfile
from .forms import ProductForm, ProductImageForm
from django.contrib import messages
from django.db import transaction

from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden

from django.http import Http404
from django.db.models.query import QuerySet


ALLOWED_IMAGE_CONTENT_TYPES = ("image/png", "image/jpeg", "image/jpg", "image/webp")
MAX_IMAGE_SIZE = 4 * 1024 * 1024


def validate_image_file(f):
    if f.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        return False, "Unsupported file type."
    if f.size > MAX_IMAGE_SIZE:
        return False, "File too large (max 4MB)"
    return True, ""


# Create your views here.
class ProductListView(View):
    def get(self, request):
        q = request.GET.get("q", "")
        products = Product.objects.filter(is_active=True).order_by("-created_at")
        if q:
            products = products.filter(title__icontains=q)
        paginator = Paginator(products, 12)
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