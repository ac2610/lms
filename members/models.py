
from django.db import models

class Member(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    membership_id = models.CharField(max_length=10, unique=True, editable=False)
    joined_date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.membership_id:
            from uuid import uuid4
            self.membership_id = uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.membership_id})"
