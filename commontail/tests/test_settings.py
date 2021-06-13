from unittest import TestCase

from django.conf import settings


class SettingsTestCase(TestCase):

    def test_import(self):
        self.assertEqual(settings.COMMONTAIL_NO_IMAGE_PLACEHOLDER_TITLE, 'image later')
