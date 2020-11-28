"""  Module Signals """

# Django
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.apps import apps

# Models
from .models import Menu

# Local
from .utils import get_attr_of_object
from . import site




""" Signal for presave instance """

@receiver(pre_save)
def prepopulate_slug(sender, instance, **kwargs):
    if not site.is_registered(sender):
        return

    model_site = site.get_modelsite(sender)
    model_name = sender._meta.model_name

    slug_fields = model_site.prepopulate_slug

    if slug_fields and not isinstance(slug_fields, tuple):
        raise ImproperlyConfigured("Field 'prepopulate_slug' must be a tuple")

    if not slug_fields:
        return

    if not hasattr(sender, "slug"):
        raise ImproperlyConfigured(f"Model '{model_name}' has not 'slug' field")

    for field in slug_fields:
        if not hasattr(sender, field):
            raise ImproperlyConfigured(f"Model '{model_name}' has no field'{str(field)}'")

    
    fields = (get_attr_of_object(instance, field) for field in slug_fields)
    slug = " ".join(fields)
    instance.slug = slugify(slug)

@receiver(pre_save, sender=Menu)
def add_route(sender, instance, **kwargs):
    instance.route = instance.get_route()

@receiver(post_save, sender=Menu)
def check(sender, instance, **kwargs):

    post_save.disconnect(check, sender=Menu)
    pre_save.disconnect(add_route, sender=Menu)

    def update_route(menu):
        menu.route = menu.get_route()
        menu.save()
        for submenu in menu.submenus.all():
            update_route(submenu)
        
    def update_groups():
        for menu in Menu.objects.all():
            menu.is_group = bool(menu.submenus.count())
            menu.save()

    update_route(instance)
    update_groups()

    post_save.connect(check, sender=Menu)
    pre_save.connect(add_route, sender=Menu)


