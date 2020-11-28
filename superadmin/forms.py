""" Forms for menu """
# Python
import inspect

# Django
from django.forms import BaseModelForm, ChoiceField
from django.forms.models import ModelFormMetaclass as DjangoModelFormMetaclass
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.utils import flatten
from django.apps import apps

# Models
from .models import Action, Menu

#
from .management.commands.createactions import get_actions_and_elements


class ModelFormMetaclass(DjangoModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        fieldsets = None
        if "Meta" in attrs and hasattr(attrs["Meta"], "fieldsets"):
            fieldsets = attrs["Meta"].fieldsets
            fields = mcs.__fields__(fieldsets)
            if hasattr(attrs["Meta"], "fields"):
                fields = fields + attrs["Meta"].fields
            attrs["Meta"].fields = fields
        new_class = super().__new__(mcs, name, bases, attrs)
        if fieldsets:
            new_class._meta.fieldsets = fieldsets
        return new_class

    def __fields__(fieldsets):
        fields = flatten(fieldsets)
        return tuple(fields)


class ModelForm(BaseModelForm, metaclass=ModelFormMetaclass):
    def get_fieldsets(self):
        sets = list()
        for fieldset in self._meta.fieldsets:
            if isinstance(fieldset, tuple):
                sets.append({
                    'bs_cols': int(12 / len(fieldset)),
                    'fields': [self[field] for field in fieldset]
                })
            else:
                sets.append({
                    'bs_cols': 12,
                    'fields': [self[fieldset]]
                })
        return sets

    def has_fieldsets(self):
        return hasattr(self._meta, "fieldsets")


class BaseActionForm(ModelForm):
    app_label = ChoiceField(
        label="Nombre de la aplicacióp"
    )
    element = ChoiceField(
        label="Elemento"
    )

    class Meta:
        model = Action
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ct = ContentType.objects.get_for_model(Permission)
        codenames = ("add_permission","change_permission","delete_permission","view_permission")
        queryset = Permission.objects.filter(content_type=ct).exclude(codename__in=codenames)
        self.fields["permissions"].queryset = queryset

        APP_CHOICES = (
            (app.label, app.verbose_name.capitalize()) for app in apps.get_app_configs()
        )

        ELEMENT_CHOICES = [
            (element, name)
            for app in apps.get_app_configs() 
            for element, name in get_actions_and_elements(app)[1].items()
        ]

        self.fields["app_label"].choices = APP_CHOICES
        self.fields["element"].choices = ELEMENT_CHOICES


class BasePermissionForm(ModelForm):
    class Meta:
        model = Permission
        exclude = ("content_type",)

    def save(self, commit=True):
        perm = super().save(commit=False)
        ct = ContentType.objects.get_for_model(Permission)
        perm.content_type = ct
        if commit:
            perm.save()
        return perm
