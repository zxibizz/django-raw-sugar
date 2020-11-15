from django.db import models, connection


class DynamicSourceQuery(models.sql.Query):
    def __init__(self, *args, source_raw=None, source_params=[], **kwargs):
        self._source_raw = source_raw
        self._source_params = source_params
        r = super().__init__(*args, **kwargs)
        return r

    def get_compiler(self, *args, **kwargs):
        compiler = super().get_compiler(*args, **kwargs)

        get_from_clause_method = compiler.get_from_clause

        def wrapper(*args, **kwargs):
            result, params = get_from_clause_method(*args, **kwargs)
            assert result[0] == f'"{self.model._meta.db_table}"'
            from_table = f'({self._source_raw}) as {self.model._meta.db_table}'
            result[0] = from_table
            params = tuple(self._source_params) + tuple(params)
            return result, params

        compiler.get_from_clause = wrapper

        return compiler


class DynamicSourceQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, source_raw=None, source_params=[], **kwargs) -> None:
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = DynamicSourceQuery(
                self.model, source_raw=source_raw, source_params=source_params)
        return r


class RawSourceManager(models.Manager):
    def __init__(self, *args, source_raw=None, source_params=[], **kwargs):
        r = super().__init__(*args, **kwargs)
        self._source_raw = source_raw
        self._source_params = source_params
        return r

    def __call__(self, source_raw, source_params):
        self._source_raw = source_raw
        self._source_params = source_params
        return self

    def get_queryset(self):
        if self._source_raw is None:
            raise Exception('Source raw was not provided!')

        return DynamicSourceQuerySet(
            self.model, using=self._db,
            source_raw=self._source_raw,
            source_params=self._source_params
        )

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


class QuerySetSourceManager(RawSourceManager):
    def __init__(self, *args, source_queryset=None, **kwargs):
        r = super().__init__(*args, **kwargs)
        if source_queryset:
            self(source_queryset)
        return r

    def __call__(self, source_queryset):
        queryset_fields = list(source_queryset.query.annotations.keys())
        for field_name in source_queryset.query.values_select:
            for field in source_queryset.model._meta.fields:
                if field.name == field_name:
                    queryset_fields.append(field.column)
                    break
            else:
                queryset_fields.append(field_name)
        
        model_fields = [f.column for f in self.model._meta.fields]

        for field in set(model_fields) - set(queryset_fields):
            source_queryset = source_queryset.annotate(
                **{f'{field}': models.Value(None, self._get_model_field(field))})

        source_raw, source_params = source_queryset.query.as_sql(
            connection=connection, compiler=None)
        self._source_raw = source_raw
        self._source_params = source_params

        return self

    def _get_model_field(self, column):
        for field in self.model._meta.fields:
            if field.column == column:
                return field


class DynamicSourceModel(models.Model):
    from_raw = RawSourceManager()
    from_queryset = QuerySetSourceManager()

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        raise NotImplementedError

    class Meta:
        abstract = True
        managed = False
