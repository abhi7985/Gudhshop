from django.db import models
from django.contrib.auth.models import User



class DeliveryPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


