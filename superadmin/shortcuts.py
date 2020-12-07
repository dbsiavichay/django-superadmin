# Python
import inspect

# Django
from django.views.generic import View
from django.urls import reverse, NoReverseMatch
from django.apps import apps


def get_slug_or_pk(object):
    res = dict()
    if object:
        param = "slug" if hasattr(object, "slug") else "pk"
        res.update({
            param:getattr(object, param)
        })

    return res


def get_object(model_class, slug_or_pk):
    search_field = "slug" if hasattr(model_class, "slug") else "pk"
    try:
        object = model_class.objects.get(**{search_field: slug_or_pk})
    except model_class.DoesNotExist:
        object = None
    return object


def get_urls_of_site(site, object=None):
    urls = {}
    kwargs = get_slug_or_pk(object)

    for action in ("list", "create", "mass_update", "mass_delete"):
        try:
            url_name = site.get_url_name(action)
            urls.update({action: reverse(url_name)})
        except NoReverseMatch:
            print("Url not found: %s" % url_name)
    
    if not kwargs:
        return urls

    for action in ("update","detail", "delete", "duplicate"):
        try:
            url_name = site.get_url_name(action)

            urls.update({action: reverse(url_name, kwargs=kwargs)})
        except NoReverseMatch:
            print("Url not found: %s" % url_name)

    return urls
