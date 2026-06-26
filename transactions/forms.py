from typing import Any

from django import forms

from transactions.models import (
    Category,
    Transaction,
    TransactionStatus,
    TransactionType,
)


class TransactionFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label="Дата от",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    date_to = forms.DateField(
        required=False,
        label="Дата до",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    status = forms.ModelChoiceField(
        queryset=TransactionStatus.objects.all(),
        required=False,
        empty_label="Все статусы",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    type = forms.ModelChoiceField(
        queryset=TransactionType.objects.all(),
        required=False,
        empty_label="Все типы",
        label="Тип",
        widget=forms.Select(attrs={"class": "form-select", "id": "filter-type"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="Все категории",
        label="Категория",
        widget=forms.Select(attrs={"class": "form-select", "id": "filter-category"}),
    )
    subcategory = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="Все подкатегории",
        label="Подкатегория",
        widget=forms.Select(attrs={"class": "form-select", "id": "filter-subcategory"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        type_id = self._selected_int("type")
        category_id = self._selected_int("category")
        category_field = self._model_choice_field("category")
        subcategory_field = self._model_choice_field("subcategory")

        if type_id:
            category_field.queryset = Category.objects.filter(
                parent__isnull=True,
                type_id=type_id,
            )
        else:
            category_field.queryset = Category.objects.none()

        if type_id and category_id:
            subcategory_field.queryset = Category.objects.filter(
                parent_id=category_id,
                parent__type_id=type_id,
            )
        else:
            subcategory_field.queryset = Category.objects.none()

    def _model_choice_field(self, name: str) -> forms.ModelChoiceField:
        field = self.fields[name]
        if not isinstance(field, forms.ModelChoiceField):
            raise TypeError(f"Field {name} must be a ModelChoiceField.")
        return field

    def _selected_int(self, name: str) -> int | None:
        if self.data is None:
            return None
        raw_value = self.data.get(name)
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    def clean(self) -> dict[str, Any]:
        super().clean()
        cleaned_data: dict[str, Any] = self.cleaned_data
        transaction_type = cleaned_data.get("type")
        category = cleaned_data.get("category")
        subcategory = cleaned_data.get("subcategory")

        if category and transaction_type and category.type_id != transaction_type.id:
            self.add_error("category", "Категория не соответствует выбранному типу.")
        if category and subcategory and subcategory.parent_id != category.id:
            self.add_error(
                "subcategory",
                "Подкатегория должна принадлежать выбранной категории.",
            )
        if (
            subcategory
            and transaction_type
            and subcategory.effective_type() != transaction_type
        ):
            self.add_error(
                "subcategory",
                "Подкатегория не соответствует выбранному типу.",
            )
        return cleaned_data


class TransactionForm(forms.ModelForm):
    root_category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=True,
        label="Категория",
        empty_label="---------",
    )
    type = forms.ModelChoiceField(
        queryset=TransactionType.objects.all(),
        required=True,
        label="Тип",
        empty_label="---------",
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=True,
        label="Подкатегория",
        empty_label="---------",
    )

    class Meta:
        model = Transaction
        fields = [
            "date",
            "status",
            "type",
            "root_category",
            "category",
            "amount",
            "comment",
        ]
        labels = {
            "date": "Дата",
            "status": "Статус",
            "amount": "Сумма",
            "comment": "Комментарий",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "category": forms.Select(
                attrs={"class": "form-select", "id": "subcategory"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].required = True

        self.fields["status"].widget.attrs.update({"class": "form-select"})
        self.fields["type"].widget.attrs.update(
            {"class": "form-select", "id": "transaction-type", "required": "required"}
        )
        self.fields["root_category"].widget.attrs.update(
            {"class": "form-select", "id": "root-category", "required": "required"}
        )
        self.fields["category"].widget.attrs.update(
            {"class": "form-select", "id": "subcategory", "required": "required"}
        )
        self.fields["amount"].widget.attrs.update(
            {
                "class": "form-control",
                "required": "required",
                "id": "transaction-amount",
            }
        )
        self.fields["comment"].widget.attrs.update({"class": "form-control"})

        root_category_field = self._model_choice_field("root_category")
        category_field = self._model_choice_field("category")

        transaction_type_id = self._selected_type_id()
        root_category_id = self._selected_root_category_id()

        if self.instance.pk and not self.data:
            root_category_field.initial = self.instance.category.parent_id
            transaction_type_id = self.instance.type_id
            root_category_id = self.instance.category.parent_id

        if transaction_type_id:
            root_category_field.queryset = Category.objects.filter(
                parent__isnull=True,
                type_id=transaction_type_id,
            )
        if root_category_id:
            subcategory_queryset = Category.objects.filter(parent_id=root_category_id)
            if transaction_type_id:
                subcategory_queryset = subcategory_queryset.filter(
                    parent__type_id=transaction_type_id
                )
            category_field.queryset = subcategory_queryset

    def _model_choice_field(self, name: str) -> forms.ModelChoiceField:
        field = self.fields[name]
        if not isinstance(field, forms.ModelChoiceField):
            raise TypeError(f"Field {name} must be a ModelChoiceField.")
        return field

    def _selected_type_id(self) -> int | None:
        if self.data is None:
            return None
        raw_type = self.data.get("type")
        if not raw_type:
            return None
        try:
            return int(raw_type)
        except (TypeError, ValueError):
            return None

    def _selected_root_category_id(self) -> int | None:
        if self.data is None:
            return None
        raw_root_category = self.data.get("root_category")
        if not raw_root_category:
            return None
        try:
            return int(raw_root_category)
        except (TypeError, ValueError):
            return None

    def clean(self) -> dict[str, Any]:
        super().clean()
        cleaned_data: dict[str, Any] = self.cleaned_data
        root_category = cleaned_data.get("root_category")
        subcategory = cleaned_data.get("category")
        transaction_type = cleaned_data.get("type")

        if (
            root_category
            and transaction_type
            and root_category.type_id != transaction_type.id
        ):
            raise forms.ValidationError(
                "Категория не соответствует выбранному типу операции."
            )
        if root_category and subcategory:
            if subcategory.parent_id != root_category.id:
                raise forms.ValidationError(
                    "Подкатегория должна принадлежать выбранной категории."
                )
        if (
            subcategory
            and transaction_type
            and subcategory.effective_type() != transaction_type
        ):
            raise forms.ValidationError(
                "Тип подкатегории не соответствует выбранному типу операции."
            )
        return cleaned_data


class StatusForm(forms.ModelForm):
    class Meta:
        model = TransactionStatus
        fields = ["name"]
        labels = {"name": "Название"}
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}


class TypeForm(forms.ModelForm):
    class Meta:
        model = TransactionType
        fields = ["name"]
        labels = {"name": "Название"}
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}


class RootCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "type"]
        labels = {
            "name": "Название",
            "type": "Тип",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
        }


class SubcategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=True),
        label="Категория",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Category
        fields = ["name", "parent"]
        labels = {
            "name": "Название",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }
