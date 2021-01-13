"""Mixins for formsets"""

# Django
from django.shortcuts import redirect
from django.db import transaction
from django.contrib import messages

#Utils
from superadmin.utils import get_label_of_field


class FormsetList:
    formsets = dict()

    """
    formsets = {
        "invoice_formset": Formset
    }
    """

    def __init__(self, formsets):
        self.formsets = dict()

        for key, formset_class in formsets.items():
            self.formsets.update({
                key: {
                    "class": formset_class,
                }
            })

    def is_valid(self):
        errors = [fs["instance"].errors for fs in self.formsets.values() if not fs["instance"].is_valid()]
        return not errors

    def get_headers(self):
        headers = {
            f"{key}_headers": value["headers"]
            for key, value in self.formsets.items()
        }
        return headers

    def get_instances(self, **kwargs):
        related_initial = None
        if 'initial' in kwargs and 'related_initial' in kwargs['initial']:
            related_initial = kwargs.get('initial').get('related_initial')  

        for key in self.formsets:
            formset_class = self.formsets[key]["class"]
            if related_initial :
                kwargs['initial'] = related_initial.get(formset_class.model, [])
            else:
                kwargs['initial'] = []
            instance = formset_class(**kwargs)
            instance.extra += len(kwargs['initial'])

            headers = [
                get_label_of_field(formset_class.form.Meta.model, field.name)
                for field in instance.empty_form.visible_fields()
                if field.name in formset_class.form.Meta.fields
            ]
            self.formsets.get(key).update({
                "instance": instance,
                "headers": headers,
            })

        instances = {
            key: value["instance"]
            for key, value in self.formsets.items()
        }
        return instances

    def get_formset(self, name):
        return self.formsets[name]["instance"]


class FormsetMixin:
    """Class for add multiple formsets in form"""

    formsets = dict()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.formsets = FormsetList(formsets=self.formsets)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        formsets = self.get_formsets()
        headers = self.get_headers()
        context.update(
            **formsets, **headers
        )
        return context

    def formsets_valid(self, formsets, form):
        with transaction.atomic():
            self.object = form.save()
            for formset in formsets:
                formset.instance = self.object
                formset.save()

        messages.success(self.request, "Se ha guardado correctamente.")
        return redirect(self.get_success_url())

    def formsets_invalid(self, formsets, form):
        for formset in formsets:
            for error in formset.errors:
                form.errors.update(error)
        return super().form_invalid(form)

    def get_headers(self):
        headers = self.formsets.get_headers()
        return headers

    def get_formsets(self):
        """Method to get all formsets"""
        formsets = self.formsets.get_instances(**self.get_form_kwargs())
        return formsets

    def get_formset(self, name):
        return self.formsets.get_formset(name)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if self.action == "update" else None
        form = self.get_form()
        formsets = self.get_formsets().values()

        if self.formsets.is_valid() and form.is_valid():
            return self.formsets_valid(formsets, form)
        else:
            return self.formsets_invalid(formsets, form)
