# Django
from django.apps import apps
from django.forms import modelform_factory
from django.views.generic import View
from django.http import JsonResponse
from django.template.loader import render_to_string

# Local
from ..sites import site


class RenderFieldView(View):
    http_method_names = ["get"]

    def get_form_class(self, **kwargs):
        self.field_name = kwargs.get("field")
        app_name = kwargs.get("app")
        model_name = kwargs.get("model")
        model = apps.get_model(app_name, model_name)

        if site.is_registered(model):
            modelsite = site.get_modelsite(model)
            if modelsite.form_class:
                if self.field_name in modelsite.form_class._meta.fields:
                    return modelsite.form_class
        form_class = modelform_factory(model, fields=(self.field_name,))
        return form_class

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class(**kwargs)
        form = form_class()
        context = {"field": form[self.field_name]}
        template = render_to_string("superadmin/field.html", context=context)
        res = {"template": template}
        return JsonResponse(res, status=200)
