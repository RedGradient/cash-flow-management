from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from transactions.forms import TransactionForm
from transactions.models import (
    Category,
    Transaction,
    TransactionStatus,
    TransactionType,
)


class CategoryModelTests(TestCase):
    def setUp(self) -> None:
        self.withdrawal_type = TransactionType.objects.get(name="Withdrawal")
        self.deposit_type = TransactionType.objects.get(name="Deposit")

    def test_create_root_category(self):
        category = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )

        self.assertTrue(category.is_root_category())
        self.assertFalse(category.is_subcategory())
        self.assertEqual(category.effective_type(), self.withdrawal_type)

    def test_create_subcategory(self):
        root = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )
        subcategory = Category.objects.create(name="Farpost", parent=root)

        self.assertFalse(subcategory.is_root_category())
        self.assertTrue(subcategory.is_subcategory())
        self.assertIsNone(subcategory.type)
        self.assertEqual(subcategory.effective_type(), self.withdrawal_type)

    def test_root_category_without_type_is_invalid(self):
        category = Category(name="Marketing")

        with self.assertRaises(ValidationError):
            category.save()

    def test_third_level_is_invalid(self):
        root = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )
        subcategory = Category.objects.create(name="Farpost", parent=root)
        third_level = Category(name="Detail", parent=subcategory)

        with self.assertRaises(ValidationError):
            third_level.save()

    def test_subcategory_with_type_violates_constraint(self):
        root = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )
        subcategory = Category(
            name="Farpost",
            parent=root,
            type=self.withdrawal_type,
        )

        with self.assertRaises(ValidationError):
            subcategory.save()

    def test_delete_root_category_cascades_to_children(self):
        root = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )
        subcategory = Category.objects.create(name="Farpost", parent=root)
        root_id = root.id
        subcategory_id = subcategory.id

        root.delete()

        self.assertFalse(Category.objects.filter(id=root_id).exists())
        self.assertFalse(Category.objects.filter(id=subcategory_id).exists())


class TransactionModelTests(TestCase):
    def setUp(self) -> None:
        self.business_status = TransactionStatus.objects.get(name="Business")
        self.personal_status = TransactionStatus.objects.get(name="Personal")
        self.tax_status = TransactionStatus.objects.get(name="Tax")
        self.withdrawal_type = TransactionType.objects.get(name="Withdrawal")
        self.deposit_type = TransactionType.objects.get(name="Deposit")

        withdrawal_root = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )
        self.withdrawal_subcategory = Category.objects.create(
            name="Farpost",
            parent=withdrawal_root,
        )

    def test_create_valid_transaction(self):
        transaction = Transaction.objects.create(
            date=date(2026, 1, 15),
            amount=Decimal("1500.00"),
            status=self.business_status,
            type=self.withdrawal_type,
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
            type=self.withdrawal_type,
        )
        transaction = Transaction(
            date=date.today(),
            amount=Decimal("100.00"),
            status=self.business_status,
            type=self.withdrawal_type,
            category=root,
        )

        with self.assertRaises(ValidationError):
            transaction.save()

    def test_mismatched_type_is_invalid(self):
        transaction = Transaction(
            date=date.today(),
            amount=Decimal("100.00"),
            status=self.business_status,
            type=self.deposit_type,
            category=self.withdrawal_subcategory,
        )

        with self.assertRaises(ValidationError):
            transaction.save()

    def test_comment_is_optional(self):
        transaction = Transaction.objects.create(
            date=date.today(),
            amount=Decimal("500.00"),
            status=self.personal_status,
            type=self.withdrawal_type,
            category=self.withdrawal_subcategory,
        )

        self.assertEqual(transaction.comment, "")

    def test_delete_category_with_transaction_is_protected(self):
        Transaction.objects.create(
            date=date.today(),
            amount=Decimal("100.00"),
            status=self.tax_status,
            type=self.withdrawal_type,
            category=self.withdrawal_subcategory,
        )

        with self.assertRaises(ProtectedError):
            self.withdrawal_subcategory.delete()


class TransactionFormTests(TestCase):
    def setUp(self) -> None:
        self.business_status = TransactionStatus.objects.get(name="Business")
        self.withdrawal_type = TransactionType.objects.get(name="Withdrawal")
        self.deposit_type = TransactionType.objects.get(name="Deposit")

        self.withdrawal_root = Category.objects.create(
            name="Marketing",
            type=self.withdrawal_type,
        )
        self.withdrawal_subcategory = Category.objects.create(
            name="Farpost",
            parent=self.withdrawal_root,
        )
        self.deposit_root = Category.objects.create(
            name="Income",
            type=self.deposit_type,
        )
        self.deposit_subcategory = Category.objects.create(
            name="Salary",
            parent=self.deposit_root,
        )

    def _form_data(
        self,
        *,
        transaction_type: TransactionType,
        root_category: Category,
        subcategory: Category,
        amount: str = "100.00",
    ) -> dict[str, str]:
        return {
            "date": "2026-01-15",
            "status": str(self.business_status.pk),
            "type": str(transaction_type.pk),
            "root_category": str(root_category.pk),
            "category": str(subcategory.pk),
            "amount": amount,
            "comment": "",
        }

    def test_valid_form(self):
        form = TransactionForm(
            data=self._form_data(
                transaction_type=self.withdrawal_type,
                root_category=self.withdrawal_root,
                subcategory=self.withdrawal_subcategory,
            )
        )

        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = TransactionForm(data={})

        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)
        self.assertIn("root_category", form.errors)
        self.assertIn("category", form.errors)
        self.assertIn("amount", form.errors)

    def test_root_category_must_match_type(self):
        form = TransactionForm(
            data=self._form_data(
                transaction_type=self.deposit_type,
                root_category=self.withdrawal_root,
                subcategory=self.withdrawal_subcategory,
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("root_category", form.errors)

    def test_subcategory_must_belong_to_root_category(self):
        form = TransactionForm(
            data=self._form_data(
                transaction_type=self.deposit_type,
                root_category=self.deposit_root,
                subcategory=self.withdrawal_subcategory,
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)
