""" Hydra model admin """

"""

# Django
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Models
from hydra.models import Action, Menu

# Forms
from hydra.forms import BaseActionForm, BaseMenuForm, BasePermissionForm

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    form = BaseActionForm
    list_display = ("__str__", "app_label")


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    form = BaseMenuForm
    list_display = ('__str__', 'action',)


@admin.register(Permission)
class PermisionAdmin(admin.ModelAdmin):
    model = Permission
    form = BasePermissionForm
    list_display = ("name", "codename", "__str__")

    def __init__(self, model, admin_site):
        self.model._meta.verbose_name = "permiso específico"
        self.model._meta.verbose_name_plural = "permisos específicos"
        super().__init__(model, admin_site)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        ct = ContentType.objects.get_for_model(self.model)
        codenames = ("add_permission","change_permission","delete_permission","view_permission")
        qs = qs.filter(content_type=ct).exclude(codename__in=codenames)
        return qs

"""
