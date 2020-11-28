"""Mixins for autosite"""

# Django
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin
)


"""
class MultiplePermissionRequiredModuleMixin(DjangoPermissionRequiredMixin):

    def has_permission(self):
        user = self.request.user
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return True
        permissions = list()
        ctx = self.get_context_data()
        for model in ctx["models_permissions"]:
            permissions.append(f"{model._meta.app_label}.view_{model._meta.model_name}")
            permissions.append(f"{model._meta.app_label}.add_{model._meta.model_name}")
            permissions.append(
                f"{model._meta.app_label}.change_{model._meta.model_name}"
            )
        return any(user.has_perm(permission) for permission in permissions)
"""


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """Verifica los permisos de acceso al modelo"""

    def get_permission_required(self):
        app = self.model._meta.app_label
        model = self.model._meta.model_name

        if self.action == "create":
            permissions = ("add",)
        elif self.action == "update":
            permissions = ("change",)
        elif self.action == "delete":
            permissions = ("delete",)
        else:
            permissions = ("view", "add", "change", "delete")

        perms = (f"{app}.{perm}_{model}" for perm in permissions)
        return perms

    def has_permission(self):
        user = self.request.user
        if all([user.is_authenticated, user.is_superuser, user.is_active]):
            return True
        perms = self.get_permission_required()
        return any(user.has_perm(perm) for perm in perms)
