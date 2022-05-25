""" Update View engine """
# Django
from django.views.generic import View
from django.views.generic import UpdateView as BaseUpdateView
from django.http import HttpResponseForbidden, JsonResponse

# Local
from .base import SiteView, get_base_view
from ..services import FilterService
from ..shortcuts import get_urls_of_site
from ..utils import import_all_mixins, import_mixin


class UpdateMixin:
    """Update View del modelo"""

    action = "update"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        opts = {"nav": nav}
        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({"site": opts})
        context.update(self.site.form_extra_context)
        return context

    def get_slug_field(self):
        return self.site.slug_field or super().get_slug_field()

    def get_success_url(self):
        urls = get_urls_of_site(self.site, object=self.object)
        return urls.get(self.site.update_success_url)


class UpdateView(SiteView):
    def view(self, request, *args, **kwargs):
        """Crear la List View del modelo"""
        # Class
        mixins = import_all_mixins() + [UpdateMixin]
        if self.site.inlines and isinstance(self.site.inlines, (list, tuple, dict)):
            InlinesMixin = import_mixin("InlinesMixin")

            class Inlines(InlinesMixin):
                inlines = self.site.inlines

            mixins += [Inlines]

        View = get_base_view(BaseUpdateView, mixins, self.get_site())

        # Set attribures
        View.form_class = self.site.form_class
        View.fields = self.site.fields
        if self.site.update_mixins:
            View.__bases__ = (*self.site.update_mixins, *View.__bases__)
        else:
            View.__bases__ = (*self.site.form_mixins, *View.__bases__)
        view = View.as_view()
        return view(request, *args, **kwargs)


class MassUpdateView(View):
    site = None
    http_method_names = [
        "post",
    ]

    def post(self, request, *args, **kwargs):
        model = self.site.model
        ids = request.POST.getlist("ids")
        field = request.POST.get("field")
        value = request.POST.get("value")

        if not self.request.user.has_perm(
            f"{model._meta.app_label}.update_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()

        if not hasattr(model, field):
            return JsonResponse({"error": "El campo indicado no existe."}, status=400)

        objects = model.objects.filter(id__in=ids)
        objects.update(**{field: value})

        return JsonResponse(
            {"success": f"{len(objects)} objectos actualizados."}, status=200
        )
