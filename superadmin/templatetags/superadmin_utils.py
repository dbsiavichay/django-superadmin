# Python
import json

# Django
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django import template
from django.urls import NoReverseMatch

# Local
from .. import site
from ..shortcuts import get_urls_of_site

register = template.Library()

# Filter utilities
@register.filter("json")
def get_json(value):
    return json.dumps(value)


@register.filter("chunks")
def chunks(value, number):
    number = int(number)
    chunks = [value[i : i + number] for i in range(0, len(value), number)]
    return chunks


@register.filter("subtract")
def subtract(value, number):
    number = float(number)
    return value - number


@register.filter("multiply")
def multiply(value, number):
    number = float(number)
    return value * number


@register.simple_tag()
def site_url(instance, action):
    model_site = site.get_modelsite(instance.__class__)
    urls = get_urls_of_site(model_site, object=instance)
    if action in urls:
        return urls[action]
    raise NoReverseMatch("The action '%s' doesn't exist in the model" % action)


@register.filter("has_perm")
def has_perm(user, perm):
    return user.has_perm(perm)


@register.simple_tag()
def detail_widget(label, value, widget):
    if widget not in settings.TEMPLATE_WIDGETS_DETAIL:
        if "default" not in settings.TEMPLATE_WIDGETS_DETAIL:
            raise ImproperlyConfigured(
                f"Does not exist template name for '{widget}' or default widget template."
            )
        template_name = settings.TEMPLATE_WIDGETS_DETAIL.get("default")
    else:
        template_name = settings.TEMPLATE_WIDGETS_DETAIL.get(widget)
    return template_name
