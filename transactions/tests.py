from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from transactions.forms import TransactionFilterForm, TransactionForm
from transactions.models import (
    Category,
    Transaction,
    TransactionStatus,
    TransactionType,
)


class CategoryModelTests(TestCase):
    def setUp(self) -> None:
        self.withdrawal_type = TransactionType.objects.get(name="Списание")
        self.deposit_type = TransactionType.objects.get(name="Пополнение")

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
        self.business_status = TransactionStatus.objects.get(name="Бизнес")
        self.personal_status = TransactionStatus.objects.get(name="Личное")
        self.tax_status = TransactionStatus.objects.get(name="Налог")
        self.withdrawal_type = TransactionType.objects.get(name="Списание")
        self.deposit_type = TransactionType.objects.get(name="Пополнение")

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
        self.business_status = TransactionStatus.objects.get(name="Бизнес")
        self.withdrawal_type = TransactionType.objects.get(name="Списание")
        self.deposit_type = TransactionType.objects.get(name="Пополнение")

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


class TransactionFilterFormTests(TestCase):
    def setUp(self) -> None:
        self.withdrawal_type = TransactionType.objects.get(name="Списание")
        self.deposit_type = TransactionType.objects.get(name="Пополнение")

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

    def _field_queryset(self, form: TransactionFilterForm, name: str):
        queryset = form._model_choice_field(name).queryset
        assert queryset is not None
        return queryset

    def test_category_queryset_empty_without_type(self) -> None:
        form = TransactionFilterForm(data={})

        self.assertEqual(list(self._field_queryset(form, "category")), [])

    def test_category_queryset_filtered_by_type(self) -> None:
        form = TransactionFilterForm(
            data={
                "type": str(self.withdrawal_type.pk),
            }
        )

        self.assertTrue(form.is_valid())
        category_queryset = self._field_queryset(form, "category")
        category_ids = list(category_queryset.values_list("id", flat=True))
        self.assertIn(self.withdrawal_root.pk, category_ids)
        self.assertTrue(
            all(
                category.type_id == self.withdrawal_type.pk
                for category in category_queryset
            )
        )

    def test_subcategory_queryset_filtered_by_category(self) -> None:
        form = TransactionFilterForm(
            data={
                "type": str(self.withdrawal_type.pk),
                "category": str(self.withdrawal_root.pk),
            }
        )

        self.assertTrue(form.is_valid())
        subcategory_ids = list(
            self._field_queryset(form, "subcategory").values_list("id", flat=True)
        )
        self.assertEqual(subcategory_ids, [self.withdrawal_subcategory.pk])

    def test_mismatched_category_and_type_is_invalid(self) -> None:
        form = TransactionFilterForm(
            data={
                "type": str(self.deposit_type.pk),
                "category": str(self.withdrawal_root.pk),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)


class SeedTests(TestCase):
    def test_seed_creates_reference_data(self) -> None:
        self.assertEqual(TransactionStatus.objects.count(), 3)
        self.assertEqual(TransactionType.objects.count(), 2)
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), 5)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), 10)
        self.assertEqual(Transaction.objects.count(), 18)
        self.assertEqual(
            Transaction.objects.filter(type__name="Пополнение").count(),
            4,
        )

    def test_seed_is_idempotent(self) -> None:
        from transactions.seed import seed_database

        count_before = Transaction.objects.count()
        category_count_before = Category.objects.count()
        seed_database()
        self.assertEqual(Transaction.objects.count(), count_before)
        self.assertEqual(Category.objects.count(), category_count_before)
