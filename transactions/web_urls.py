from django.urls import path

from transactions import views

urlpatterns = [
    path("", views.transaction_list, name="transaction_list"),
    path("transactions/new/", views.transaction_create, name="transaction_create"),
    path(
        "transactions/<int:pk>/edit/",
        views.transaction_update,
        name="transaction_update",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.transaction_delete,
        name="transaction_delete",
    ),
    path("references/", views.reference_manage, name="reference_manage"),
    path(
        "references/<str:model>/<int:pk>/delete/",
        views.reference_delete,
        name="reference_delete",
    ),
    path("api/categories/", views.categories_api, name="categories_api"),
    path("api/subcategories/", views.subcategories_api, name="subcategories_api"),
]
