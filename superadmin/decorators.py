from django.apps import apps
from django.core.exceptions import ImproperlyConfigured


def register(model):
    """
    Register the given model(s) classes and wrapped ModelSite class:
    @register(Author)
    class AuthorSite(superadmin.ModelSite):
        pass
    """
    from superadmin import ModelSite, site

    def _model_site_wrapper(site_class):
        if not model:
            raise ValueError('One model must be passed to register.')
        
        model_class = None
        if isinstance(model, str):
            try:
                app_name, model_name = model.split('.')
                model_class = apps.get_model(app_name, model_name)
            except ValueError:
                raise ImproperlyConfigured("Does not exist '%s' model" % model)
        

        if not issubclass(site_class, ModelSite):
            raise ValueError('Wrapped class must subclass ModelSite.')

        site.register(model_class if model_class else model, site_class=site_class)

        return site_class
    return _model_site_wrapper