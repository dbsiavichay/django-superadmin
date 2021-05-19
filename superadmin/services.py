# Django
from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import pretty_name
from django.utils.html import format_html

from . import settings


class FieldService:
    @classmethod
    def get_field_label(cls, model, field):
        names = field.split("__")
        name = names.pop(0)
        try:
            name, verbose_name = name.split(":")
            return pretty_name(verbose_name)
        except ValueError:
            pass
        if not hasattr(model, name):
            try:
                str_model = f"<{model._meta.model_name}>"
            except:
                str_model = str(model)
            raise AttributeError(f"No existe le atributo <{name}> para {str_model}.")
        if len(names):
            if hasattr(model, "_meta"):
                return cls.get_field_label(
                    model._meta.get_field(name).related_model, "__".join(names)
                )
            else:
                attr = getattr(model, name)
                return cls.get_field_label(
                    attr() if callable(attr) else attr, "__".join(names)
                )
        try:
            field = model._meta.get_field(name)
            label = field.verbose_name if hasattr(field, "verbose_name") else name
        except FieldDoesNotExist:
            label = str(model._meta.verbose_name) if name == "__str__" else name
        return pretty_name(label)

    @classmethod
    def get_field_value(cls, object, field):
        names = field.split("__")
        name = names.pop(0)
        name = name.split(":")[0]
        if not hasattr(object, name):
            raise AttributeError(f"No existe le atributo <{name}> para {str(object)}.")
        if len(names):
            return cls.get_field_value(getattr(object, name), "__".join(names))
        try:
            field = object._meta.get_field(name)
            if hasattr(field, "choices") and field.choices:
                name = f"get_{name}_display"
        except FieldDoesNotExist:
            pass
        attr = getattr(object, name)
        if hasattr(attr, "__class__") and (
            attr.__class__.__name__ == "ManyRelatedManager"
            or attr.__class__.__name__ == "RelatedManager"
        ):
            attr = [str(obj) for obj in attr.all()]
        attr = attr() if callable(attr) else attr
        if isinstance(attr, bool):
            attr = settings.BOOLEAN_YES if attr else settings.BOOLEAN_NO
        return format_html(str(attr))

    @classmethod
    def get_field_type(cls, model, field):
        names = field.split("__")
        name = names.pop(0)
        if not hasattr(model, name):
            try:
                str_model = f"<{model._meta.model_name}>"
            except:
                str_model = str(model)
            raise AttributeError(f"No existe le atributo <{name}> para {str_model}.")
        if len(names):
            if hasattr(model, "_meta"):
                return cls.get_field_type(
                    model._meta.get_field(name).related_model, "__".join(names)
                )
            else:
                attr = getattr(model, name)
                return cls.get_field_type(
                    attr() if callable(attr) else attr, "__".join(names)
                )
        try:
            field = model._meta.get_field(name)
            type = model._meta.get_field(name).get_internal_type()
        except FieldDoesNotExist:
            type = "Function"
        return type
