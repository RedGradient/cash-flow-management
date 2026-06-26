from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from transactions.models import (
    Category,
    Transaction,
)


# Это базовый класс для CategorySerializer и TransactionSerializer
# Реализует общую функциональность для валидации входящих данных
class FullCleanModelSerializer(serializers.ModelSerializer):
    def _raise_validation_error(self, error: DjangoValidationError) -> None:
        if hasattr(error, "message_dict"):
            raise serializers.ValidationError(error.message_dict)
        raise serializers.ValidationError(error.messages)

    def validate(self, attrs: dict) -> dict:
        model = self.Meta.model
        instance = self.instance or model()
        for field_name, value in attrs.items():
            setattr(instance, field_name, value)

        try:
            instance.full_clean()
        except DjangoValidationError as error:
            self._raise_validation_error(error)

        return attrs


# Сериализация Категорий для API
class CategorySerializer(FullCleanModelSerializer):
    effective_type = serializers.SerializerMethodField()

    class Meta:  # type: ignore
        model = Category
        fields = [
            "id",
            "name",
            "parent",
            "type",
            "effective_type",
        ]
        read_only_fields = ["id", "effective_type"]

    def get_effective_type(self, category: Category) -> str | None:
        effective_type = category.effective_type()
        return effective_type.name if effective_type else None


# Сериализация Транзакций для API
class TransactionSerializer(FullCleanModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)
    type_name = serializers.CharField(source="type.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    parent_category_name = serializers.CharField(
        source="category.parent.name",
        read_only=True,
    )

    class Meta:  # type: ignore
        model = Transaction
        fields = [
            "id",
            "date",
            "amount",
            "status",
            "status_name",
            "type",
            "type_name",
            "category",
            "category_name",
            "parent_category_name",
            "comment",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "status_name",
            "type_name",
            "category_name",
            "parent_category_name",
        ]
