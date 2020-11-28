""" Models for buid menus """

# Django
from django.db import models
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.text import slugify
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Local
from . import site
from .utils import import_class


class Action(models.Model):
    class ToChoices(models.IntegerChoices):
        MODEL = 1, "Modelo"
        CLASSVIEW = 2, "Vista"

    to = models.PositiveSmallIntegerField(
        choices=ToChoices.choices,
        verbose_name="acción hacia un"
    )
    app_label = models.CharField(
        max_length=128,
        verbose_name="aplicación"
    )
    name = models.CharField(max_length=128, verbose_name='nombre de la acción') 
    element = models.CharField(
        max_length=128,
        verbose_name='elemento accionado'
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name="permisos específicos"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "acción"
        verbose_name_plural = "acciones"
        unique_together = ("app_label", "element")
        ordering = ("name",)

    def get_model_class(self):
        if self.to != self.ToChoices.MODEL:
            return None
        try:
            model_class = apps.get_model(self.app_label, self.element)
            return model_class
        except LookupError:
            return None

    def get_view_class(self):
        if self.to != self.ToChoices.CLASSVIEW:
            return None
        try:
            app_config = apps.get_app_config(self.app_label)
            view_class = import_class(f"{app_config.name}.views", self.element)
            return view_class
        except (LookupError):
            return None

    def get_permissions(self):
        return [f"auth.{perm.codename}" for perm in self.permissions.all()]

    def has_permissions(self, user):
        if not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser:
            return True

        if self.to == self.ToChoices.MODEL:
            basic_perms = any(
                user.has_perm(f"{self.app_label}.{perm}_{self.element}") 
                for perm in ("view", "add", "change", "delete")
            )
        else:
            basic_perms = True

        specific_perms = all(
            user.has_perm(perm) for perm in self.get_permissions()
        )

        return basic_perms and specific_perms

    
class Menu(models.Model):
    """ Models for menu """

    parent = models.ForeignKey(
        'self',
        blank=True, null=True,
        related_name='submenus',
        on_delete=models.CASCADE,
        verbose_name='menú padre'
    )
    name = models.CharField(max_length=128, verbose_name='nombre')
    route = models.CharField(
        max_length=512,
        unique=True, editable=False,
        verbose_name='ruta de acceso'
    )
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        verbose_name='acción'
    )
    icon_class = models.CharField(
        max_length=128,
        blank=True, null=True, 
        verbose_name='clase css del ícono'
    )
    is_group = models.BooleanField(
        default=False, editable=False,
        verbose_name="agrupa"
    )
    sequence = models.PositiveSmallIntegerField(verbose_name='secuencia')
    is_active = models.BooleanField(default=True, verbose_name='activo?')

    class Meta:
        ordering = ('route', 'sequence')

    def __str__(self):
        return f"{self.name} | {self.get_route()}" 

    def get_route(self):
        route = f"{self.parent.get_route()}/{slugify(self.name)}" if self.parent else slugify(self.name)
        return route

    def get_url(self):
        url_name = None
        if self.action.to == Action.ToChoices.MODEL:
            model_class = self.action.get_model_class()
            if model_class and model_class in site._registry:
                model_site = site._registry[model_class]
                url_name = model_site.get_url_name("list")
        else:
            url_name = f"site:{slugify(self.name)}"
        try:
            url = reverse(url_name)
            return url
        except NoReverseMatch:
            print("Not found url for %s" % url_name)

        return url_name
