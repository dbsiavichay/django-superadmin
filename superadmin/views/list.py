""" List view engine"""

# Python
import operator
from functools import reduce

# Django
from django.core.paginator import InvalidPage
from django.db.models import Q
from django.http import Http404
from django.utils.translation import gettext as _
from django.views.generic import ListView as BaseListView


# Local

from .base import SiteView, get_base_view
from ..shortcuts import get_urls_of_site
from ..utils import import_mixin, import_all_mixins

# Utilities
from ..services import FieldService


class ListMixin:
    """Define class"""

    allow_empty = True
    action = "list"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_params = self.request.GET
        if search_params:
            params = search_params.dict()
            search = params.pop("search", None)
            params.pop("page", None)
            params.pop("paginate_by", None)
            model_site = self.site
            if (
                search
                and hasattr(model_site, "search_params")
                and isinstance(model_site.search_params, (list, tuple))
                and model_site.search_params
            ):
                search = search.replace("+", ",").replace(";", ",")
                search_split = search.split(",")
                for search_value in search_split:
                    filters = {
                        key: search_value.strip() for key in model_site.search_params
                    }
                    params.update(**filters)
                    args = [Q(**{key: value}) for key, value in filters.items()]
                    queryset = queryset.filter(reduce(operator.__or__, args))
        return queryset

    def paginate_queryset(self, queryset, page_size):
        """Paginate the queryset, if needed."""
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == "last":
                page_number = paginator.num_pages
            else:
                raise Http404(
                    _("Page is not “last”, nor can it be converted to an int.")
                )
        try:
            if page_number > paginator.num_pages:
                page_number = paginator.num_pages
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage as e:
            raise Http404(
                _("Invalid page (%(page_number)s): %(message)s")
                % {"page_number": page_number, "message": str(e)}
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.site.list_extra_context)
        opts = {
            "fields": self.get_list_fields(),
            "rows": self.get_rows(context["object_list"]),
            "page_start_index": context["page_obj"].start_index()
            if context["is_paginated"]
            else 1,
            "page_end_index": context["page_obj"].end_index()
            if context["is_paginated"]
            else context["object_list"].count(),
            "total_records": context["paginator"].count
            if context["is_paginated"]
            else context["object_list"].count(),
        }
        if (
            hasattr(self.site, "search_params")
            and isinstance(self.site.search_params, (list, tuple))
            and self.site.search_params
        ):
            opts.update({"search_params": self.site.search_params})
        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({"site": opts})

        return context

    def get_paginate_by(self, queryset):
        paginate_by = self.request.GET.get("paginate_by")
        if paginate_by:
            return paginate_by
        return super().get_paginate_by(queryset)

    def get_list_fields(self):
        fields = [
            (name, FieldService.get_field_label(self.model, name))
            for name in self.site.list_fields
        ]
        return fields

    def get_editable_fields(self):
        fields = [
            (name, FieldService.get_field_label(self.model, name))
            for name in self.site.form_class._meta.fields
        ]
        return fields

    def get_rows(self, queryset):
        rows = [
            {
                "instance": instance,
                "values": self.get_values(instance),
                "urls": get_urls_of_site(
                    self.site, object=instance, user=self.request.user
                ),
            }
            for instance in queryset
        ]
        return rows

    def get_values(self, instance):
        values = [
            FieldService.get_field_value(instance, name)
            for name in self.site.list_fields
        ]
        return values


class ListView(SiteView):
    def view(self, request, *args, **kwargs):
        """Crear la List View del modelo"""
        # Class
        FilterMixin = import_mixin("FilterMixin")
        mixins = import_all_mixins() + [FilterMixin, ListMixin]
        View = get_base_view(BaseListView, mixins, self.get_site())

        # Set attriburtes
        View.paginate_by = self.site.paginate_by

        View.__bases__ = (*self.site.list_mixins, *View.__bases__)

        view = View.as_view()
        return view(request, *args, **kwargs)
