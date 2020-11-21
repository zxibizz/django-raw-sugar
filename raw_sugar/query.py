from django.db import models


class _RawQuery(models.sql.Query):
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


class _RawQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, _source=None, **kwargs) -> None:
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = _RawQuery(
                self.model,
                _source=_source)
        return r
