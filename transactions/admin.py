from django.contrib import admin

from transactions.models import Category, Transaction

# Register your models here.
admin.site.register(Category)
admin.site.register(Transaction)
