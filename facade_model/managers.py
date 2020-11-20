from django.db import models, connection


class FacadeModelQuery(models.sql.Query):
    def __init__(self, *args, source_raw=None,
                 source_params=None, source_translations=None,
                 source_null_fields=None, **kwargs):
        self._source_raw = source_raw
        self._source_params = source_params or []
        self._source_translations = source_translations or {}
        self._source_null_fields = source_null_fields or []

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
                for translation_name in self._source_translations:
                    translation_source = self._source_translations[translation_name]
                    if '"{}"'.format(translation_source) == sql_field_name:
                        sql_field_name = '"{}"'.format(translation_source)
                        sql = '.'.join([sql_table_name, translation_name])
                        sql += ' as {}'.format(sql_field_name)
                        break
                for null_field in self._source_null_fields:
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
            result[0] = '({}) as {}'.format(
                self._source_raw, self.model._meta.db_table)
            params = tuple(self._source_params) + tuple(params)
            return result, params
        compiler.get_from_clause = get_from_clause_wrapper

        return compiler


class FacadeModelQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, source_raw=None,
                 source_params=[], source_translations=None,
                 source_null_fields=None, **kwargs) -> None:
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = FacadeModelQuery(
                self.model,
                source_raw=source_raw,
                source_params=source_params,
                source_translations=source_translations,
                source_null_fields=source_null_fields)
        return r


class RawFacadeManager(models.Manager):
    def __call__(self, raw_query, params=None, translations=None, null_fields=None):
        self._source_raw = raw_query
        self._source_params = params
        self._source_translations = translations
        self._source_null_fields = null_fields
        return self

    def get_queryset(self):
        if self._source_raw is None:
            raise Exception('Source raw was not provided!')

        return FacadeModelQuerySet(
            self.model, using=self._db,
            source_raw=self._source_raw,
            source_params=self._source_params,
            source_translations=self._source_translations,
            source_null_fields=self._source_null_fields
        )


class ReadOnlyRawFacadeManager(models.Manager):
    def bulk_create(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def get_or_create(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError


class QuerysetFacadeManager(RawFacadeManager):
    def __call__(self, queryset, translations=None):
        queryset_fields = list(queryset.query.annotations.keys())
        if translations:
            queryset_fields += [translations[i] for i in translations]
        if len(queryset.query.values_select) > 0:
            for field_name in queryset.query.values_select:
                for field in queryset.model._meta.fields:
                    if field.name == field_name:
                        queryset_fields.append(field.column)
                        break
                else:
                    queryset_fields.append(field_name)
        else:
            queryset_fields += [field.column for field in queryset.model._meta.fields]

        model_fields = [f.column for f in self.model._meta.fields]
        null_fields = list(set(model_fields) - set(queryset_fields))

        source_raw, source_params = queryset.query.as_sql(
            connection=connection, compiler=None)
        self._source_raw = source_raw
        self._source_params = source_params
        self._source_translations = translations
        self._source_null_fields = null_fields

        return self

    def _get_model_field(self, column):
        for field in self.model._meta.fields:
            if field.column == column:
                return field
