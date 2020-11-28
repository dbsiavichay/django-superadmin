# Python
from copy import copy
import types
import re

# Django
from django import template
from django.urls import reverse_lazy
from django.forms.models import model_to_dict
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from collections.abc import Iterable
from .. import settings



from django.template import Context
from django.template.base import (
    FILTER_SEPARATOR,
    VariableNode,
    TextNode,
    Node,
    NodeList,
    TemplateSyntaxError,
    VariableDoesNotExist,
)

# Exceptions
from django.template.exceptions import TemplateDoesNotExist

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.forms.utils import pretty_name


register = template.Library()


def silence_without_field(fn):
    """
    Args:
        fn:
    """

    def wrapped(field, attr):
        if not field:
            return ""
        return fn(field, attr)

    return wrapped


def _process_field_attributes(field, attr, process):

    # split attribute name and value from 'attr:value' string
    """
    Args:
        field:
        attr:
        process:
    """
    params = attr.split(":", 1)
    attribute = params[0]
    value = params[1] if len(params) == 2 else ""

    field = copy(field)

    # decorate field.as_widget method with updated attributes
    old_as_widget = field.as_widget

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        attrs = attrs or {}
        process(widget or self.field.widget, attrs, attribute, value)
        html = old_as_widget(widget, attrs, only_initial)
        self.as_widget = old_as_widget
        return html

    field.as_widget = types.MethodType(as_widget, field)
    return field


@register.filter("attr")
@silence_without_field
def set_attr(field, attr):
    """
    Args:
        field:
        attr:
    """

    def process(widget, attrs, attribute, value):
        attrs[attribute] = value

    return _process_field_attributes(field, attr, process)


@register.filter("append_attr")
@silence_without_field
def append_attr(field, attr):
    """
    Args:
        field:
        attr:
    """

    def process_str(field, attr):
        params = attr.split(":", 1)
        attribute = params[0]
        value = params[1] if len(params) == 2 else ""

        content = field.split('name')
        content.insert(1, f'{attribute}="{value}" name')
        field = ''.join(content)
        return mark_safe(field)

    if isinstance(field, str): return process_str(field, attr)

    def process(widget, attrs, attribute, value):
        if attrs.get(attribute):
            attrs[attribute] += " " + value
        elif widget.attrs.get(attribute):
            attrs[attribute] = widget.attrs[attribute] + " " + value
        else:
            attrs[attribute] = value
    
    return _process_field_attributes(field, attr, process)


@register.filter("add_class")
@silence_without_field
def add_class(field, css_class):
    """
    Args:
        field:
        css_class:
    """
    return append_attr(field, "class:" + css_class)


@register.filter("data")
@silence_without_field
def set_data(field, data):
    return set_attr(field, "data-" + data)

@register.filter(name="field_type")
def field_type(field):
    """Template filter that returns field class name (in lower case). E.g. if
    field is CharField then {{ field|field_type }} will return 'charfield'.

    Args:
        field:
    """
    if hasattr(field, "field") and field.field:
        return field.field.__class__.__name__.lower()
    return ""


@register.filter(name="widget_name")
def widget_name(field):
    """Template filter that returns field widget class name (in lower case).
    E.g. if field's widget is TextInput then {{ field|widget_type }} will return
    'textinput'.

    Args:
        field:
    """
    if (
        hasattr(field, "field")
        and hasattr(field.field, "widget")
        and field.field.widget
    ):
        return field.field.widget.__class__.__name__.lower()
    return ""


# ======================== render_field tag ==============================

ATTRIBUTE_RE = re.compile(
    r"""
    (?P<attr>
        [\w_-]+
    )
    (?P<sign>
        \+?=
    )
    (?P<value>
    ['"]? # start quote
        [^"']*
    ['"]? # end quote
    )
""",
    re.VERBOSE | re.UNICODE,
)

# ATTRIBUTE_RE = re.compile(r"""(?P<attr>[\w_-]+)(?P<sign>\+?=)(?P<value>['"]?[^"']*['"]?)""", re.VERBOSE | re.UNICODE)


@register.tag
def render_field(parser, token):
    """Render a form field using given attribute-value pairs

    Takes form field as first argument and list of attribute-value pairs for
    all other arguments. Attribute-value pairs should be in the form of
    attribute=value or attribute="a value" for assignment and attribute+=value
    or attribute+="value" for appending.

    Args:
        parser:
        token:
    """
    error_msg = (
        '%r tag requires a form field followed by a list of attributes and values in the form attr="value"'
        % token.split_contents()[0]
    )
    try:
        bits = token.split_contents()
        tag_name = bits[0]
        form_field = bits[1]
        attr_list = bits[2:]
    except ValueError:
        raise TemplateSyntaxError(error_msg)

    form_field = parser.compile_filter(form_field)
    
    attrs = []
    for pair in attr_list:
        match = ATTRIBUTE_RE.match(pair)
        if not match:
            raise TemplateSyntaxError(error_msg + ": %s" % pair)
        dct = match.groupdict()
        attr, value = dct["attr"], parser.compile_filter(dct["value"])

        attrs.append((attr, value))

    return FieldNode(form_field, attrs)


class FieldNode(Node):
    def __init__(self, field, attrs):
        """
        Args:
            field:
            attrs:
        """
        self.field = field
        self.attrs = attrs

    def render(self, context):
        """
        Args:
            context:
        """

        bounded_field = self.field.resolve(context)
        #field = getattr(bounded_field, "field", None)
        with context.push():
            for key, value in self.attrs:
                if key == "class":
                    bounded_field = add_class(bounded_field, value.resolve(context))
                elif key == "type":
                    bounded_field.field.widget.input_type = value.resolve(context)
                else:
                    context.update({key: value.resolve(context)})
            
            # Get template name
            if not bounded_field:
                raise ImproperlyConfigured('The field passed do not exist.')

            widget_name = bounded_field.widget_type
            if not widget_name in settings.TEMPLATE_WIDGETS:
                if not "default" in settings.TEMPLATE_WIDGETS:
                    raise ImproperlyConfigured(f"Does not exist template name for '{widget_name}' or default widget template.")
                template_name = settings.TEMPLATE_WIDGETS.get("default")
            else:
                template_name = settings.TEMPLATE_WIDGETS.get(widget_name)

            
            context.update({
                "field": bounded_field,
            })

            if widget_name in ("clearablefile",) and hasattr(bounded_field.form, "instance") and hasattr(bounded_field.form.instance, bounded_field.name):
                file = getattr(bounded_field.form.instance, bounded_field.name)
                if file:
                    context.update({
                        "file_name": file.name,
                        "file_url": file.url
                    })
            
            t = context.template.engine.get_template(template_name)
            component = t.render(context)
            context.pop()
            return mark_safe(component)
            


"""
@register.filter
def verbose_name(obj):
    
    return obj._meta.verbose_name


@register.filter
def verbose_name_plural(obj):
   
    try:
        return obj._meta.verbose_name_plural
    except:
        pass


@register.simple_tag
def get_verbose_field_name(instance, field_name):
   
    return instance._meta.get_field(field_name).verbose_name.title()


@register.filter
def get_class(obj):
    
    return obj.model.__name__


# OBTENER LOS NOMBRES DE UN OBJETO
# GET MODEL INSTANCE FIELDS
# EJ. OBJECT.OBJECTS.GET(PK=1)
@register.filter
def get_field_names(obj):
    
    return obj._meta.fields
    # El siguiente metodo recupera incluso las tablas subrelacionadas
    # return obj._meta.get_fields()


@register.filter
def get_field_verbose_names(obj):
   
    return obj._meta.verbose_name.title()


@register.simple_tag
def get_field_values(obj):
    
    return model_to_dict(obj)
"""

# LIST VIEW CON VALUES
"""
@register.simple_tag
def obtener_cabeceras(obj, numero):
    
    objeto = model_to_dict(obj)
    cabeceras = []
    for c in objeto.keys():
        cabeceras.append(obj._meta.get_field(c).verbose_name.title())
    return cabeceras


@register.simple_tag
def obtener_valores(obj, numero):
   
    objeto = model_to_dict(obj)
    objeto = model_to_dict(obj)
    valores = []
    for c in objeto.values():
        valores.append(c)
    return valores


@register.filter
def verbose_name_and_name(obj):
   
    objeto = model_to_dict(obj)
    lista = []
    for c in objeto.keys():
        lista.append(
            {"verbose_name": obj._meta.get_field(c).verbose_name.title(), "name": c}
        )
    return lista








@register.filter
def is_date(val):
  
    return isinstance(val, date)


@register.simple_tag
def get_headers(model_site):
 
    headers = []
    for name in model_site.list_display:
        try:
            field = model_site.model._meta.get_field(name)
            label = field.verbose_name
        except FieldDoesNotExist:
            if name == "__str__":
                label = str(model_site.model._meta.verbose_name)
            else:
                if hasattr(model_site, name):
                    attr = getattr(model_site, name)
                elif hasattr(model_site.model, name):
                    attr = getattr(model_site.model, name)
                else:
                    raise AttributeError

                label = attr.__name__ if callable(attr) else attr
        finally:
            headers.append(pretty_name(label))

    return headers


@register.simple_tag
def get_results(model_site, queryset):
    results = []
    for instance in queryset:
        try:
            slug_or_pk = instance.slug
        except:
            slug_or_pk = instance.id
        line = {
            "update_url": reverse_lazy(
                "site:%s_%s_editar" % model_site.get_info(), args=[instance.id]
            ),
            "detail_url": reverse_lazy(
                "site:%s_%s_detalle" % model_site.get_info(), args=[instance.id]
            ),
        }
        object_list = []
        for name in model_site.list_display:
            if name == "__str__":
                value = str(instance)
            else:
                if hasattr(model_site, name):
                    attr = getattr(model_site, name)
                elif hasattr(instance, name):
                    attr = getattr(instance, name)
                else:
                    raise AttributeError
                value = attr() if callable(attr) else attr
            object_list.append(value)
        line.update({"object_list": object_list})
        results.append(line)
    return results



@register.simple_tag
def model_name(value):
    if hasattr(value, "model"):
        value = value.model

    return value._meta.label.split(".")[-1]


@register.filter
def content_type(obj):
    if not obj:
        return False
    return ContentType.objects.get_for_model(obj).id


@register.filter()
def get_app_label_content_type(value):
    return ContentType.objects.get_for_id(value)


@register.filter
def has_permission(request, view_permissions):
    user = request.user
    if request.user.is_authenticated and request.user.is_superuser:
        return True
    permissions = list()
    if isinstance(view_permissions, Iterable):
        for model in view_permissions:
            permissions.append(f"{model._meta.app_label}.view_{model._meta.model_name}")
            permissions.append(f"{model._meta.app_label}.add_{model._meta.model_name}")
            permissions.append(
                f"{model._meta.app_label}.change_{model._meta.model_name}"
            )
    else:
        permissions.append(
            f"{view_permissions._meta.app_label}.view_{view_permissions._meta.model_name}"
        )
        permissions.append(
            f"{view_permissions._meta.app_label}.add_{view_permissions._meta.model_name}"
        )
        permissions.append(
            f"{view_permissions._meta.app_label}.change_{view_permissions._meta.model_name}"
        )
    return any(user.has_perm(permission) for permission in permissions)


@register.simple_tag
def permission(request, object, action):
    try:
        model = object.__class__
    except:
        model = object
    return request.user.has_perm(
        f"{model._meta.app_label}.{action}_{model._meta.model_name}"
    )


@register.filter
def get_type(value):
    return type(value)


# RENDERIZAR PDF
@register.simple_tag(takes_context=True)
def render_pdf(context, tpl_string):
    t = template.Template(tpl_string)
    return t.render(context)


@register.simple_tag(takes_context=True)
def params(context, **kwargs):
    
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% params page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>
    d = context["request"].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()
    
"""