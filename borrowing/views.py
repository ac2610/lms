# Django imports
from datetime import date
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# DRF imports
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# App-specific imports
from borrowing.models import BorrowRecord
from inventory.models import Book, BookStatusLog
from members.models import Member
from utils.book_status import update_book_status


    
    
@api_view(['POST'])
def borrow_book(request):
    
    try:
        member_name = request.data.get('member_name')
        book_title = request.data.get('book_title')
        print("[DEBUG] BorrowBook called for:", book_title, "by member:", member_name)
        due_date = request.data.get('due_date')
        if not (member_name and book_title and due_date):
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        member = Member.objects.get(full_name=member_name)
        book = Book.objects.get(title=book_title)

        if BorrowRecord.objects.filter(member=member, book=book, return_date__isnull=True).exists():
            return Response({"error": "You already have this book borrowed."}, status=status.HTTP_400_BAD_REQUEST)

        print(f"BEFORE Borrow: {book.available_copies}")
        
        # Only block if no copies available
        if book.available_copies < 1:
            return Response({"error": f"'{book.title}' is out of stock."}, status=status.HTTP_400_BAD_REQUEST)


        print("[DEBUG] AFTER decrement:", book.available_copies)
        print(f"AFTER Borrow and save: {book.available_copies}")

       
        BorrowRecord.objects.create(member=member, book=book, due_date=due_date)
        update_book_status(book, "borrowed", f"Borrowed by {member.full_name}")
        print("[DEBUG RESPONSE]: Sending new_available =", book.available_copies)

        return Response({"message": f"Book '{book.title}' successfully borrowed by {member.full_name}.", 
                        "book_title": book.title,
                        "new_available": book.available_copies
    },
                        status=status.HTTP_200_OK)

    except Member.DoesNotExist:
        return Response({"error": "Member not found."}, status=status.HTTP_404_NOT_FOUND)
    except Book.DoesNotExist:
        return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def return_book(request):
    try:
        member_name = request.data.get('member_name')
        book_title = request.data.get('book_title')
        if not (member_name and book_title):
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        member = Member.objects.get(full_name=member_name)
        book = Book.objects.get(title=book_title)

        borrow_record = BorrowRecord.objects.filter(member=member, book=book, return_date__isnull=True).first()
        if not borrow_record:
            return Response({"error": "No active borrowing record found."}, status=status.HTTP_404_NOT_FOUND)

        borrow_record.return_date = timezone.now()
        borrow_record.save()

        # book.available_copies += 1
        # book.save()
        update_book_status(book, 'returned', f"Returned by {member.full_name}")

        return Response({
            "message": f"Book '{book.title}' returned successfully by {member.full_name}.",
            "book_title": book.title,
            "new_available": book.available_copies
        }, status=status.HTTP_200_OK)

    except Member.DoesNotExist:
        return Response({"error": "Member not found."}, status=status.HTTP_404_NOT_FOUND)
    except Book.DoesNotExist:
        return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def lost_or_damaged_book(request):
    try:
        member_name = request.data.get('member_name')
        book_title = request.data.get('book_title')
        status_type = request.data.get('status_type')
        if status_type not in ["lost", "damaged"]:
            return Response({"error": "Invalid status type; must be 'lost' or 'damaged'."}, status=status.HTTP_400_BAD_REQUEST)

        member = Member.objects.get(full_name=member_name)
        book = Book.objects.get(title=book_title)

        borrow_record = BorrowRecord.objects.filter(member=member, book=book, return_date__isnull=True).first()
        if not borrow_record:
            return Response({"error": "No active borrowing record found."}, status=status.HTTP_404_NOT_FOUND)

        # borrow_record.return_date = timezone.now()
        # borrow_record.save()

        if status_type == "lost":
            update_book_status(book, "lost", f"Marked lost by {member.full_name}")
        elif status_type == "damaged":
            update_book_status(book, "damaged", f"Marked damaged by {member.full_name}")
        # handle 'damaged'
        # book.available_copies += 1
        
        # book.save()
        
        # after update_book_status...
        return Response({
            "message": f"Book '{book.title}' marked as {status_type} by {member.full_name}.",
            "book_title": book.title,
            "new_available": book.available_copies
        }, status=status.HTTP_200_OK)


    except Member.DoesNotExist:
        return Response({"error": "Member not found."}, status=status.HTTP_404_NOT_FOUND)
    except Book.DoesNotExist:
        return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def book_detail_view(request):
    book_title = request.GET.get('title')
    
    if not book_title:
        return render(request, 'book_detail.html', {'error': 'Book title is required.'})

    try:
        book = Book.objects.get(title=book_title)
    except Book.DoesNotExist:
        return render(request, 'book_detail.html', {'error': 'Book not found.'})

    borrow_history = BorrowRecord.objects.filter(book=book).select_related('member').order_by('-borrow_date')

    return render(request, 'book_detail.html', {
        "book": book,
        "borrow_history": borrow_history,
        "today": date.today()
    })




# @api_view(['GET'])
# def member_borrow_history(request):
def member_borrow_history(request):
    member_name = request.GET.get('name')

    if not member_name:
        return render(request, 'member_detail.html', {'error': 'Member name is required.'})

    try:
        member = Member.objects.get(full_name=member_name)
    except Member.DoesNotExist:
        return render(request, 'member_detail.html', {'error': 'Member not found.'})

    borrow_history = BorrowRecord.objects.filter(member=member).select_related('book').order_by('-borrow_date')

    return render(request, 'member_detail.html', {
        "member": member,
        "borrow_history": borrow_history,
        "today": date.today()
    })

@api_view(['GET'])
def admin_dashboard_summary1(request):
    total_books = Book.objects.count()
    total_members = Member.objects.count()
    total_borrowed = BorrowRecord.objects.filter(return_date__isnull=True).count()
    total_returned = BorrowRecord.objects.filter(return_date__isnull=False).count()
    total_damaged = BookStatusLog.objects.filter(status__in=['lost', 'damaged']).count()

    # Books currently borrowed with member name
    active_borrows = BorrowRecord.objects.filter(return_date__isnull=True)
    borrowed_books = []
    for record in active_borrows:
        borrowed_books.append({
            "book_title": record.book.title,
            "borrowed_by": record.member.full_name,
            "borrow_date": record.borrow_date,
            "due_date": record.due_date,
        })

    return Response({
        "total_books": total_books,
        "total_members": total_members,
        "number_of_times_books_borrowed": total_borrowed,
        "number_of_times_books_returned": total_returned,
        "total_books_damaged_or_lost": total_damaged,
        "currently_borrowed_books": borrowed_books,
    }, status=200)



def admin_summary_page(request):
    try:
        total_books = Book.objects.count()
        total_members = Member.objects.count()
        currently_borrowed_books = BorrowRecord.objects.filter(return_date__isnull=True).count()
        damaged_books_qs = BookStatusLog.objects.filter(status__icontains='damaged')
        lost_books_qs = BookStatusLog.objects.filter(status__icontains='lost')
        available_copies_total = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0

        damaged_books = [
            {"title": log.book.title, "code": log.book.code, "logged_at": log.date}
            for log in damaged_books_qs.select_related("book")
        ]

        lost_books = [
            {"title": log.book.title, "code": log.book.code, "logged_at": log.date}
            for log in lost_books_qs.select_related("book")
        ]

        low_stock_books = [
            {"title": book.title, "code": book.code, "available": book.available_copies}
            for book in Book.objects.filter(available_copies__lte=1)
        ]

        currently_borrowed = [
            {
                "title": record.book.title,
                "code": record.book.code,
                "borrowed_by": record.member.full_name,
                "due_date": record.due_date
            }
            for record in BorrowRecord.objects.filter(return_date__isnull=True).select_related("book", "member")
        ]

        context = {
            "totals": {
                "total_books": total_books,
                "total_members": total_members,
                "currently_borrowed_books": currently_borrowed_books,
                "damaged_books_count": damaged_books_qs.count(),
                "lost_books_count": lost_books_qs.count(),
                "available_copies_total": available_copies_total
            },
            "lists": {
                "damaged_books": damaged_books,
                "lost_books": lost_books,
                "low_stock_books": low_stock_books,
                "currently_borrowed": currently_borrowed
            }
        }


        # return render(request, "admin_summary.html", context)
        return render(request, "admin_summary.html", {
            "summary": {
                "totals": context.get("totals", {}),
                "lists": context.get("lists", {}),
                }
            })
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

