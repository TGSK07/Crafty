from django.urls import path
from .views import SignUpView, LoginView, LogoutView, ProfileView
from .views import UserProfileEditView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit", UserProfileEditView.as_view(), name="edit_profile")
]
