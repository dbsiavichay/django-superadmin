# Django
from django.core.management.base import BaseCommand, CommandError

# local
from .base import create_actions


class Command(BaseCommand):
    help = "Create actions mapping all apps"

    def handle(self, *args, **options):
        create_actions()
        self.stdout.write(self.style.SUCCESS("Successfully actions was created"))
