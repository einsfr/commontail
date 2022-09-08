from django.http import HttpRequest, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin import messages
from wagtail.models import Page, PagePermissionTester

from ..models import AbstractCacheAwarePage


__all__ = ['clear_page_cache_view', ]


def clear_page_cache_view(request: HttpRequest, page_id: int) -> HttpResponse:
    page: Page = Page.objects.get(pk=page_id).specific
    permissions: PagePermissionTester = page.permissions_for_user(request.user)
    if not permissions.can_edit():
        return HttpResponseForbidden()
    if isinstance(page, AbstractCacheAwarePage):
        page.get_cache_provider().clear(page.get_cache_vary_on())
    messages.success(request, _('Page cache cleared.'))

    return HttpResponseRedirect(reverse('wagtailadmin_pages:edit', kwargs={'page_id': page_id}))
