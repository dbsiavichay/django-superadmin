# Python
from functools import reduce

# Django
from django.forms import BaseModelForm
from django.forms.models import ModelFormMetaclass as DjangoModelFormMetaclass
from django.contrib.admin.utils import flatten
from django.core.exceptions import ImproperlyConfigured


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
        if isinstance(fieldsets, (list, tuple)):
            fields = flatten(fieldsets)
        elif isinstance(fieldsets, dict):
            fields = reduce(
                lambda acc, fieldset: acc + flatten(fieldset), fieldsets.values(), []
            )
        else:
            raise ImproperlyConfigured(
                "The fieldsets must be an instance of list, tuple or dict"
            )
        return tuple(fields)


class ModelForm(BaseModelForm, metaclass=ModelFormMetaclass):
    def parse(self, fieldset):
        def wrap(fields):
            fields = fields if isinstance(fields, (list, tuple)) else [fields]
            return {
                "bs_cols": int(12 / len(fields)),
                "fields": [self[field] for field in fields],
            }

        fieldset_list = list(map(wrap, fieldset))
        return fieldset_list

    def get_fieldsets(self):
        fieldsets_list = self._meta.fieldsets
        fieldsets = (
            [(None, fieldsets_list)]
            if isinstance(fieldsets_list, (list, tuple))
            else fieldsets_list.items()
        )
        fieldsets = [
            {"title": title or "", "fieldset": self.parse(fieldset)}
            for title, fieldset in fieldsets
        ]

        return fieldsets

    def has_fieldsets(self):
        return hasattr(self._meta, "fieldsets")
