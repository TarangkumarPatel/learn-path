from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    name = models.CharField(max_length=150, blank=True)

    @property
    def display_name(self):
        if self.name:
            return self.name
        if self.first_name:
            return self.first_name
        return self.username

    def __str__(self):
        return self.display_name
