from rest_framework.routers import DefaultRouter

from transactions.views import CategoryViewSet, TransactionViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = router.urls
