from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.full_clean()
        self.email = self.email.lower()
        super().save(*args, **kwargs)
