# Python
import operator
from functools import reduce

# Django
from django.http import Http404
from django.db.models import Q

# Local
from ..services import FieldService, FilterService


class FilterMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opts = {
            "all_records": self.all_records,
            "filter_fields": self.get_filter_fields(),
            "current_filters": self.get_current_filters(),
        }
        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({"site": opts})
        return context

    """"
    def get_query(self):
        query = []
        if "search" in self.request.GET:
            value = self.request.GET.get("search")
            for field in self.site.search_fields:
                query.append(Q(**{field: value}))
        if query:
            return reduce(operator.__or__, query)
        return query"""

    def get_queryset(self):
        queryset = super().get_queryset()
        self.all_records = queryset.count()
        params = FilterService.get_params(self.site.model, self.request.session)
        queryset = FilterService.filter(queryset, params)
        return queryset

    def get_filter_fields(self):
        fields = []
        for field in self.site.filter_fields:
            field_name = field.split(":")[0]
            fields.append(
                {
                    "name": field_name,
                    "label": FieldService.get_field_label(self.site.model, field),
                    "app_name": self.site.model._meta.app_label,
                    "model_model": self.site.model._meta.model_name,
                }
            )
        return fields

    def get_current_filters(self):
        filters = []
        params = FilterService.get_params(self.site.model, self.request.session)
        for key, value in params.items():
            lookup = FilterService.has_lookup(key)
            lookup_label = FilterService.get_lookup_label(lookup)
            field = key.split(f"__{lookup}")[0]
            for filter_field in self.site.filter_fields:
                if field in filter_field:
                    try:
                        field, field_label = filter_field.split(":")
                    except ValueError:
                        field_label = FieldService.get_field_label(
                            self.site.model, field
                        )
            if not field_label:
                raise Http404
            choices = FilterService.get_choices(self.site.model, field)
            if choices:
                search = int(value) if type(value) == bool else value
                if hasattr(choices, "model"):
                    try:
                        search_label = str(choices.get(pk=value))
                    except choices.model.DoesNotExist:
                        search_label = "[objeto eliminado]"
                else:
                    try:
                        search = int(search)
                    except ValueError:
                        pass
                    choices = dict(choices)
                    search_label = choices.get(search)
            else:
                search = value
                search_label = value

            filters.append(
                {
                    "field": field,
                    "field_label": field_label,
                    "lookup": lookup,
                    "lookup_label": lookup_label,
                    "search": search,
                    "search_label": search_label,
                }
            )
        return filters
