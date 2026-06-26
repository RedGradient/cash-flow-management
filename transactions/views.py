from django.contrib import messages
from django.db.models import ProtectedError, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from rest_framework import viewsets

from transactions.forms import (
    RootCategoryForm,
    StatusForm,
    SubcategoryForm,
    TransactionFilterForm,
    TransactionForm,
    TypeForm,
)
from transactions.models import (
    Category,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from transactions.serializers import CategorySerializer, TransactionSerializer


def _filter_transactions(
    queryset: QuerySet[Transaction], form: TransactionFilterForm
) -> QuerySet[Transaction]:
    """Фильтрует переданный queryset по полям из form."""

    if not form.is_valid():
        return queryset

    date_from = form.cleaned_data.get("date_from")
    date_to = form.cleaned_data.get("date_to")
    status = form.cleaned_data.get("status")
    transaction_type = form.cleaned_data.get("type")
    category = form.cleaned_data.get("category")
    subcategory = form.cleaned_data.get("subcategory")

    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)
    if status:
        queryset = queryset.filter(status=status)
    if transaction_type:
        queryset = queryset.filter(type=transaction_type)
    if category:
        queryset = queryset.filter(category__parent=category)
    if subcategory:
        queryset = queryset.filter(category=subcategory)

    return queryset


# Главная страница: таблица операций и фильтры (GET).
def transaction_list(request: HttpRequest) -> HttpResponse:
    filter_form = TransactionFilterForm(request.GET or None)
    transactions = Transaction.objects.select_related(
        "status",
        "type",
        "category",
        "category__parent",
    ).order_by("-date", "-id")
    transactions = _filter_transactions(transactions, filter_form)

    return render(
        request,
        "transactions/transaction_list.html",
        {
            "transactions": transactions,
            "filter_form": filter_form,
        },
    )


# Форма создания новой операции.
def transaction_create(request: HttpRequest) -> HttpResponse:
    form = TransactionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Операция создана.")
        return redirect("transaction_list")

    return render(
        request,
        "transactions/transaction_form.html",
        {"form": form, "title": "Новая операция"},
    )


# Форма редактирования существующей операции.
def transaction_update(request: HttpRequest, pk: int) -> HttpResponse:
    transaction = get_object_or_404(Transaction, pk=pk)
    form = TransactionForm(request.POST or None, instance=transaction)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Операция обновлена.")
        return redirect("transaction_list")

    return render(
        request,
        "transactions/transaction_form.html",
        {"form": form, "title": "Редактирование операции", "transaction": transaction},
    )


# Удаление операции (POST с главной страницы).
@require_POST
def transaction_delete(request: HttpRequest, pk: int) -> HttpResponse:
    transaction = get_object_or_404(Transaction, pk=pk)
    transaction.delete()
    messages.success(request, "Операция удалена.")
    return redirect("transaction_list")


# Страница справочников: добавление и правка статусов, типов, категорий.
def reference_manage(request: HttpRequest) -> HttpResponse:
    status_form = StatusForm(request.POST or None, prefix="status")
    type_form = TypeForm(request.POST or None, prefix="type")
    root_category_form = RootCategoryForm(request.POST or None, prefix="root")
    subcategory_form = SubcategoryForm(request.POST or None, prefix="sub")

    if request.method != "POST":
        action = request.POST.get("action")
        if action == "add_status" and status_form.is_valid():
            status_form.save()
            messages.success(request, "Статус добавлен.")
            return redirect("reference_manage")
        if action == "update_status":
            status = get_object_or_404(
                TransactionStatus,
                pk=request.POST.get("id"),
            )
            status.name = request.POST.get("name", "").strip()
            status.save()
            messages.success(request, "Статус обновлён.")
            return redirect("reference_manage")
        if action == "add_type" and type_form.is_valid():
            type_form.save()
            messages.success(request, "Тип добавлен.")
            return redirect("reference_manage")
        if action == "update_type":
            transaction_type = get_object_or_404(
                TransactionType,
                pk=request.POST.get("id"),
            )
            transaction_type.name = request.POST.get("name", "").strip()
            transaction_type.save()
            messages.success(request, "Тип обновлён.")
            return redirect("reference_manage")
        if action == "add_root" and root_category_form.is_valid():
            root_category_form.save()
            messages.success(request, "Категория добавлена.")
            return redirect("reference_manage")
        if action == "update_root":
            category = get_object_or_404(Category, pk=request.POST.get("id"))
            category.name = request.POST.get("name", "").strip()
            category.type_id = int(request.POST.get("type", ""))
            category.save()
            messages.success(request, "Категория обновлена.")
            return redirect("reference_manage")
        if action == "add_sub" and subcategory_form.is_valid():
            subcategory_form.save()
            messages.success(request, "Подкатегория добавлена.")
            return redirect("reference_manage")
        if action == "update_sub":
            subcategory = get_object_or_404(Category, pk=request.POST.get("id"))
            subcategory.name = request.POST.get("name", "").strip()
            subcategory.parent_id = int(request.POST.get("parent", ""))
            subcategory.save()
            messages.success(request, "Подкатегория обновлена.")
            return redirect("reference_manage")

    return render(
        request,
        "transactions/reference_manage.html",
        {
            "statuses": TransactionStatus.objects.all(),
            "types": TransactionType.objects.all(),
            "root_categories": Category.objects.filter(
                parent__isnull=True
            ).select_related("type"),
            "subcategories": Category.objects.filter(
                parent__isnull=False
            ).select_related("parent"),
            "status_form": status_form,
            "type_form": type_form,
            "root_category_form": root_category_form,
            "subcategory_form": subcategory_form,
        },
    )


# Удаление записи справочника по типу и id (POST).
@require_POST
def reference_delete(request: HttpRequest, model: str, pk: int) -> HttpResponse:
    models_map = {
        "status": TransactionStatus,
        "type": TransactionType,
        "category": Category,
        "subcategory": Category,
    }
    model_class = models_map.get(model)
    if model_class is None:
        messages.error(request, "Неизвестный тип справочника.")
        return redirect("reference_manage")

    obj = get_object_or_404(model_class, pk=pk)
    try:
        obj.delete()
        messages.success(request, "Запись удалена.")
    except ProtectedError:
        messages.error(request, "Невозможно удалить: запись используется.")
    return redirect("reference_manage")


# JSON: корневые категории для выбранного типа (форма операции).
@require_GET
def categories_api(request: HttpRequest) -> JsonResponse:
    transaction_type_id = request.GET.get("type")
    if not transaction_type_id:
        return JsonResponse([], safe=False)

    try:
        type_id = int(transaction_type_id)
    except (TypeError, ValueError):
        return JsonResponse([], safe=False)

    queryset: QuerySet[Category] = Category.objects.filter(
        parent__isnull=True,
        type_id=type_id,
    )
    data = [{"id": category.pk, "name": category.name} for category in queryset]
    return JsonResponse(data, safe=False)


# JSON: подкатегории для выбранной категории и типа (форма операции).
@require_GET
def subcategories_api(request: HttpRequest) -> JsonResponse:
    parent_id = request.GET.get("parent")
    transaction_type_id = request.GET.get("type")

    if not parent_id or not transaction_type_id:
        return JsonResponse([], safe=False)

    try:
        parent_pk = int(parent_id)
        type_id = int(transaction_type_id)
    except (TypeError, ValueError):
        return JsonResponse([], safe=False)

    queryset: QuerySet[Category] = Category.objects.filter(
        parent__isnull=False,
        parent_id=parent_pk,
        parent__type_id=type_id,
    ).select_related("parent")
    data = [{"id": category.pk, "name": category.name} for category in queryset]
    return JsonResponse(data, safe=False)


# REST API: категории и подкатегории.
class CategoryViewSet(viewsets.ModelViewSet[Category]):
    queryset = Category.objects.select_related("parent", "type").all()
    serializer_class = CategorySerializer

    # Фильтрация списка по query-параметрам parent и type.
    def get_queryset(self) -> QuerySet[Category]:
        queryset = super().get_queryset()
        parent = self.request.query_params.get("parent")
        transaction_type = self.request.query_params.get("type")

        if parent == "null":
            queryset = queryset.filter(parent__isnull=True)
            if transaction_type:
                queryset = queryset.filter(type_id=int(transaction_type))
        elif parent:
            queryset = queryset.filter(parent_id=int(parent))
        elif transaction_type:
            queryset = queryset.filter(
                parent__isnull=True, type_id=int(transaction_type)
            )

        return queryset


# REST API: операции ДДС.
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related(
        "status",
        "type",
        "category",
        "category__parent",
    ).all()
    serializer_class = TransactionSerializer
