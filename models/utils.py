__all__ = ['AbstractIconAware', ]


class AbstractIconAware:

    def get_icon(self):
        raise NotImplementedError
