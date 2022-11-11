from django.core.paginator import Paginator
from django.conf import settings


def show_pages(post_list, request):
    paginator = Paginator(post_list, settings.AMOUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
