from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from transactions.models import Category, Transaction, TransactionType


class CategoryModelTests(TestCase):
    def test_create_root_category(self):
        category = Category.objects.create(
            name="Marketing",
            type=TransactionType.WITHDRAWAL,
        )

        self.assertTrue(category.is_root_category())
        self.assertFalse(category.is_subcategory())
        self.assertEqual(category.effective_type(), TransactionType.WITHDRAWAL)

    def test_create_subcategory(self):
        root = Category.objects.create(
            name="Marketing",
            type=TransactionType.WITHDRAWAL,
        )
        subcategory = Category.objects.create(name="Farpost", parent=root)

        self.assertFalse(subcategory.is_root_category())
        self.assertTrue(subcategory.is_subcategory())
        self.assertIsNone(subcategory.type)
        self.assertEqual(subcategory.effective_type(), TransactionType.WITHDRAWAL)

    def test_root_category_without_type_is_invalid(self):
        category = Category(name="Marketing")

        with self.assertRaises(ValidationError):
            category.save()

    def test_third_level_is_invalid(self):
        root = Category.objects.create(
            name="Marketing",
            type=TransactionType.WITHDRAWAL,
        )
        subcategory = Category.objects.create(name="Farpost", parent=root)
        third_level = Category(name="Detail", parent=subcategory)

        with self.assertRaises(ValidationError):
            third_level.save()

    def test_subcategory_with_type_violates_constraint(self):
        root = Category.objects.create(
            name="Marketing",
            type=TransactionType.WITHDRAWAL,
        )
        subcategory = Category(
            name="Farpost",
            parent=root,
            type=TransactionType.WITHDRAWAL,
        )

        with self.assertRaises(ValidationError):
            subcategory.save()

    def test_delete_root_category_cascades_to_children(self):
        root = Category.objects.create(
            name="Marketing",
            type=TransactionType.WITHDRAWAL,
        )
        subcategory = Category.objects.create(name="Farpost", parent=root)
        root_id = root.id  # type: ignore
        subcategory_id = subcategory.id  # type: ignore

        root.delete()

        self.assertFalse(Category.objects.filter(id=root_id).exists())
        self.assertFalse(Category.objects.filter(id=subcategory_id).exists())


class TransactionModelTests(TestCase):
    def setUp(self) -> None:
        withdrawal_root = Category.objects.create(
            name="Marketing",
            type=TransactionType.WITHDRAWAL,
        )
        self.withdrawal_subcategory = Category.objects.create(
            name="Farpost",
            parent=withdrawal_root,
        )

    def test_create_valid_transaction(self):
        transaction = Transaction.objects.create(
            amount=Decimal("1500.00"),
            status=Transaction.Status.BUSINESS,
            type=TransactionType.WITHDRAWAL,
            category=self.withdrawal_subcategory,
            comment="Monthly ads",
        )

        self.assertEqual(transaction.amount, Decimal("1500.00"))
        self.assertEqual(transaction.category, self.withdrawal_subcategory)
        self.assertEqual(transaction.comment, "Monthly ads")
        self.assertIsNotNone(transaction.created_at)

    def test_root_category_is_invalid(self):
        root = Category.objects.create(
            name="Infrastructure",
            type=TransactionType.WITHDRAWAL,
        )
        transaction = Transaction(
            amount=Decimal("100.00"),
            status=Transaction.Status.BUSINESS,
            type=TransactionType.WITHDRAWAL,
            category=root,
        )

        with self.assertRaises(ValidationError):
            transaction.save()

    def test_mismatched_type_is_invalid(self):
        transaction = Transaction(
            amount=Decimal("100.00"),
            status=Transaction.Status.BUSINESS,
            type=TransactionType.DEPOSIT,
            category=self.withdrawal_subcategory,
        )

        with self.assertRaises(ValidationError):
            transaction.save()

    def test_comment_is_optional(self):
        transaction = Transaction.objects.create(
            amount=Decimal("500.00"),
            status=Transaction.Status.PERSONAL,
            type=TransactionType.WITHDRAWAL,
            category=self.withdrawal_subcategory,
        )

        self.assertEqual(transaction.comment, "")

    def test_delete_category_with_transaction_is_protected(self):
        Transaction.objects.create(
            amount=Decimal("100.00"),
            status=Transaction.Status.TAX,
            type=TransactionType.WITHDRAWAL,
            category=self.withdrawal_subcategory,
        )

        with self.assertRaises(ProtectedError):
            self.withdrawal_subcategory.delete()
