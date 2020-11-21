from django.db import models
from .sources import FromRaw, FromQuerySet


class RawSugarQuery(models.sql.Query):
    def __init__(self, *args, _source=None, **kwargs):
        self._source = _source

        return super().__init__(*args, **kwargs)

    def get_compiler(self, *args, **kwargs):
        compiler = super().get_compiler(*args, **kwargs)

        get_select_method = compiler.get_select

        def get_select_wrapper(*args, **kwargs):
            ret, klass_info, annotations = get_select_method(*args, **kwargs)
            new_ret = []
            for ret_data in ret:
                col, (sql, params), alias = ret_data

                [sql_table_name, sql_field_name] = sql.split('.')
                for translation_name in self._source.translations:
                    translation_source = self._source.translations[translation_name]
                    if '"{}"'.format(translation_source) == sql_field_name:
                        sql_field_name = '"{}"'.format(translation_source)
                        sql = '.'.join([sql_table_name, translation_name])
                        sql += ' as {}'.format(sql_field_name)
                        break
                for null_field in self._source.null_fields:
                    if '"{}"'.format(null_field) == sql_field_name:
                        sql = 'Null as {}'.format(sql_field_name)
                        break

                ret_data = col, (sql, params), alias
                new_ret.append(ret_data)

            return new_ret, klass_info, annotations
        compiler.get_select = get_select_wrapper

        get_from_clause_method = compiler.get_from_clause

        def get_from_clause_wrapper(*args, **kwargs):
            result, params = get_from_clause_method(*args, **kwargs)
            result[0] = '{} as {}'.format(
                self._source.raw_query, self.model._meta.db_table)
            params = tuple(self._source.params) + tuple(params)
            return result, params
        compiler.get_from_clause = get_from_clause_wrapper

        return compiler


class RawSugarQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, _source=None, **kwargs) -> None:
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = RawSugarQuery(
                self.model,
                _source=_source)
        return r


class _RawSugarDecoratedManager(models.Manager):
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
        elif self._source_func_is_callable:
            self._source = self._source_func(self.model, *args, **kwargs)
            self._check_source_type()
        else:
            raise TypeError
        return self

    def get_queryset(self):
        if not self._source_func_is_callable:
            self._source = self._source_func(self.model)
            self._check_source_type()

        if isinstance(self._source, FromQuerySet):
            self._source._calculate_null_fields(self.model)

        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source=self._source)


class RawManager(models.Manager):
    def __init__(self, from=None, *args, **kwargs):
        if from is not None:
            assert isinstance(from, FromRaw), \
                "Expected a `FromRaw` to be passed "\
                "to 'from', but received a `%s" % type(from)
        self._source = from
        return super().__init__(*args, **kwargs)

    def get_queryset(self):
        assert isinstance(self._source, FromRaw), \
            "Source was not provided! "\
            "Provide source during initialization or "\
            "use .from_raw or .from_queryset instead."
        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source=self._source)

    def from_raw(self, raw_query=None, params=[],
                 translations={}, null_fields=[],
                 db_table=None):
        source = FromRaw(raw_query, params, translations,
                         null_fields, db_table)
        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source=source)

    def from_queryset(self, queryset, translations={}):
        source = FromQuerySet(queryset, translations)
        source._calculate_null_fields(self.model)
        return RawSugarQuerySet(self.model,
                                using=self._db,
                                _source=source)
