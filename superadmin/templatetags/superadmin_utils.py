# Python
import json

# Django
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
    urls = get_urls_of_site(model_site, instance)
    if action in urls:
        return urls[action]
    raise NoReverseMatch("The action '%s' doesn't exist in the model" % action)
