from django.shortcuts import render, get_list_or_404, redirect
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
        product = get_list_or_404(Product, slug=slug, is_ative=True)
        seller_profile = None
        if hasattr(product.seller, "artist_profile"):
            seller_profile = product.seller.artist_profile
        images = product.images.all()
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
    def get(self, request, pk):
        product = get_list_or_404(Product, pk=pk, seller=request.user)
        form = ProductForm(instance=product)
        return render(request, "market/seller/product_form.html", {"form":form, "product":product})

    def post(self, request, pk):
        product = get_list_or_404(Product, pk=pk, seller=request.user)
        form = ProductForm(request.POST, instance=product)
        files = request.FILES.getlist("images")
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
                for idx, f in enumerate(files, start=product.iamges.count()):
                    ok, err = validate_image_file(f)
                    if not ok:
                        transaction.set_rollback(True)
                        messages.error(request, f"Image error: {err}")
                        return render(request, "market/seller/product_form.html", {"form":form, "product":product})
                    ProductImage.objects.create(product=product, image=f, order=idx)    
            messages.success(request, "Product updated.")
            return redirect("seller_products")      
        
            # form.save()
            # messages.success(request, "Product updated.")
            # return redirect("seller_products")
        return render(request, "market/seller/product_form.html", {"form":form, "product":product})
    
class ProductDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_list_or_404(Product, pk=pk, seller=request.user)
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("seller_products")

class ProductImageDeleteView(LoginRequiredMixin, View):
    @method_decorator(require_POST)
    def post(self, request, pk):
        img = get_list_or_404(ProductImage, pk=pk)
        if img.product.seller != request.user:
            return HttpResponseForbidden("Not Allowed")
        img.delete()
        messages.success(request, "Image removed.")
        return redirect("product_edit", pk=img.product.pk)