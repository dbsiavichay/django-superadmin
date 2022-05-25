""" """
# Python
from functools import reduce

# Django
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import DetailView as BaseDetailView
from django.contrib.admin.utils import flatten

# Local
from .base import SiteView, get_base_view
from ..services import FieldService, FilterService
from ..utils import import_all_mixins
from ..shortcuts import get_urls_of_site


class DetailMixin:
    """Definimos la clase que utilizará el modelo"""

    action = "detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.site.detail_extra_context)
        flatten_results, fieldset_results = self.get_results()
        params = FilterService.get_params(self.site.model, self.request.session)
        queryset = FilterService.filter(self.site.queryset, params)
        nav = FilterService.get_previous_and_next(queryset, self.object)
        if nav:
            nav["previous_url"] = (
                get_urls_of_site(self.site, nav["previous"])[self.action]
                if nav.get("previous")
                else None
            )
            nav["next_url"] = (
                get_urls_of_site(self.site, nav["next"])[self.action]
                if nav.get("next")
                else None
            )
        opts = {
            "results": fieldset_results,
            "flatten_results": flatten_results,
            "nav": nav,
        }

        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({"site": opts})

        return context

    def get_results(self):
        if isinstance(self.site.detail_fields, (list, tuple)):
            fields = flatten(self.site.detail_fields)
        elif isinstance(self.site.detail_fields, dict):
            fields = reduce(
                lambda acc, fieldset: acc + flatten(fieldset),
                self.site.detail_fields.values(),
                [],
            )
        else:
            raise ImproperlyConfigured(
                "The fieldsets must be an instance of list, tuple or dict"
            )
        fields = fields if fields else (field.name for field in self.model._meta.fields)
        results = {
            field: (
                FieldService.get_field_label(self.object, field),
                FieldService.get_field_value(self.object, field),
                FieldService.get_field_type(self.object, field),
                field,
            )
            for field in fields
        }

        flatten_results = results.values()

        def parse(fieldset):
            def wrap(fields):
                fields = fields if isinstance(fields, (list, tuple)) else [fields]
                return {
                    "bs_cols": int(12 / len(fields)),
                    "fields": [results.get(field, ("", "", "")) for field in fields],
                }

            fieldset_list = list(map(wrap, fieldset))
            return fieldset_list

        fieldsets_list = self.site.detail_fields
        fieldsets = (
            [(None, fieldsets_list)]
            if isinstance(fieldsets_list, (list, tuple))
            else fieldsets_list.items()
        )
        fieldsets_results = [
            {"title": title or "", "fieldset": parse(fieldset)}
            for title, fieldset in fieldsets
        ]

        return flatten_results, fieldsets_results

    def get_slug_field(self):
        return self.site.slug_field or super().get_slug_field()


class DetailView(SiteView):
    def view(self, request, *args, **kwargs):
        """Crear la List View del modelo"""
        # Class
        mixins = import_all_mixins() + [DetailMixin]
        View = get_base_view(BaseDetailView, mixins, self.site)

        # Set attributes
        View.__bases__ = (*self.site.detail_mixins, *View.__bases__)
        view = View.as_view()
        return view(request, *args, **kwargs)
