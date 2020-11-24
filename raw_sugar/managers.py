from django.db import models
from .query import RawSugarQuerySet
from .sources import SourceRaw, FromRaw, FromQuerySet


class RawManagerMixin:
    def from_raw(self, raw_query=None, params=[],
                 translations={}, null_fields=[],
                 db_table=None):
        def source_func(cls, *args):
            return FromRaw(raw_query, args, translations,
                           null_fields, db_table)
        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source_func=source_func,
                                _source_func_args=params)

    def from_queryset(self, queryset, translations={}):
        def source_func(cls):
            return FromQuerySet(queryset, translations)
        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source_func=source_func)


class RawManager(models.Manager, RawManagerMixin):
    def __init__(self, from_raw=None):
        if from_raw is not None:
            assert isinstance(from_raw, FromRaw), \
                "Expected a `FromRaw` to be passed "\
                "to 'from_raw', but received a `%s" % type(from_raw)
        self._source = from_raw
        return super().__init__()

    def get_queryset(self):
        if isinstance(self._source, FromRaw):
            def source_func(cls, *args):
                return self._source.with_params(*args)
            return RawSugarQuerySet(self.model,
                                    using=self._db,
                                    _source_func=source_func,
                                    _source_func_args=self._source.params)
        else:
            return super().get_queryset()

    def with_params(self, *args):
        def source_func(cls, *args):
            return self._source.with_params(*args)
        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source_func=source_func,
                                _source_func_args=args)


class DecoratedRawManager(models.Manager, RawManagerMixin):
    def __init__(self, *args, _source_func=None, _source_func_is_callable=False,
                 _set_source_func_on_next_call=False, **kwargs):
        self._source_func = _source_func
        if not _source_func_is_callable:
            assert callable(self._source_func)
        self._source_func_is_callable = _source_func_is_callable
        self._set_source_func_on_next_call = _set_source_func_on_next_call
        return super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self._set_source_func_on_next_call:
            self._source_func = args[0]
            assert callable(self._source_func)
            self._set_source_func_on_next_call = False
            return self
        elif self._source_func_is_callable:
            return RawSugarQuerySet(
                self.model, using=self._db,
                _source_func=self._source_func,
                _source_func_args=args,
                _source_func_kwargs=kwargs)
        else:
            raise TypeError

    def get_queryset(self):
        return RawSugarQuerySet(
            self.model, using=self._db,
            _source_func=self._source_func)


def raw_manager(is_callable=False):
    if callable(is_callable):
        return DecoratedRawManager(_source_func=is_callable)
    if is_callable:
        return DecoratedRawManager(_set_source_func_on_next_call=True,
                                   _source_func_is_callable=True)
    else:
        return DecoratedRawManager(_set_source_func_on_next_call=True)
