
# Models
from .models import Menu
from .utils import get_user_menu


def menu(request):
    return {
        "menu_tree": build_user_menu(request.user)
    }


def build_user_menu(user):
    menu_list = list()
    if user.is_authenticated and user.is_active:
        object_list = Menu.objects.filter(parent__isnull=True)
        menu_list = get_user_menu(object_list, user)
    return menu_list
