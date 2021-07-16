__all__ = ['AbstractIconAware', 'AbstractExtendedTitleAware', ]


class AbstractIconAware:

    def get_icon(self):
        raise NotImplementedError


class AbstractExtendedTitleAware:

    def get_title(self, *args, **kwargs):
        raise NotImplementedError

    def get_link_title(self):
        raise NotImplementedError
