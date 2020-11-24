from django.db import models
from django.db.models.sql import Query

from raw_sugar.sources import SourceRaw, FromQuerySet


class RawSugarQuery(Query):
    def __init__(self, *args,
                 _source_func=None,
                 _source_func_args=None,
                 _source_func_kwargs=None,
                 **kwargs):
        self._source_func = _source_func
        self._source_func_args = _source_func_args
        self._source_func_kwargs = _source_func_kwargs
        return super().__init__(*args, **kwargs)

    def get_compiler(self, *args, **kwargs):
        compiler = super().get_compiler(*args, **kwargs)
        get_from_clause_method = compiler.get_from_clause

        def get_from_clause_wrapper(*args, **kwargs):
            source = self._source_func(
                self.model,
                *(self._source_func_args or []),
                **(self._source_func_kwargs or {}))
            assert isinstance(source, SourceRaw)
            if isinstance(source, FromQuerySet):
                source._set_target_model(self.model)

            qn = compiler.connection.ops.quote_name
            result, params = get_from_clause_method(*args, **kwargs)
            assert result[0] == qn(self.model._meta.db_table)
            if len(source.translations) > 0 or len(source.null_fields) > 0:
                select_fields = []
                for col in self.model._meta.fields:
                    field_name = col.column
                    if not field_name in source.translations.values()\
                            and not field_name in source.null_fields:
                        select_fields.append('{}.{}'.format(
                            qn('wrapper_table'),
                            qn(field_name)))
                for null_field in source.null_fields:
                    select_fields.append('NULL AS {}'.format(
                        qn(null_field)))
                for translation_field in source.translations.items():
                    select_fields.append('{}.{} AS {}'.format(
                        qn('wrapper_table'),
                        qn(translation_field[0]),
                        qn(translation_field[1])))
                wrapper = '(SELECT {} FROM {} AS {})'.format(
                    ', '.join(select_fields),
                    source.raw_query,
                    qn('wrapper_table'))
            else:
                wrapper = source.raw_query
            result[0] = '{} AS {}'.format(
                wrapper, qn(self.model._meta.db_table))
            params = tuple(source.params) + tuple(params)
            return result, params

        compiler.get_from_clause = get_from_clause_wrapper
        return compiler


class RawSugarQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, _source_func=None,
                 _source_func_args=None, _source_func_kwargs=None,
                 **kwargs):
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = RawSugarQuery(
                self.model,
                _source_func=_source_func,
                _source_func_args=_source_func_args,
                _source_func_kwargs=_source_func_kwargs)
        return r

    def with_params(self, *args, **kwargs):
        clone = self._chain()
        clone.query._source_func_args = args
        clone.query._source_func_kwargs = kwargs
        return clone
