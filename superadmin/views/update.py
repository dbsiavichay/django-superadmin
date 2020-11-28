""" Update View engine """
# Django
from django.views.generic import View
from django.views.generic import UpdateView as BaseUpdateView

# Local
from .base import get_base_view
from ..shortcuts import get_urls_of_site
from ..utils import import_all_mixins


class UpdateMixin:
    """Update View del modelo"""

    action = "update"

    def get_success_url(self):
        urls = get_urls_of_site(self.site, self.object)
        return urls.get(self.site.update_success_url)


class UpdateView(View):
    site = None

    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [UpdateMixin]
        View = get_base_view(BaseUpdateView, mixins, self.site)

        # Set attribures
        View.form_class = self.site.form_class
        View.fields = self.site.fields

        View.__bases__ = (*self.site.form_mixins, *View.__bases__)

        view = View.as_view()
        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)