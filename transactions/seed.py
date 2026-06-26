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


def _seed_withdrawal_categories(withdrawal: TransactionType) -> dict[str, Category]:
    subcategories: dict[str, Category] = {}
    for root_name, children in WITHDRAWAL_CATEGORIES.items():
        root, _ = Category.objects.get_or_create(
            name=root_name,
            parent=None,
            defaults={"type": withdrawal},
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
    TransactionType.objects.get_or_create(name="Пополнение")

    business, _ = TransactionStatus.objects.get_or_create(name="Бизнес")
    personal, _ = TransactionStatus.objects.get_or_create(name="Личное")
    tax, _ = TransactionStatus.objects.get_or_create(name="Налог")

    subcategories = _seed_withdrawal_categories(withdrawal)

    vps = subcategories["VPS"]
    proxy = subcategories["Proxy"]
    farpost = subcategories["Farpost"]
    avito = subcategories["Avito"]
    salary = subcategories["Зарплата"]
    freelance = subcategories["Фриланс"]
    bank = subcategories["Банк"]
    office = subcategories["Офис"]

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
