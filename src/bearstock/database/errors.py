
__all__ = [
    'BearError',
    'BearModelError',
    'BearDatabaseError',
]


class BearError(RuntimeError):
    pass


class BearDatabaseError(BearError):
    pass


class BearModelError(BearError):
    pass

