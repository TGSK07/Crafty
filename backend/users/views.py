from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.views import View
from .forms import SignUpForm, LoginForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from .forms import UserProfileForm
from django.contrib import messages
from django.urls import reverse



# Create your views here.
class SignUpView(View):
    template_name = "auth/signup.html"

    def get(self, request):
        form = SignUpForm()
        return render(request, self.template_name, {"form":form})
    
    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            login(request, user)

            if user.user_type == User.SELLER:
                return redirect("seller_dashboard")
            return redirect("/")
        return render(request, self.template_name, {"form":form})
    
class LoginView(View):
    template_name = "auth/login.html"

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {"form":form})
    
    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
        return render(request, self.template_name, {"form":form})

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("/")
    
class ProfileView(LoginRequiredMixin, View):
    template_name = "auth/profile.html"

    def get(self, request):
        return render(request, self.template_name)
    
class UserProfileEditView(LoginRequiredMixin, View):
    template_name = "auth/edit_profile.html"

    def get(self, request):
        user = request.user
        form = UserProfileForm(instance=user, current_user=user)
        return render(request, self.template_name, {"form": form, "user_obj": user})

    def post(self, request):
        user = request.user
        form = UserProfileForm(request.POST, instance=user, current_user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect(reverse("profile"))
        else:
            messages.error(request, "Please fix the errors below.")
        return render(request, self.template_name, {"form": form, "user_obj": user})