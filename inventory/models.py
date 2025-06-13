from django.db import models
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    code = models.CharField(max_length=10, unique=True, editable=False)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    available_copies = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.code})"

class BookStatusLog(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
#        timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.book.title} - {self.status} on {self.date.date()}"

class RestockLog(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='restocks')
    quantity_added = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Restocked {self.quantity_added} of {self.book.title} on {self.date.date()}"