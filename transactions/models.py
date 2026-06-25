from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class TransactionType(models.TextChoices):
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"


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

    name: models.CharField[str, str] = models.CharField(max_length=100)
    parent: models.ForeignKey[Category | None, Category | None] = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    type: models.CharField[str | None, str | None] = models.CharField(
        max_length=50,
        choices=TransactionType.choices,
        null=True,
        blank=True,
    )

    def clean(self) -> None:
        if (
            self.is_subcategory()
            and self.parent is not None
            and self.parent.is_subcategory()
        ):
            raise ValidationError("Only two levels allowed.")
        if self.is_root_category() and not self.type:
            raise ValidationError("Root category must have a type.")

    # Переопределяем save, чтобы валидация clean выполнялась
    # при добавлении модели через ORM
    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Строковое представление категории для админки и консоли.

        Примеры:
            «Инфраструктура»              # корневая категория
            «Инфраструктура → VPS»        # подкатегория
        """
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def type_value(self) -> str | None:
        """Возвращает значение поля ``type`` этой записи в БД."""
        return self.type

    def effective_type(self) -> str | None:
        """
        Возвращает тип категории для сопоставления с типом транзакции.

        Для корневой категории — её собственный ``type``.
        Для подкатегории — ``type`` родителя, даже если своё поле ``type`` пустое.
        """
        return self.parent.type if self.parent else self.type

    def is_root_category(self) -> bool:
        return self.parent is None

    def is_subcategory(self) -> bool:
        return self.parent is not None


class Transaction(models.Model):
    class Meta:
        db_table = "transactions"

    class Status(models.TextChoices):
        BUSINESS = "Business"
        PERSONAL = "Personal"
        TAX = "Tax"

    amount: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status: models.CharField[str, str] = models.CharField(
        max_length=50,
        choices=Status.choices,
    )
    type: models.CharField[str, str] = models.CharField(
        max_length=50,
        choices=TransactionType.choices,
    )
    category: models.ForeignKey[Category, Category] = models.ForeignKey(
        Category,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )
    comment: models.CharField[str, str] = models.CharField(max_length=100, blank=True)
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self) -> None:
        # Категория должна быть подкатегорией, а не корневой
        if self.category.is_root_category():
            raise ValidationError(
                "Transaction must be linked to a subcategory, not a category."
            )
        # Тип категории (точнее, подкатегории) должен соответствовать типу транзакции
        if self.category.effective_type() != self.type:
            raise ValidationError(
                f"Category type '{self.category.effective_type()}' does not match "
                f"transaction type '{self.type}'."
            )

    # Переопределяем save, чтобы валидация clean выполнялась
    # при добавлении модели через ORM
    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Строковое представление транзакции для админки и консоли.

        Пример:
            «Deposit — 1500.00 rub. (Business)»
        """
        return f"{self.type} — {self.amount} rub. ({self.status})"
