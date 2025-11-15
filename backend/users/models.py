from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    SELLER = 'seller'
    BUYER = 'buyer'
    USER_TYPE_CHOICES = [
        (BUYER, "Buyer"),
        (SELLER, "Seller") 
    ]

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default=BUYER)

    @property
    def initials(self):
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        if first and last:
            return f"{first[0].upper()} {last[0].upper()}"
        if first:
            return first[0].upper()
        
        if last:
            return last[0].upper()
        return (self.username or "").strip()[:2].upper()
    