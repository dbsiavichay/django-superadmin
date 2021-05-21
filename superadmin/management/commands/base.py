# Python
import inspect
from importlib import import_module

# Django
from django.db.models import Q
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.views.generic import View
from django.apps import apps

# Models
from ...models import Action, Menu


def get_views_catalog():
    module_name = "django.views"

    def map_module(module_name):
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            return []

        names = [
            name
            for name, cand in inspect.getmembers(module, inspect.isclass)
            if issubclass(cand, View)
        ]
        for name, mod in inspect.getmembers(module, inspect.ismodule):
            names.extend(map_module(f"{module_name}.{name}"))

        return names

    names = set(map_module(module_name))
    return list(names)


def get_actions_and_elements(app_config, VIEWS_CATALOG):
    actions = {
        action.element: action
        for action in Action.objects.filter(app_label=app_config.label)
    }

    model_elements = {
        model._meta.model_name: (
            f"{app_config.verbose_name.capitalize()} | {model._meta.verbose_name.capitalize()}"
        )
        for model in app_config.get_models()
    }

    try:
        module = import_module(f"{app_config.name}.views")
        view_elements = {
            name: (f"{app_config.verbose_name.capitalize()} | {name}")
            for name, candidate in inspect.getmembers(module, inspect.isclass)
            if issubclass(candidate, View) and not candidate.__name__ in VIEWS_CATALOG
        }
    except (ModuleNotFoundError, ImportError):
        view_elements = {}

    elements = {**model_elements, **view_elements}

    return actions, elements, model_elements, view_elements


def create_actions():
    VIEWS_CATALOG = get_views_catalog()

    for app in apps.get_app_configs():
        actions, elements, m, v = get_actions_and_elements(app, VIEWS_CATALOG)

        if not elements:
            continue

        acts = []
        acts += [
            Action(
                to=Action.ToChoices.MODEL,
                app_label=app.label,
                name=name,
                element=element,
            )
            for (element, name) in m.items()
            if element not in actions
        ]
        acts += [
            Action(
                to=Action.ToChoices.CLASSVIEW,
                app_label=app.label,
                name=name,
                element=element,
            )
            for (element, name) in v.items()
            if element not in actions
        ]

        Action.objects.bulk_create(acts)


def build_menu(data):
    create_actions()
    Menu.objects.all().delete()
    default_action = Action.objects.get(app_label="superadmin", element="ModuleView")

    def permissions(data, action):
        content_type = ContentType.objects.get_for_model(Permission)
        for perm in data:
            obj, created = Permission.objects.update_or_create(
                codename=perm.get("codename"),
                content_type=content_type,
                defaults={"name": perm.get("name")},
            )
            action.permissions.add(obj)

    def build(name, data, action, parent=None, menu_list=[]):
        default = action
        is_group = True
        if "app" in data:
            element = data["model"] if "model" in data else data["view"]
            default = Action.objects.get(app_label=data["app"], element=element)
            is_group = False
            if "permissions" in data:
                permissions(data["permissions"], default)

        current = Menu.objects.create(
            parent=parent,
            name=name.capitalize(),
            action=default,
            is_group=is_group,
            sequence=len(menu_list) + 1,
        )
        menu_list.append(current)
        if is_group:
            for key in data:
                build(key, data[key], action, parent=current, menu_list=menu_list)
        return menu_list

    menus = []
    for key in data:
        build(key, data[key], default_action, menu_list=menus)
