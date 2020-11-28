# Django
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

# Models
from superadmin.models import Action, Menu

#
from superadmin import site


class Command(BaseCommand):
    help = 'Create base menu mapping all apps'

    def handle(self, *args, **options):
        call_command("createactions")
        
        Menu.objects.all().delete()

        default_action = Action.objects.get(app_label="superadmin", element="ModuleView")

        apps = {}
        for model in site._registry:
            if model._meta.app_config in apps:
                apps[model._meta.app_config].append(model)
            else:
                apps[model._meta.app_config] = [model]

        sequence = 1
        for app in apps:
            menu = Menu.objects.create(
                name=app.verbose_name.capitalize(),
                action=default_action,
                is_group=True,
                sequence=sequence
            )
            sequence += 1

            index = 1
            for model in apps[app]:
                action = Action.objects.get(app_label=app.label, element=model._meta.model_name)

                Menu.objects.create(
                    parent=menu,
                    name=model._meta.verbose_name_plural.capitalize(),
                    action=action,
                    is_group=False,
                    sequence=index
                )

                index += 1


        self.stdout.write(self.style.SUCCESS("Successfully base menu was created"))


    