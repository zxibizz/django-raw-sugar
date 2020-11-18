from django.db import models, connection


class FacadeModelQuery(models.sql.Query):
    def __init__(self, *args, source_raw=None, source_params=None,
                 source_translations=None, **kwargs):
        self._source_raw = source_raw
        self._source_params = source_params or []
        self._source_translations = source_translations or {}
        r = super().__init__(*args, **kwargs)
        return r

    def get_compiler(self, *args, **kwargs):
        compiler = super().get_compiler(*args, **kwargs)

        get_from_clause_method = compiler.get_from_clause

        def wrapper(*args, **kwargs):
            result, params = get_from_clause_method(*args, **kwargs)
            assert result[0] == f'"{self.model._meta.db_table}"'
            if self._source_translations:
                from_fields = ','.join([
                    f'temp.{t} as {tt}' for t, tt in self._source_translations.items()
                ])
                from_table = f'(SELECT *, {from_fields} FROM ({self._source_raw}) as temp) as {self.model._meta.db_table}'
            else:
                from_table = f'({self._source_raw}) as {self.model._meta.db_table}'
            result[0] = from_table
            params = tuple(self._source_params) + tuple(params)
            return result, params

        compiler.get_from_clause = wrapper

        return compiler


class FacadeModelQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, source_raw=None,
                 source_params=[], source_translations=None, **kwargs) -> None:
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = FacadeModelQuery(
                self.model,
                source_raw=source_raw,
                source_params=source_params,
                source_translations=source_translations)
        return r


class RawFacadeManager(models.Manager):
    def __call__(self, raw_query, params=None, translations=None):
        self._source_raw = raw_query
        self._source_params = params
        self._source_translations = translations
        return self

    def get_queryset(self):
        if self._source_raw is None:
            raise Exception('Source raw was not provided!')

        return FacadeModelQuerySet(
            self.model, using=self._db,
            source_raw=self._source_raw,
            source_params=self._source_params,
            source_translations=self._source_translations,
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

        for field in set(model_fields) - set(queryset_fields):
            queryset = queryset.annotate(
                **{f'{field}': models.Value(None, self._get_model_field(field))})

        source_raw, source_params = queryset.query.as_sql(
            connection=connection, compiler=None)
        self._source_raw = source_raw
        self._source_params = source_params
        self._source_translations = translations

        return self

    def _get_model_field(self, column):
        for field in self.model._meta.fields:
            if field.column == column:
                return field
