""" List view engine"""
# Django
from django.views.generic import ListView as BaseListView


# Local
from .base import SiteView, get_base_view
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
        context.update(self.site.list_extra_context)

        opts = {
            "fields": self.get_list_fields(),
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
    
    def get_paginate_by(self, queryset):
        paginate_by = self.request.GET.get("paginate_by")
        if paginate_by:
            return paginate_by
        return super().get_paginate_by(queryset)

    def get_list_fields(self):
        fields = [(name, get_label_of_field(self.model, name)) for name in self.site.list_fields]
        return fields

    def get_editable_fields(self):
        fields = [(name, get_label_of_field(self.model, name)) for name in self.site.form_class._meta.fields]
        return fields

    def get_rows(self, queryset):
        rows = [
            {
                "instance": instance,
                "values": self.get_values(instance),
                "urls": get_urls_of_site(self.site, instance),
            }
            for instance in queryset    
        ]
        return rows

    def get_values(self, instance):
        values = [get_attr_of_object(instance, name) for name in self.site.list_fields]
        return values


class ListView(SiteView):
    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [ListMixin]
        View = get_base_view(BaseListView, mixins, self.get_site())
        
        # Set attriburtes
        View.queryset = self.site.queryset
        View.paginate_by = self.site.paginate_by

        View.__bases__ = (*self.site.list_mixins, *View.__bases__)

        view = View.as_view()
        return view(request, *args, **kwargs)
        
