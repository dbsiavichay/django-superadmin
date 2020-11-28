""" Hydra init config """
from .sites import site
from .options import ModelSite
from django.utils.module_loading import autodiscover_modules

__all__ = [
    "site", "ModelSite"
]

default_app_config = "superadmin.apps.SuperAdminConfig"

def autodiscover():
    autodiscover_modules('sites')