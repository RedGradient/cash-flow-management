from datetime import date
from decimal import Decimal

from transactions.models import (
    Category,
    Transaction,
    TransactionStatus,
    TransactionType,
)

WITHDRAWAL_CATEGORIES: dict[str, list[str]] = {
    "Инфраструктура": ["VPS", "Proxy"],
    "Маркетинг": ["Farpost", "Avito"],
    "Персонал": ["Зарплата", "Фриланс"],
    "Операционные": ["Банк", "Офис"],
}

DEPOSIT_CATEGORIES: dict[str, list[str]] = {
    "Доходы": ["Продажи", "Возвраты"],
}


def _seed_categories(
    category_tree: dict[str, list[str]],
    transaction_type: TransactionType,
) -> dict[str, Category]:
    subcategories: dict[str, Category] = {}
    for root_name, children in category_tree.items():
        root, _ = Category.objects.get_or_create(
            name=root_name,
            parent=None,
            defaults={"type": transaction_type},
        )
        for child_name in children:
            subcategory, _ = Category.objects.get_or_create(
                name=child_name,
                parent=root,
            )
            subcategories[child_name] = subcategory
    return subcategories


def seed_database() -> None:
    withdrawal, _ = TransactionType.objects.get_or_create(name="Списание")
    deposit, _ = TransactionType.objects.get_or_create(name="Пополнение")

    business, _ = TransactionStatus.objects.get_or_create(name="Бизнес")
    personal, _ = TransactionStatus.objects.get_or_create(name="Личное")
    tax, _ = TransactionStatus.objects.get_or_create(name="Налог")

    withdrawal_subcategories = _seed_categories(WITHDRAWAL_CATEGORIES, withdrawal)
    deposit_subcategories = _seed_categories(DEPOSIT_CATEGORIES, deposit)

    vps = withdrawal_subcategories["VPS"]
    proxy = withdrawal_subcategories["Proxy"]
    farpost = withdrawal_subcategories["Farpost"]
    avito = withdrawal_subcategories["Avito"]
    salary = withdrawal_subcategories["Зарплата"]
    freelance = withdrawal_subcategories["Фриланс"]
    bank = withdrawal_subcategories["Банк"]
    office = withdrawal_subcategories["Офис"]
    sales = deposit_subcategories["Продажи"]
    refunds = deposit_subcategories["Возвраты"]

    samples = [
        (date(2026, 1, 5), Decimal("890.00"), business, withdrawal, vps, "Оплата VPS"),
        (date(2026, 1, 10), Decimal("150.00"), business, withdrawal, proxy, "Прокси на месяц"),
        (date(2026, 1, 15), Decimal("2500.00"), business, withdrawal, farpost, "Реклама Farpost"),
        (date(2026, 1, 20), Decimal("1800.00"), business, withdrawal, avito, "Продвижение Avito"),
        (date(2026, 2, 1), Decimal("890.00"), business, withdrawal, vps, "Сервер на февраль"),
        (date(2026, 2, 5), Decimal("3200.00"), personal, withdrawal, farpost, "Личная реклама"),
        (date(2026, 2, 10), Decimal("150.00"), business, withdrawal, proxy, "Продление Proxy"),
        (date(2026, 2, 15), Decimal("500.00"), tax, withdrawal, vps, "Налог на инфраструктуру"),
        (date(2026, 3, 1), Decimal("2100.00"), business, withdrawal, avito, "Avito — март"),
        (date(2026, 3, 5), Decimal("1200.00"), business, withdrawal, proxy, "Дополнительные прокси"),
        (date(2026, 3, 10), Decimal("45000.00"), business, withdrawal, salary, "Зарплата менеджера"),
        (date(2026, 3, 12), Decimal("8000.00"), business, withdrawal, freelance, "Дизайн лендинга"),
        (date(2026, 3, 15), Decimal("500.00"), business, withdrawal, bank, "Комиссия банка"),
        (date(2026, 3, 18), Decimal("3500.00"), business, withdrawal, office, "Канцтовары и вода"),
        (date(2026, 2, 20), Decimal("15000.00"), business, deposit, sales, "Оплата заказа клиента"),
        (date(2026, 2, 25), Decimal("5000.00"), business, deposit, refunds, "Возврат от Farpost"),
        (date(2026, 3, 20), Decimal("22000.00"), business, deposit, sales, "Продажи — март"),
        (date(2026, 3, 22), Decimal("1200.00"), personal, deposit, refunds, "Личный возврат"),
    ]

    for transaction_date, amount, status, tx_type, category, comment in samples:
        Transaction.objects.get_or_create(
            date=transaction_date,
            amount=amount,
            comment=comment,
            defaults={
                "status": status,
                "type": tx_type,
                "category": category,
            },
        )
