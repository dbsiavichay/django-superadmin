
# Django
from django.urls import reverse_lazy
from django.utils.html import format_html

# Shortcuts
from superadmin.shortcuts import get_slug_or_pk

# Utils
from superadmin.utils import import_class
from superadmin import settings

class BreadcrumbMixin:
    """Clase base que contiene la información común de todas las subclases"""

    def get_menu_in_path(self, path):
        Menu = import_class("superadmin.models", "Menu")
        if not Menu: return
        if not path: return

        try:
            menu = Menu.objects.get(route=path)
            return menu
        except Menu.DoesNotExist:
            path = "/".join(path.split("/")[0: -1])
            return self.get_menu_in_path(path)

    def get_breadcrumb_text(self, action):
        attr = "breadcrumb_%s_text" % action
        if hasattr(self, "site"):
            text = getattr(self.site, attr, "")
        else:
            text = getattr(settings, attr.upper(), "")

        return format_html(text)

    def get_base(self, menu):
        base = [(menu.name, f"/{menu.route}/")]
        if menu.parent:
            base =  self.get_base(menu.parent) + base
        return base

    def get_base_breadcrumbs(self):
        base_breadcrumbs = [(self.get_breadcrumb_text("home"), "/")]

        menu = self.get_menu_in_path(self.request.path[1:-1])
        if not menu: return base_breadcrumbs
        base_breadcrumbs.extend(self.get_base(menu))
        return base_breadcrumbs

    def get_create_breadcrumbs(self):
        breadcrumbs = self.get_base_breadcrumbs()
        breadcrumbs.append((self.get_breadcrumb_text(self.action), "#"))
        return breadcrumbs

    def get_update_breadcrumbs(self):
        breadcrumbs = self.get_detail_breadcrumbs()
        breadcrumbs.append((self.get_breadcrumb_text(self.action), "#"))
        return breadcrumbs

    def get_list_breadcrumbs(self):
        return self.get_base_breadcrumbs()

    def get_detail_breadcrumbs(self):
        """Obtiene el breadcumb para Detail View"""
        url_name = self.site.get_url_name("detail")
        breadcrumbs = self.get_list_breadcrumbs()
        breadcrumbs.append(
            (
                self.get_breadcrumb_text("detail") or str(self.object),
                reverse_lazy(url_name, kwargs=get_slug_or_pk(self.object),),
            )
        )
        return breadcrumbs

    def get_delete_breadcrumbs(self):
        breadcrumbs = self.get_detail_breadcrumbs()
        breadcrumbs.append((self.get_breadcrumb_text(self.action), "#"))
        return breadcrumbs

    def get_breadcrumbs(self):
        if hasattr(self, "action"):
            attr = getattr(self, "get_%s_breadcrumbs" % self.action)
            return attr()
        return self.get_base_breadcrumbs()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        breadcrumbs = {
            "breadcrumbs" : self.get_breadcrumbs()
        }

        if "site" in context:
            context["site"].update(breadcrumbs)
        else:
            context.update({
                "site": breadcrumbs
            })
        return context
