from django.conf import settings

BREADCRUMB_HOME_TEXT = getattr(settings, "BREADCRUMB_HOME_TEXT", "home")
BREADCRUMB_CREATE_TEXT = getattr(settings, "BREADCRUMB_CREATE_TEXT", "create")
BREADCRUMB_UPDATE_TEXT = getattr(settings, "BREADCRUMB_UPDATE_TEXT", "update")
BREADCRUMB_DETAIL_TEXT = getattr(settings, "BREADCRUMB_DETAIL_TEXT", "detail")
BREADCRUMB_DELETE_TEXT = getattr(settings, "BREADCRUMB_DELETE_TEXT", "delete")

BOOLEAN_YES = getattr(settings, "BOOLEAN_YES", "Yes")
BOOLEAN_NO = getattr(settings, "BOOLEAN_NO", "No")

TEMPLATE_WIDGETS = getattr(settings, "TEMPLATE_WIDGETS", {})