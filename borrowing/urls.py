from django.urls import path
from . import views

urlpatterns = [
    path('borrow/', views.borrow_book, name='borrow-book'),
    path('return/', views.return_book, name='return-book'),
    path('lost_or_damaged/', views.lost_or_damaged_book, name='report-lost-or-damaged'),
    # path('book-history/', views.book_borrowing_history, name='book-history'),
    path('books/history/', views.book_detail_view, name='book_detail'),

    path('admin-summary/', views.admin_summary_page, name='admin-dashboard-summary'),
    path('book/', views.book_detail_view, name='book-detail'),
    path('members/history/', views.member_borrow_history, name='member-history'),
    path('admin/summary/', views.admin_summary_page, name='admin-summary'),


]
