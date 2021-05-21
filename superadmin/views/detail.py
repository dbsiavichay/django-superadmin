""" """
# Django
from django.views.generic import DetailView as BaseDetailView
from django.contrib.admin.utils import flatten

# Local
from .base import SiteView, get_base_view
from ..services import FieldService
from ..utils import import_all_mixins


class DetailMixin:
    """Definimos la clase que utilizará el modelo"""

    action = "detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.site.detail_extra_context)

        flatten_results, fieldset_results = self.get_results()
        opts = {
            "results": fieldset_results,
            "flatten_results": flatten_results,
        }

        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({"site": opts})

        return context

    def get_results(self):
        fields = flatten(self.site.detail_fields)
        fields = fields if fields else (field.name for field in self.model._meta.fields)
        results = {}
        for field in fields:
            label = FieldService.get_field_label(self.object, field)
            value = FieldService.get_field_value(self.object, field)
            type = FieldService.get_field_type(self.object, field)
            results[field] = (label, value, type)

        flatten_results = results.values()
        fieldset_results = []
        for fieldset in self.site.detail_fields:
            if isinstance(fieldset, (list, tuple)):
                fieldset_results.append(
                    {
                        "bs_cols": int(12 / len(fieldset)),
                        "fields": [results.get(field, ()) for field in fieldset],
                    }
                )
            else:
                fieldset_results.append(
                    {
                        "bs_cols": 12,
                        "fields": [
                            results.get(fieldset, ()),
                        ],
                    }
                )

        return flatten_results, fieldset_results

    def get_slug_field(self):
        return self.site.slug_field or super().get_slug_field()


class DetailView(SiteView):
    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [DetailMixin]
        View = get_base_view(BaseDetailView, mixins, self.site)

        # Set attributes
        View.__bases__ = (*self.site.detail_mixins, *View.__bases__)

        view = View.as_view()
        return view(request, *args, **kwargs)
