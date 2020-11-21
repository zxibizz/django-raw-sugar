from django.db import models
from .query import _RawQuerySet
from .sources import FromRaw, FromQuerySet


class RawManager(models.Manager):
    def __init__(self, from_raw=None, *args, **kwargs):
        if from_raw is not None:
            assert isinstance(from_raw, FromRaw), \
                "Expected a `FromRaw` to be passed "\
                "to 'from_raw', but received a `%s" % type(from_raw)
        self._source = from_raw
        return super().__init__(*args, **kwargs)

    def get_queryset(self):
        assert isinstance(self._source, FromRaw), \
            "Source was not provided! "\
            "Provide source during initialization or "\
            "use .from_raw or .from_queryset instead."
        return _RawQuerySet(self.model,
                            using=self._db,
                            _source=self._source)

    def from_raw(self, raw_query=None, params=[],
                 translations={}, null_fields=[],
                 db_table=None):
        source = FromRaw(raw_query, params, translations,
                         null_fields, db_table)
        return _RawQuerySet(self.model,
                            using=self._db,
                            _source=source)

    def from_queryset(self, queryset, translations={}):
        source = FromQuerySet(queryset, translations)
        source._calculate_null_fields(self.model)
        return _RawQuerySet(self.model,
                            using=self._db,
                            _source=source)


class _DecoratedRawManager(models.Manager):
    def __init__(self, *args, _source_func=None, _source_func_is_callable=False,
                 _set_source_func_on_next_call=False, **kwargs):
        self._source_func = _source_func
        if not _source_func_is_callable:
            assert callable(self._source_func)
        self._source_func_is_callable = _source_func_is_callable
        self._set_source_func_on_next_call = _set_source_func_on_next_call
        self._source = None
        return super().__init__(*args, **kwargs)

    def _check_source_type(self):
        assert isinstance(self._source, (FromRaw, FromQuerySet)), \
            "Expected a `FromRaw` or `FromQuerySet` to be returned "\
            "from the manager method, but received a `%s" % type(self._source)

    def __call__(self, *args, **kwargs):
        if self._set_source_func_on_next_call:
            self._source_func = args[0]
            assert callable(self._source_func)
            self._set_source_func_on_next_call = False
            return self
        elif self._source_func_is_callable:
            self._source = self._source_func(self.model, *args, **kwargs)
            self._check_source_type()
        else:
            raise TypeError
        return self.get_queryset()

    def get_queryset(self):
        if not self._source_func_is_callable:
            self._source = self._source_func(self.model)
            self._check_source_type()

        if isinstance(self._source, FromQuerySet):
            self._source._calculate_null_fields(self.model)

        return _RawQuerySet(self.model,
                                using=self._db,
                                _source=self._source)


def raw_manager(is_callable=False):
    if callable(is_callable):
        return _DecoratedRawManager(_source_func=is_callable)
    if is_callable:
        return _DecoratedRawManager(_set_source_func_on_next_call=True,
                                    _source_func_is_callable=True)
    else:
        return _DecoratedRawManager(_set_source_func_on_next_call=True)
