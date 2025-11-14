from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("user_type",)}),
    )
    list_display = ("username", "email", "first_name", "last_name", "user_type", "is_staff")
