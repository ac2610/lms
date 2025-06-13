from inventory.models import BookStatusLog, Book
from django.utils import timezone
from django.db import transaction

def update_book_status(book: Book, status: str, notes: str = ""):
    VALID_STATUSES = ["borrowed", "returned", "lost", "damaged"]

    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'")

    with transaction.atomic():
        # Log the status change
        BookStatusLog.objects.create(
            book=book,
            status=status,
            date=timezone.now(),
            notes=notes,
        )

        # Update available copies based on the status
        if status == "borrowed":
            if book.available_copies <= 0:
                raise ValueError("No available copies to borrow.")
            book.available_copies -= 1
        elif status in ["returned", "restocked"]:
            book.available_copies += 1
        elif status in ["lost", "damaged"]:
            raise ValueError("Book marked as " + status )
            # book.available_copies -= 1

        book.save()
