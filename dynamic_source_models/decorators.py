import types


class _classproperty:
    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self


def _property_source_queryset(func):
    def inner_wrapper(cls, *args, **kwargs):
        qs = func(cls, *args, **kwargs)
        return cls.from_queryset(qs)
    return _classproperty(inner_wrapper)


def _callable_source_queryset(func):
    def wrapper(*args, **kwargs):
        def inner_wrapper(cls, *args, **kwargs):
            qs = func(cls, *args, **kwargs)
            return cls.from_queryset(qs)
        return inner_wrapper(*args, **kwargs)
    return classmethod(wrapper)


def source_queryset(callable=False):
    if isinstance(callable, types.FunctionType):
        return _property_source_queryset(callable)
    if callable:
        return _callable_source_queryset
    else:
        return _property_source_queryset
