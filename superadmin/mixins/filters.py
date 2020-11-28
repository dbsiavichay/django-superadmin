# Python
import operator
from functools import reduce

# Django
from django.db.models import Q


class FilterMixin:
    def get_params(self, value):
        args = []
        for field in self.site.search_fields:
            args.append(Q(**{field: value}))
        if args:
            return reduce(operator.__or__, args)
        return args

    def get_queryset(self):
        queryset = super().get_queryset()
        search_value = self.request.GET.get("search")
        if search_value:
            args = self.get_params(search_value)
            if args:
                queryset = queryset.filter(args)
        return queryset


    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        opts = {
            "order_by": self._get_headers(),
            "search_fields": self._get_search_fields_with_labels(),
            "active_searches": self._clean_search_params(),
        }

        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({
                "site": opts
            })
    
        return context

    def reduce_queryset(self, params, queryset, op):
        args = []
        for field, value, verbose_name in params:
            action = '__icontains'
            if self.model._meta.get_field(field).__class__.__name__ in (
                'CharField',
                'TextField',
            ):
                action = '__unaccent' + action
            args.append(Q(**{field + action: value}))
        if args:
            queryset = queryset.filter(reduce(op, args))
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()

        params = self._clean_search_params()
        if 'sf' in self.request.GET:
            return self.reduce_queryset(params, queryset, operator.__or__)

        queryset = self.reduce_queryset(params, queryset, operator.__and__)
        return queryset

    def _clean_search_params(self):
        params = []
        if 'sf' in self.request.GET:
            value = self.request.GET.get('sf')
            for field in self.site.search_fields:
                verbose_name = get_field_label_of_model(
                    self.site.model, '.'.join(field.split('__'))
                )
                params.append((field, value, verbose_name))
            return params

        for key in self.request.GET.keys():
            if key.startswith('sf_') and key[3:] in self.site.search_fields:
                field = key[3:]
                verbose_name = get_field_label_of_model(
                    self.site.model, '.'.join(field.split('__'))
                )
                params.append((field, self.request.GET.get(key), verbose_name))
        return params

    def _get_search_fields_with_labels(self):
        fields = []
        for field in self.site.search_fields:
            point_field = '.'.join(field.split('__'))
            fields.append(
                (
                    f'sf_{field}',
                    get_field_label_of_model(self.model, point_field),
                )
            )
        return fields
    """