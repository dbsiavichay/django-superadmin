""" """
# Django
from django.views.generic import View
from django.views.generic import DeleteView as BaseDeleteView
from django.http import HttpResponseForbidden, JsonResponse

# Local
from .base import SiteView, get_base_view
from ..shortcuts import get_urls_of_site
from ..utils import import_all_mixins


class DeleteMixin:
    """Definimos la clase que utilizará el modelo"""

    action = "delete"

    def get_slug_field(self):
        return self.site.slug_field or super().get_slug_field()

    def get_success_url(self):
        urls = get_urls_of_site(self.site, object=self.object)
        return urls.get(self.site.delete_success_url)


class DeleteView(SiteView):
    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [DeleteMixin]
        View = get_base_view(BaseDeleteView, mixins, self.site)

        # Set attributes
        View.__bases__ = (*self.site.delete_mixins, *View.__bases__)
        view = View.as_view()
        return view(request, *args, **kwargs)


class MassDeleteView(View):
    site = None
    http_method_names = [
        "post",
    ]

    def post(self, request, *args, **kwargs):
        model = self.site.model
        ids = request.POST.getlist("ids")

        if not self.request.user.has_perm(
            f"{model._meta.app_label}.delete_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()

        objects = model.objects.filter(id__in=ids)
        objects.delete()

        return JsonResponse(
            {"success": f"{len(object)} objectos eliminados."}, status=200
        )
