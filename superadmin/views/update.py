""" Update View engine """
# Django
from django.views.generic import View
from django.views.generic import UpdateView as BaseUpdateView
from django.http import HttpResponseForbidden, JsonResponse

# Local
from .base import SiteView, get_base_view
from ..shortcuts import get_urls_of_site
from ..utils import import_all_mixins, import_mixin


class UpdateMixin:
    """Update View del modelo"""

    action = "update"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.site.form_extra_context)
        return context

    def get_success_url(self):
        urls = get_urls_of_site(self.site, self.object)
        return urls.get(self.site.update_success_url)


class UpdateView(SiteView):
    def view(self, request, *args, **kwargs):
        """ Crear la List View del modelo """
        # Class
        mixins = import_all_mixins() + [UpdateMixin]
        if self.site.inlines and isinstance(self.site.inlines, dict):
            FormsetMixin = import_mixin('FormsetMixin')
            class InlineMixin(FormsetMixin):
                formsets = self.site.inlines
            mixins += [InlineMixin]

        View = get_base_view(BaseUpdateView, mixins, self.get_site())

        # Set attribures
        View.form_class = self.site.form_class
        View.fields = self.site.fields

        View.__bases__ = (*self.site.form_mixins, *View.__bases__)

        view = View.as_view()
        return view(request, *args, **kwargs)



class MassUpdateView(View):
    site = None
    http_method_names = ['post',]

    def post(self, request, *args, **kwargs):
        model = self.site.model
        ids = request.POST.getlist('ids')
        field = request.POST.get('field')
        value = request.POST.get('value')

        if not self.request.user.has_perm(f"{model._meta.app_label}.update_{model._meta.model_name}"):
            return HttpResponseForbidden()

        if not hasattr(model, field):
            return JsonResponse({'error': 'El campo indicado no existe.'}, status=400)
            
        objects = model.objects.filter(id__in=ids)
        objects.update(**{field: value})

        return JsonResponse({'success': f'{len(objects)} objectos actualizados.'}, status=200)



