import types


class _classproperty:
    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self


def _property_manager_from_queryset(func):
    def inner_wrapper(cls, *args, **kwargs):
        result = func(cls, *args, **kwargs)
        if not isinstance(result, tuple):
            result = (result,)
        return cls.from_queryset(*result)
    return _classproperty(inner_wrapper)


def _callable_manager_from_queryset(func):
    def wrapper(*args, **kwargs):
        def inner_wrapper(cls, *args, **kwargs):
            result = func(cls, *args, **kwargs)
            if not isinstance(result, tuple):
                result = (result,)
            return cls.from_queryset(*result)
        return inner_wrapper(*args, **kwargs)
    return classmethod(wrapper)


def manager_from_queryset(is_method=False):
    if callable(is_method):
        return _property_manager_from_queryset(is_method)
    if is_method:
        return _callable_manager_from_queryset
    else:
        return _property_manager_from_queryset


def _property_manager_from_raw(func):
    def inner_wrapper(cls, *args, **kwargs):
        result = func(cls, *args, **kwargs)
        if not isinstance(result, tuple):
            result = (result,)
        return cls.from_raw(*result)
    return _classproperty(inner_wrapper)


def _callable_manager_from_raw(func):
    def wrapper(*args, **kwargs):
        def inner_wrapper(cls, *args, **kwargs):
            result = func(cls, *args, **kwargs)
            if not isinstance(result, tuple):
                result = (result,)
            return cls.from_raw(*result)
        return inner_wrapper(*args, **kwargs)
    return classmethod(wrapper)


def manager_from_raw(is_method=False):
    if callable(is_method):
        return _property_manager_from_raw(is_method)
    if is_method:
        return _callable_manager_from_raw
    else:
        return _property_manager_from_raw
