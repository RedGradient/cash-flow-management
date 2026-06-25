from rest_framework import viewsets

from transactions.models import Category, Transaction
from transactions.serializers import CategorySerializer, TransactionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related("category", "category__parent").all()
    serializer_class = TransactionSerializer
