import yaml

# Django
from django.core.management.base import BaseCommand, CommandError

# Local
from .base import build_menu


class Command(BaseCommand):
    help = "Create base menu mapping all apps"

    def add_arguments(self, parser):
        parser.add_argument(
            "--build",
            action="store_true",
            help="Build menu",
        )

    def handle(self, *args, **options):
        """
        apps = {}
        for model in site._registry:
            if model._meta.app_config in apps:
                apps[model._meta.app_config].append(model)
            else:
                apps[model._meta.app_config] = [model]
        """
        try:
            with open("menu.yaml") as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise CommandError("Must be a menu.yaml file in the root of the project")
        except yaml.parser.ParserError as e:
            raise CommandError(
                f"""An error has occurred {e.context}:
                - {e.problem}"""
            )
        build_menu(data)
        self.stdout.write(self.style.SUCCESS("Successfully menu was created"))
