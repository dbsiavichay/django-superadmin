#Python
import inspect
from importlib import import_module

# Django
from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import pretty_name
from django.utils.html import format_html

from . import settings


def get_label_of_field(model, field):
    names = field.split(".")
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
            return get_label_of_field(
                model._meta.get_field(name).related_model, ".".join(names)
            )
        else:
            attr = getattr(model, name)
            return get_label_of_field(
                attr() if callable(attr) else attr, ".".join(names)
            )
    try:
        field = model._meta.get_field(name)
        label = field.verbose_name if hasattr(field, "verbose_name") else name
    except FieldDoesNotExist:
        label = str(model._meta.verbose_name) if name == "__str__" else name

    return pretty_name(label)


def get_attr_of_object(instance, field):
    names = field.split(".")
    name = names.pop(0)
    name = name.split(":")[0]

    if not hasattr(instance, name):
        raise AttributeError(f"No existe le atributo <{name}> para {str(instance)}.")

    if len(names):
        return get_attr_of_object(getattr(instance, name), ".".join(names))

    try:
        field = instance._meta.get_field(name)
        if hasattr(field, "choices") and field.choices:
            name = f"get_{name}_display"
    except FieldDoesNotExist:
        pass

    attr = getattr(instance, name)
    
    if hasattr(attr, '__class__') and (attr.__class__.__name__ == 'ManyRelatedManager' or attr.__class__.__name__ == 'RelatedManager'):
        attr = [str(obj) for obj in attr.all()]

    attr = attr() if callable(attr) else attr

    if isinstance(attr, bool):
        attr = format_html(settings.BOOLEAN_YES) if attr else format_html(settings.BOOLEAN_NO)

    return attr


def import_class(module_name, class_name):
    cls = None
    try:
        module = import_module(module_name)
        members = inspect.getmembers(module, inspect.isclass)
        for name, klass in members:
            if name == class_name:
                cls = klass
                break
    except ModuleNotFoundError as error:
        print("Not found %s" % module_name)
    return cls


def import_mixin(name):
    mixin = import_class("superadmin.mixins", name)
    return mixin


def import_all_mixins():
    mixins = list()
    names = "PermissionRequiredMixin", "BreadcrumbMixin", "UrlMixin", "TemplateMixin", "FilterMixin"
    for name in names:
        mixin = import_mixin(name)
        if mixin:
            mixins.append(mixin)
        
    return mixins

def get_user_menu(menu_list, user):
    menus = list()
    for menu in menu_list:
        obj_menu = {
            "name": menu.name,
            "url": menu.get_url(),
            "icon": menu.icon_class or "",
            "submenus": get_user_menu(menu.submenus.all(), user),
            "is_root": not menu.parent,
            "is_group": menu.is_group
        }

        if not obj_menu["submenus"] and (menu.is_group or not menu.action.has_permissions(user)):
            continue

        menus.append(obj_menu)

    return menus

