from django.db import models


class RawSugarQuery(models.sql.Query):
    def __init__(self, *args, _source=None, **kwargs):
        self._source = _source
        return super().__init__(*args, **kwargs)

    def get_compiler(self, *args, **kwargs):
        compiler = super().get_compiler(*args, **kwargs)
        get_from_clause_method = compiler.get_from_clause

        def get_from_clause_wrapper(*args, **kwargs):
            qn = compiler.connection.ops.quote_name
            result, params = get_from_clause_method(*args, **kwargs)
            if len(self._source.translations) > 0 or len(self._source.null_fields) > 0:
                wrapper_fields = []
                for left, right in self._source.translations.items():
                    wrapper_fields.append(
                        '{}.{} AS {}'.format(qn('wrapper_table'),  qn(left), qn(right)))
                for null_field in self._source.null_fields:
                    wrapper_fields.append('NULL AS {}'.format(qn(null_field)))
                wrapper = '(SELECT *, {} FROM {} AS {})'.format(
                    ','.join(wrapper_fields),
                    self._source.raw_query,
                    qn('wrapper_table'))
            else:
                wrapper = self._source.raw_query
            result[0] = '{} AS {}'.format(
                wrapper, qn(self.model._meta.db_table))
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
