from django.contrib import admin

# Register your models here.
from .models import Book, Category, BookStatusLog, RestockLog

admin.site.register(Book)
admin.site.register(Category) 
admin.site.register(BookStatusLog)
admin.site.register(RestockLog)
 

