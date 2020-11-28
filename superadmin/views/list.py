""" List view engine"""
# Django
from django.views.generic import View
from django.views.generic import ListView as BaseListView


# Local
from .base import get_base_view
from ..shortcuts import get_urls_of_site
from ..utils import import_all_mixins

# Utilities
from ..utils import (
    get_label_of_field,
    get_attr_of_object,
)


class ListMixin:
    """Definimos la clase que utilizará el modelo"""

    action = "list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        opts = {
            "headers": self.get_headers(),
            "rows": self.get_rows(context["object_list"]),
            "page_start_index":context["page_obj"].start_index() if context["is_paginated"] else 1,
            "page_end_index":context["page_obj"].end_index() if context["is_paginated"] else context["object_list"].count(),
            "total_records": context["paginator"].count if context["is_paginated"] else context["object_list"].count(),
        }

        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({
                "site": opts
            })
    
        return context

    def get_headers(self):
        for name in self.site.list_fields:
            yield get_label_of_field(self.model, name)

    def get_rows(self, queryset):
        for instance in queryset:
            urls = get_urls_of_site(self.site, instance)
            row = {
                "instance": instance,
                "values": self.get_values(instance),
                "urls": urls,
            }

            yield row

    def get_values(self, instance):
        for name in self.site.list_fields:
            value = get_attr_of_object(instance, name)
            yield value

class ListView(View):
    site = None

    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [ListMixin]
        View = get_base_view(BaseListView, mixins, self.site)
        
        # Set attriburtes
        View.queryset = self.site.queryset
        View.paginate_by = self.site.paginate_by

        View.__bases__ = (*self.site.list_mixins, *View.__bases__)

        view = View.as_view()
        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
