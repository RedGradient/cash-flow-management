from django.contrib import admin

from transactions.models import (
    Category,
    Transaction,
    TransactionStatus,
    TransactionType,
)


@admin.register(TransactionStatus)
class TransactionStatusAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "type")
    list_filter = ("type",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "type", "status", "amount", "category")
    list_filter = ("status", "type", "date")
