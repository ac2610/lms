from django.db import models
from inventory.models import Book
from members.models import Member
from django.utils import timezone

class BorrowRecord(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='borrowed_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    borrow_date = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    returned = models.BooleanField(default=False)
    penalty_incurred = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.member.full_name} borrowed {self.book.title}"

    def is_overdue(self):
        return not self.returned and timezone.now().date() > self.due_date
