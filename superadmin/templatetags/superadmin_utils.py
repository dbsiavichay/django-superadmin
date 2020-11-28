# Python
import json

# Django
from django import template

register = template.Library()

# Filter utilities
@register.filter("json")
def get_json(value):
    return json.dumps(value)