""" """
# Django
from django.views.generic import View
from django.views.generic import DeleteView as BaseDeleteView

# Local
from .base import get_base_view
from ..shortcuts import get_urls_of_site
from ..utils import import_all_mixins

class DeleteMixin:
    """Definimos la clase que utilizará el modelo"""

    action = "delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        opts = {
            "urls": get_urls_of_site(self.site, self.object),
        }

        if "site" in context:
            context["site"].update(opts)
        else:
            context.update({
                "site": opts
            })
        return context

    def get_success_url(self):
        urls = get_urls_of_site(self.site, self.object)
        return urls.get(self.site.delete_success_url)


class DeleteView(View):
    site = None

    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [DeleteMixin]
        View = get_base_view(BaseDeleteView, mixins, self.site)
        
        # Set attribures

        view = View.as_view()
        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)

