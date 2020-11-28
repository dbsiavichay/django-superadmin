""" Hydra Apps config  """

# Django
from django.apps import AppConfig


class SuperAdminConfig(AppConfig):
    name = 'superadmin'

    def ready(self):
        from . import signals
        self.module.autodiscover()
