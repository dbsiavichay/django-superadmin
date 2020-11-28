# Shortcuts
from superadmin.shortcuts import get_urls_of_site


class UrlMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object = None
        if self.action != "list":
            object = self.object

        urls = get_urls_of_site(self.site, object)

        if "site" in context:
            context["site"].update({"urls":urls})
        else:
            context.update({
                "site": {"urls":urls}
            })
        return context
