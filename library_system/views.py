
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from inventory.models import Book
from members.models import Member
from borrowing.models import BorrowRecord
from utils.book_status import update_book_status
from django.utils import timezone

@require_http_methods(["GET", "POST"])
def homepage(request):
    message = request.GET.get('message')
    error = request.GET.get('error')
    available_books = Book.objects.filter(available_copies__gt=0)


    if request.method == "POST":
        action = request.POST.get('action')
        member_name = request.POST.get('member_name')
        book_title = request.POST.get('book_title')

        try:
            member = Member.objects.get(full_name=member_name)
            book = Book.objects.get(title=book_title)

            # Borrow a book
            if action == "borrow":
                due_date = request.POST.get('due_date')
                if not due_date:
                    raise ValueError("Due date is required.")
                borrow = BorrowRecord.objects.create(member=member, book=book, due_date=due_date)
                update_book_status(book, "borrowed", f"Borrowed by {member.full_name}")
                message = f"Book '{book.title}' borrowed by {member.full_name}."

            # Return a book
            elif action == "return":
                record = BorrowRecord.objects.filter(member=member, book=book, return_date__isnull=True).first()
                if not record:
                    raise ValueError("No active borrow record found.")
                record.return_date = timezone.now()
                record.save()
                book.available_copies += 1
                book.save()
                update_book_status(book, "returned", f"Returned by {member.full_name}")
                message = f"Book '{book.title}' returned by {member.full_name}."

            # Report lost or damaged
            elif action == "report":
                status_type = request.POST.get('status_type')
                if status_type not in ["lost", "damaged"]:
                    raise ValueError("Select Lost or Damaged.")
                record = BorrowRecord.objects.filter(member=member, book=book, return_date__isnull=True).first()
                if not record:
                    raise ValueError("No active borrow record to report.")
                record.return_date = timezone.now()
                record.save()
                if book.available_copies > 0:
                    book.available_copies -= 1
                    book.save()
                update_book_status(book, status_type, f"{status_type.capitalize()} by {member.full_name}")
                message = f"Book '{book.title}' marked as {status_type}."

            else:
                raise ValueError("Unknown action.")

        except Member.DoesNotExist:
            error = "Member not found."
        except Book.DoesNotExist:
            error = "Book not found."
        except Exception as e:
            error = str(e)

    # Fetch available books list
    # available_books = Book.objects.filter(available_copies__gt=0)

    return render(request, 'homepage.html', {
        'available_books': available_books,
        'message': message,
        'error': error
    })