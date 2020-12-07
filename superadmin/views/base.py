# Django
from django.views.generic import TemplateView, View
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.contrib import messages

# Utils
from ..utils import get_user_menu

class SiteView(View):
    site = None

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)

    def get_site(self):
        return self.site

class ModuleView(TemplateView):
    """Clase para definir las vistas de los módulos de aplicaciones"""
    menu = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        opts = {"title": self.menu.name}
        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({
                "site": opts
            })
            
        data = {
            "object_list": get_user_menu(self.menu.submenus.all(), self.request.user)
        }

        context.update(data)

        return context

    def get_template_names(self):
        template_name = "superadmin/module_list.html"
        if hasattr(settings, "MODULE_TEMPLATE_NAME"):
            template_name = settings.MODULE_TEMPLATE_NAME
        return [template_name]


def get_base_view(ClassView, mixins, site):
    class View(ClassView):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            opts = {
                "title": self.model._meta.verbose_name_plural,
                "app_name": self.model._meta.app_label,
                "model_name": self.model._meta.model_name,
            }

            if "site" in context:
                context["site"].update(opts)
            else:
                context.update({
                    "site": opts
                })
            return context

        def form_valid(self, form):
            messages.success(self.request, "Se ha guardado correctamente.")
            return super().form_valid(form)


    View.__bases__ = (*mixins, *View.__bases__)
    View.site = site
    View.model = site.model
    return View
