from .managers import _RawSugarDecoratedManager
from .sources import FromRaw, FromQuerySet


def raw_manager(is_callable=False):
    if callable(is_callable):
        return _RawSugarDecoratedManager(_source_func=is_callable)
    if is_callable:
        return _RawSugarDecoratedManager(_set_source_func_on_next_call=True,
                                       _source_func_is_callable=True)
    else:
        return _RawSugarDecoratedManager(_set_source_func_on_next_call=True)


__all__ = ["raw_manager", "FromRaw", "FromQuerySet"]
