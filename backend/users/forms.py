from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)

    class Meta:
        model = User
        fields = Userfields = ("username", "first_name", "last_name", "email", "user_type", "password1", "password2")

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254)
