from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class TransactionStatus(models.Model):
    class Meta:
        db_table = "transaction_statuses"
        verbose_name = "Status"
        verbose_name_plural = "Statuses"

    name: models.CharField[str, str] = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class TransactionType(models.Model):
    class Meta:
        db_table = "transaction_types"
        verbose_name = "Type"
        verbose_name_plural = "Types"

    name: models.CharField[str, str] = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    """
    Двухуровневая иерархия категорий.

    Категории верхнего уровня ``(parent=None)`` — корневые (например, «Инфраструктура»).
    Категории второго уровня ссылаются на корневую как родителя (например, «VPS»).

    Вложенность глубже двух уровней не допускается и приводит к ``ValidationError``.
    """

    class Meta:
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

        # Подкатегория не хранит type — type задаётся только у корневой категории.
        constraints = [
            models.CheckConstraint(
                condition=Q(parent__isnull=True) | Q(type__isnull=True),
                name="category_subcategory_has_no_type",
            )
        ]

    id: int
    name: models.CharField[str, str] = models.CharField(max_length=100)
    parent: models.ForeignKey[Category | None, Category | None] = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    parent_id: int | None
    type: models.ForeignKey[TransactionType | None, TransactionType | None] = (
        models.ForeignKey(
            TransactionType,
            null=True,
            blank=True,
            on_delete=models.PROTECT,
            related_name="categories",
        )
    )
    type_id: int | None

    def clean(self) -> None:
        if (
            self.is_subcategory()
            and self.parent is not None
            and self.parent.is_subcategory()
        ):
            raise ValidationError("Only two levels allowed.")
        if self.is_root_category() and not self.type_id:
            raise ValidationError("Root category must have a type.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Корневая категория: ``«Маркетинг»``.
        Подкатегория: ``«Маркетинг → Farpost»``.
        """
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def type_value(self) -> TransactionType | None:
        """Возвращает значение поля ``type`` этой записи в БД."""
        return self.type

    def effective_type(self) -> TransactionType | None:
        """
        Возвращает тип категории для сопоставления с типом транзакции.

        Для корневой категории — её собственный ``type``.
        Для подкатегории — ``type`` родителя.
        """
        if self.parent:
            return self.parent.type
        return self.type

    def is_root_category(self) -> bool:
        return self.parent is None

    def is_subcategory(self) -> bool:
        return self.parent is not None


class Transaction(models.Model):
    class Meta:
        db_table = "transactions"

    id: int
    date: models.DateField[datetime, datetime] = models.DateField()
    amount: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status: models.ForeignKey[TransactionStatus, TransactionStatus] = models.ForeignKey(
        TransactionStatus,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    status_id: int | None
    type: models.ForeignKey[TransactionType, TransactionType] = models.ForeignKey(
        TransactionType,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    type_id: int | None
    category: models.ForeignKey[Category, Category] = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    category_id: int | None
    comment: models.CharField[str, str] = models.CharField(max_length=100, blank=True)
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self) -> None:
        if not self.category_id:
            return
        if self.category.is_root_category():
            raise ValidationError(
                "Transaction must be linked to a subcategory, not a category."
            )
        if self.category.effective_type() != self.type:
            raise ValidationError(
                f"Category type '{self.category.effective_type()}' does not match "
                f"transaction type '{self.type}'."
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Формат: ``«Withdrawal — 1500.00 rub. (Business)»`` —
        тип, сумма и статус операции.
        """
        return f"{self.type} — {self.amount} rub. ({self.status})"
