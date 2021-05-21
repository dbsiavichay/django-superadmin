""" """
# Django
from django.apps import apps
from django.http import JsonResponse
from django.views.generic import View

# Local
from ..services import FieldService, FilterService


class FilterView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        model = apps.get_model(self.app_name, self.model_name)
        lookups = self.get_lookups(model, self.field)
        choices = self.get_choices(model, self.field)
        return JsonResponse({"lookups": lookups, "choices": choices})

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.app_name = kwargs.get("app")
        self.model_name = kwargs.get("model")
        self.field = kwargs.get("field")

    def get_lookups(self, model, field):
        lookups = [
            {"id": lookup, "text": label}
            for lookup, label in FilterService.get_field_lookups(model, field)
        ]
        return lookups

    def get_choices(self, model, field):
        choices = FilterService.get_choices(model, field)
        if hasattr(choices, "model"):
            choices = [{"id": obj.id, "text": str(obj)} for obj in choices]
        else:
            choices = [{"id": value, "text": label} for value, label in choices]
        return choices
