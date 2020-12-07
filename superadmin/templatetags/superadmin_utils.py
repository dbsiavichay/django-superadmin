# Python
import json

# Django
from django import template

register = template.Library()

# Filter utilities
@register.filter("json")
def get_json(value):
    return json.dumps(value)


@register.filter("chunks")
def chunks(value, number):
    number = int(number)
    chunks = [ value[i:i + number] for i in range(0, len(value), number) ]
    return chunks


@register.filter("subtract")
def subtract(value, number):
    number = float(number)
    return value - number


@register.filter("multiply")
def multiply(value, number):
    number = float(number)
    return value * number