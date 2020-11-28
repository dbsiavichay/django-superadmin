""" """
# Django
from django.views.generic import RedirectView
from django.urls import reverse


class DuplicateView(RedirectView):
    site = None
    duplicate_param = "duplicate"

    def get_redirect_url(self, *args, **kwargs):
        slug_or_pk = kwargs.get("slug") if "slug" in kwargs else kwargs.get("pk")
        url = reverse(self.site.get_url_name("create"))
        url = "%s?%s" % (url, f"{self.duplicate_param}={slug_or_pk}")
        return url
