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

    def get_params(self, exclude=False):
        DEFAULT = "search"
        EXCLUDE = "__exclude"
        params = {}
        if DEFAULT in self.request.GET:
            params[DEFAULT] = self.request.GET.get(DEFAULT)
            return params
        lookup_params = {
            key: value
            for key, value in self.request.GET.items()
            if self.has_lookup(key)
        }
        for key, value in lookup_params.items():
            lookup = self.has_lookup(key)
            type = FieldService.get_field_type(
                self.site.model, key.split(f"__{lookup}")[0]
            )
            if type == "BooleanField":
                try:
                    value = bool(int(value))
                except ValueError:
                    value = False
            if exclude:
                if EXCLUDE in key:
                    params[key.split(EXCLUDE)[0]] = value
            elif EXCLUDE not in key:
                params[key] = value
        return params

    def get_query(self, exclude=False):
        args = []
        params = self.get_params(exclude=exclude)
        op = operator.__or__
        if "search" in params:
            value = params.get("search")
            for field in self.site.search_fields:
                args.append(Q(**{field: value}))
        else:
            for field, value in params.items():
                args.append(Q(**{field: value}))
            op = operator.__and__
        if args:
            return reduce(op, args)
        return args

    def get_queryset(self):
        queryset = super().get_queryset()
        self.all_records = queryset.count()
        query = self.get_query()
        if query:
            queryset = queryset.filter(query)
        exclude = self.get_query(exclude=True)
        if exclude:
            queryset = queryset.exclude(exclude)
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
        params = {
            **self.get_params(exclude=True),
            **self.get_params(exclude=False),
        }
        if "search" in params:
            return filters
        for key, value in params.items():
            lookup = self.has_lookup(key)
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
                    search_label = str(choices.get(pk=value))
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

    def has_lookup(self, field):
        for lookup in FilterService.get_flatten_lookups():
            if lookup in field:
                return lookup
