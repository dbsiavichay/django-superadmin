# Python 
import inspect
from importlib import import_module

# Django
from django.views.generic import View
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

# Models
from ...models import Action


def get_views_catalog():
    module_name = "django.views"

    def map_module(module_name):
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            return []

        names = [
            name for name, cand in inspect.getmembers(module, inspect.isclass)
            if issubclass(cand, View)
        ] 
        for name, mod in inspect.getmembers(module, inspect.ismodule):
            names.extend(map_module(f"{module_name}.{name}"))

        return names

    names = set(map_module(module_name))
    return list(names)


VIEWS_CATALOG = get_views_catalog()


class Command(BaseCommand):
    help = 'Create actions mapping all apps'

    def handle(self, *args, **options):
        for app in apps.get_app_configs():
            actions, elements, m, v = get_actions_and_elements(app)

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

        self.stdout.write(self.style.SUCCESS("Successfully actions was created"))


def get_actions_and_elements(app_config):
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
            name: (
                f"{app_config.verbose_name.capitalize()} | {name}"
            )
            for name, candidate in inspect.getmembers(module, inspect.isclass)
            if issubclass(candidate, View) and not candidate.__name__ in VIEWS_CATALOG
        }
    except (ModuleNotFoundError, ImportError):
        view_elements = {}

    elements = {
        **model_elements,
        **view_elements
    }

    return actions, elements, model_elements, view_elements



    


    