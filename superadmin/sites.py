"""Classes and functios for register site models"""

# Django
from django.utils.text import slugify
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.db import connection
from django.urls import path, include 
from django.apps import apps

from .utils import import_mixin


class Site:
    """Site class"""

    def __init__(self, name="site"):
        self._registry = {}
        self.name = name

    def register(self, model, site_class):
        """Registra las clases en el auto site"""
        if isinstance(model, str):
            try:
                app_label, model_name = model.split(".")
                model = apps.get_model(app_label, model_name)
            except ValueError:
                raise Exception(
                    "The model_name passed must be contains app label and model name like 'app_label.model_name'"
                )
        if not isinstance(model, ModelBase):
            raise Exception(
                "The model passed cannot be registered but not is a model."
            )

        if model._meta.abstract:
            raise ImproperlyConfigured(
                "The model %s is abstract, so it cannot be registered with superadmin."
                % model.__name__
            )

        if model in self._registry:
            raise Exception('The model %s is already registered' % model.__name__)

        self._registry[model] = site_class(model)

    def is_registered(self, model):
        """
        Check if a model class is registered with this `Site`.
        """
        return model in self._registry

    def get_modelsite(self, model):
        if not isinstance(model, ModelBase):
            raise Exception("The model passed is not a Model.")
        
        if not self.is_registered(model):
            raise Exception('The model %s is not registered' % model.__name__)

        return self._registry[model]

    def get_model_urls(self, menu):
        urlpatterns = []
        model = menu.action.get_model_class()
        if model and model in self._registry:
            model_site = self._registry[model]
            urlpatterns = [
                path(f"{menu.route}/", include(model_site.urls))
            ]
       
        return urlpatterns

    def get_view_urls(self, menu):
        from django.contrib.auth.mixins import PermissionRequiredMixin
        urlpatterns = []
        mixin = import_mixin("BreadcrumbMixin")
        view = menu.action.get_view_class()
        view.menu = None
        if PermissionRequiredMixin not in view.__bases__:
            view.__bases__ = (PermissionRequiredMixin, mixin, *view.__bases__)
        
        view.permission_required = menu.action.get_permissions()
        if view:
            urlpatterns = [
                path(
                    route=f"{menu.route}/",
                    view=view.as_view(menu=menu),
                    name=slugify(menu.name),
                )
            ]
       
        return urlpatterns

    def get_menu_urls(self, menu):
        urlpatterns = []
        if menu.action.to == menu.action.ToChoices.MODEL:
            urlpatterns.extend(self.get_model_urls(menu))
        else:
            urlpatterns.extend(self.get_view_urls(menu))

        return urlpatterns

    def get_menus(self):
        menus = None
        try:
            Menu = apps.get_model("superadmin", "Menu")
            if Menu._meta.db_table in connection.introspection.table_names():
                menus = Menu.objects.all()
        except LookupError as error:
            print(error)
            menus = None
        return menus

    def get_urls(self):
        """Obtiene las urls de auto site"""

        # def wrap(view, cacheable=False):
        #   def wrapper(*args, **kwargs):
        #       return self.admin_view(view, cacheable)(*args, **kwargs)
        #       wrapper.admin_site = self
        #       return update_wrapper(wrapper, view)

        urlpatterns = []
        menus = self.get_menus()
        if menus:
            for menu in menus:
                urlpatterns.extend(self.get_menu_urls(menu))
        else:
            for model, model_site in self._registry.items():
                info = model_site.get_info()
                url_format = "%s/%s/" % info
                urlpatterns += [path(url_format, include(model_site.urls))]

        return urlpatterns

    @property
    def urls(self):
        """Permite registrar las URLs en el archivo de urls del proyecto"""
        return self.get_urls(), 'site', self.name


site = Site()
