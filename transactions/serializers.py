from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from transactions.models import Category, Transaction


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


class CategorySerializer(FullCleanModelSerializer):
    effective_type = serializers.SerializerMethodField()

    class Meta:
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
        return category.effective_type()


class TransactionSerializer(FullCleanModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "amount",
            "status",
            "type",
            "category",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
