from django.test import TestCase, Client

from ..models import TestHierarchyOnlyPage


class PageTestCase(TestCase):

    fixtures = ['pages', ]

    def test_hierarchy_only_page(self):
        self.assertEqual(Client().get('/testhierarchyonlypage/').status_code, 403)
        page: TestHierarchyOnlyPage = TestHierarchyOnlyPage.objects.first()
        self.assertFalse(page.get_sitemap_urls())
