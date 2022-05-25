""" """
# Python
from datetime import datetime

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
        return JsonResponse(
            {
                "lookups": lookups,
                "choices": choices,
                "type": FieldService.get_field_type(model, self.field),
            }
        )

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


class SessionView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        params = self.save_params()
        return JsonResponse(params)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.app_name = kwargs.get("app")
        self.model_name = kwargs.get("model")

    def save_params(self):
        model = apps.get_model(self.app_name, self.model_name)
        params = {}
        for key, value in self.request.POST.items():
            if key != "csrfmiddlewaretoken":
                clean_key = key.split("__")
                if clean_key:
                    clean_key = clean_key[0]
                    field = FieldService.get_field_type(model, clean_key)
                    if field == "DateField":
                        datetime_object = datetime.strptime(value, "%d/%m/%Y").strftime(
                            "%Y-%m-%d"
                        )
                        params.update({key: datetime_object})
                    else:
                        params.update({key: value})
        filters = self.request.session.get("filters", [])
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for elem in filters:
            if elem["app"] == self.app_name and elem["model"] == self.model_name:
                elem["params"] = params
                elem["last_date"] = now
                break
        else:
            filters.append(
                {
                    "app": self.app_name,
                    "model": self.model_name,
                    "params": params,
                    "last_date": now,
                }
            )
        self.request.session["filters"] = filters
        return params
