from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin


# Для удобства делаем админку /admin без авторизации.
def setup_dev_admin_without_auth() -> None:
    if not settings.DEBUG:
        return

    admin.site.has_permission = lambda request: True

    # has_permission открывает только главную; без этого модели скрыты и дают 403.
    def allow(self, request, obj=None):
        return True

    ModelAdmin.has_module_permission = allow
    ModelAdmin.has_view_permission = allow
    ModelAdmin.has_add_permission = lambda self, request: True
    ModelAdmin.has_change_permission = allow
    ModelAdmin.has_delete_permission = allow
