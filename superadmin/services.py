# Python
import operator
from functools import reduce

# Django
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.forms.utils import pretty_name
from django.utils.html import format_html
from django.db.models import Q

from . import settings


class FieldService:
    FIELD_SEPARATOR = "__"
    LABEL_SEPARATOR = ":"

    @classmethod
    def get_field(cls, model, field):
        field = field.split(cls.LABEL_SEPARATOR)[0]
        names = field.split(cls.FIELD_SEPARATOR)
        name = names.pop(0)
        try:
            if len(names):
                related_model = model._meta.get_field(name).related_model
                if related_model:
                    return cls.get_field(related_model, cls.FIELD_SEPARATOR.join(names))
                else:
                    raise ImproperlyConfigured(f"The field <{name}> not is an object")
            field = model._meta.get_field(name)
            return field
        except FieldDoesNotExist:
            str_model = (
                model._meta.model_name if hasattr(model, "_meta") else str(model)
            )
            raise AttributeError(f"Does not exist attribute <{name}> for {str_model}")

    @classmethod
    def get_field_label(cls, model, field):
        try:
            name, verbose_name = field.split(cls.LABEL_SEPARATOR)
            return pretty_name(verbose_name)
        except ValueError:
            pass
        if "__str__" in field:
            label = str(model._meta.verbose_name)
            return pretty_name(label)
        names = field.split(cls.FIELD_SEPARATOR)
        name = names.pop(0)
        if not hasattr(model, name):
            str_model = (
                model._meta.model_name if hasattr(model, "_meta") else str(model)
            )
            raise AttributeError(f"Does not exist attribute <{name}> for {str_model}.")
        try:
            field = model._meta.get_field(name)
            if len(names):
                related_model = field.related_model
                return cls.get_field_label(
                    related_model, cls.FIELD_SEPARATOR.join(names)
                )
            label = field.verbose_name
        except FieldDoesNotExist:
            attr = getattr(object, name)
            if len(names):
                return cls.get_field_label(
                    attr(model) if callable(attr) else attr,
                    cls.FIELD_SEPARATOR.join(names),
                )
            label = name
        return pretty_name(label)

    @classmethod
    def get_field_value(cls, object, field):
        if "__str__" in field:
            return object
        if object is None:
            return object
        field = field.split(cls.LABEL_SEPARATOR)[0]
        names = field.split(cls.FIELD_SEPARATOR)
        name = names.pop(0)
        if not hasattr(object, name):
            raise AttributeError(
                f"Does not exist attribute <{name}> for {str(object)}."
            )
        if len(names):
            attr = getattr(object, name)
            return cls.get_field_value(
                attr() if callable(attr) else attr, cls.FIELD_SEPARATOR.join(names)
            )
        try:
            field = object._meta.get_field(name)
            if hasattr(field, "choices") and field.choices:
                return dict(field.choices).get(field.value_from_object(object))
            elif field.related_model:
                if field.one_to_many or field.many_to_many:
                    raise ImproperlyConfigured(
                        "OneToMany or ManyToMany is not supported: '%s' " % field.name
                    )
                try:
                    return field.related_model.objects.get(
                        pk=field.value_from_object(object)
                    )
                except field.related_model.DoesNotExist:
                    return None
            else:
                return field.value_from_object(object)
        except FieldDoesNotExist:
            attr = getattr(object, name)
            attr = attr() if callable(attr) else attr
            if isinstance(attr, bool):
                attr = settings.BOOLEAN_YES if attr else settings.BOOLEAN_NO
            return format_html(str(attr))

    @classmethod
    def get_field_type(cls, model, field):
        field = field.split(cls.LABEL_SEPARATOR)[0]
        names = field.split(cls.FIELD_SEPARATOR)
        name = names.pop(0)
        if not hasattr(model, name):
            str_model = (
                model._meta.model_name if hasattr(model, "_meta") else str(model)
            )
            raise AttributeError(f"Does not exist attribute <{name}> for {str_model}.")
        if len(names):
            if hasattr(model, "_meta"):
                return cls.get_field_type(
                    model._meta.get_field(name).related_model,
                    cls.FIELD_SEPARATOR.join(names),
                )
            else:
                attr = getattr(model, name)
                return cls.get_field_type(
                    attr() if callable(attr) else attr, cls.FIELD_SEPARATOR.join(names)
                )
        try:
            field = model._meta.get_field(name)
            type = model._meta.get_field(name).get_internal_type()
        except FieldDoesNotExist:
            type = "Function"
        return type


class FilterService:
    LOOKUPS = {
        "iexact": "Es igual a",
        "exact": "Es igual a",
        "iexact__exclude": "No es igual a",
        "exact__exclude": "No es igual a",
        "icontains": "Contiene",
        "contains": "Contiene",
        "icontains__exclude": "No contiene",
        "contains__exclude": "No contiene",
        "gte": "Mayor o igual que",
        "lte": "Menor o igual que",
    }

    EXCLUDE = "__exclude"

    @classmethod
    def get_lookup_label(cls, lookup):
        return cls.LOOKUPS.get(lookup)

    @classmethod
    def get_flatten_lookups(cls):
        return cls.LOOKUPS.keys()

    @classmethod
    def get_field_lookups(cls, model, field):
        field_lookups = []
        field = FieldService.get_field(model, field)
        if field.get_internal_type() == "BooleanField":
            field_lookups = [
                ("exact", cls.get_lookup_label("exact")),
                ("exact__exclude", cls.get_lookup_label("exact__exclude")),
            ]
            return field_lookups
        lookups = [
            ("iexact", "exact"),
            ("icontains", "contains"),
            ("gte",),
            ("lte",),
        ]
        allow_lookups = list(field.get_lookups().keys())
        for pair in lookups:
            for lookup in pair:
                if lookup in allow_lookups:
                    field_lookups.append((lookup, cls.get_lookup_label(lookup)))
                    if "exact" in lookup or "contains" in lookup:
                        field_lookups.append(
                            (
                                f"{lookup}__exclude",
                                cls.get_lookup_label(f"{lookup}__exclude"),
                            )
                        )
                    break
        return field_lookups

    @classmethod
    def get_choices(self, model, field):
        type = FieldService.get_field_type(model, field)
        field = FieldService.get_field(model, field)
        if type in ("ForeignKey", "OneToOneField", "ManyToManyField"):
            return field.related_model.objects.all()
        elif type == "BooleanField":
            choices = [(1, "Verdadero"), (0, "False")]
        elif field.choices:
            choices = list(field.choices)
        else:
            choices = []
        return choices

    @classmethod
    def get_previous_and_next(cls, queryset, instance):
        values = queryset.values_list("id", flat=True).all()
        for index, value in enumerate(values):
            if value == instance.pk:
                previous_id = None if index == 0 else values[index - 1]
                next_id = None if index == len(values) - 1 else values[index + 1]
                objects = queryset.filter(id__in=[previous_id, next_id])
                return {
                    "previous": previous_id if not previous_id else objects.first(),
                    "next": next_id if not next_id else objects.last(),
                    "current_index": index,
                    "total_entries": len(values),
                }

    @classmethod
    def get_params(self, model, session):
        app = model._meta.app_label
        model = model._meta.model_name
        filters = session.get("filters", [])
        params = {}
        for elem in filters:
            if elem["app"] == app and elem["model"] == model:
                params = elem["params"]
                break
        return params

    @classmethod
    def filter(cls, queryset, params):
        filter_query, exclude_query = map(
            lambda params: cls.get_query(params),
            cls.split_params(queryset.model, params),
        )
        if filter_query:
            queryset = queryset.filter(filter_query)
        if exclude_query:
            queryset = queryset.exclude(exclude_query)
        return queryset

    @classmethod
    def split_params(cls, model, params):
        lookup_params = {
            key: value for key, value in params.items() if cls.has_lookup(key)
        }
        filter_params = {
            key: value for key, value in lookup_params.items() if cls.EXCLUDE not in key
        }
        exclude_params = {
            key.split(cls.EXCLUDE)[0]: value
            for key, value in lookup_params.items()
            if cls.EXCLUDE in key
        }
        for params in [filter_params, exclude_params]:
            for key, value in params.items():
                lookup = cls.has_lookup(key)
                type = FieldService.get_field_type(model, key.split(f"__{lookup}")[0])
                if type == "BooleanField":
                    try:
                        value = bool(int(value))
                    except ValueError:
                        value = False
                params[key] = value
        return filter_params, exclude_params

    @classmethod
    def get_query(cls, params):
        args = []
        for field, value in params.items():
            args.append(Q(**{field: value}))
        if args:
            return reduce(operator.__and__, args)
        return args

    @classmethod
    def has_lookup(cls, key):
        for lookup in cls.get_flatten_lookups():
            if key.endswith(lookup):
                return lookup
