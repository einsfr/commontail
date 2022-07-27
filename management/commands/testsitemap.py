import requests
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand


class Non200Exception(Exception):
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            action='store',
            dest='url',
            default='http://127.0.0.1:8000/sitemap.xml',
            help='Sitemap URL',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            dest='quiet',
            default=False,
            help='Suppress all stdout messages.',
        )
        parser.add_argument(
            '--continue',
            action='store_true',
            dest='continue',
            default=True,
            help='Don\'t stop even if other than 200 status code returned.'
        )
        parser.add_argument(
            '--additional',
            action='store',
            dest='additional',
            default='',
            help='A text file with additional URLs to test.'
        )
        parser.add_argument(
            '--additionalbase',
            action='store',
            dest='additional_base',
            default='',
            help='Base URL for additional URLs to test.'
        )
        parser.add_argument(
            '--additionalonly',
            action='store_true',
            dest='additional_only',
            default=False,
            help='Skip sitemap testing and process only additional URLs.'
        )
        parser.add_argument(
            '--replacehost',
            action='store',
            dest='replace_host',
            default='',
            help='Replacement for a protocol://host:port part of sitemap\'s URLs.'
        )

    def _check_url(self, url, quiet):
        r: requests.Response = requests.get(url)
        if r.status_code == 200:
            if not quiet:
                self.stdout.write(f'{url}: {r.status_code}')
        else:
            self.stderr.write(f'{url}: {r.status_code}')

            raise Non200Exception

    @staticmethod
    def _replace_host(old_url: str, replace_host: str) -> str:
        split_original = urlsplit(old_url)
        split_replacement = urlsplit(replace_host)
        scheme = split_replacement.scheme
        netloc = split_replacement.netloc

        if split_replacement.path and split_replacement.path != '/':
            path = split_replacement.path + split_original.path
        else:
            path = split_original.path

        url = urlunsplit((scheme, netloc, path, split_original.query, split_original.fragment))

        return url

    def handle(self, *args, **options):
        quiet: bool = options['quiet']
        checked_count: int = 0
        exceptions_count: int = 0

        if options['additional_only']:
            if not quiet:
                self.stdout.write('Skipping sitemap testing: --additionalonly option passed')
        else:
            if not quiet:
                self.stdout.write('Downloading sitemap...')

            r: requests.Response = requests.get(options['url'])

            if r.status_code == 200:
                if not quiet:
                    self.stdout.write('Success!')
            else:
                self.stderr.write('Failed to download sitemap file with status code {}'.format(r.status_code))

                return

            soup = BeautifulSoup(r.text, 'lxml')

            for loc in soup.find_all('loc'):
                if options['replace_host']:
                    url = self._replace_host(loc.string, options['replace_host'])
                else:
                    url = loc.string

                try:
                    self._check_url(url, quiet)
                    checked_count += 1
                except Non200Exception:
                    exceptions_count += 1

                    if not options['continue']:
                        return

        additional = options['additional']

        if additional:
            if not quiet:
                self.stdout.write('Checking additional URLs...')

            with open(additional) as f:
                for line in f:
                    url = f'{options["additional_base"]}{line}'

                    if options['replace_host']:
                        url = self._replace_host(url, options['replace_host'])

                    try:
                        self._check_url(url, quiet)
                    except Non200Exception:
                        exceptions_count += 1
                        if not options['continue']:
                            return
                    else:
                        checked_count += 1

        if not quiet:
            self.stdout.write(f'All done! Checked {checked_count} URLs, found {exceptions_count} exceptions.')
