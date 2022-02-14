# Python
import inspect
from importlib import import_module


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
    names = (
        "PermissionRequiredMixin",
        "BreadcrumbMixin",
        "UrlMixin",
        "TemplateMixin",
    )
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
            "is_group": menu.is_group,
        }

        if not obj_menu["submenus"] and (
            menu.is_group or not menu.action.has_permissions(user)
        ):
            continue

        menus.append(obj_menu)
    return menus
