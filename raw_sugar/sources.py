from copy import copy
from django.db import connection


class SourceRaw:
    def copy(self):
        return copy(self)

    def with_params(self, *args):
        clone = self.copy()
        clone.params = args
        return clone


class FromRaw(SourceRaw):
    def __init__(self, raw_query=None, params=None,
                 translations=None, null_fields=None,
                 db_table=None):
        assert raw_query or db_table, \
            "Either `raw_query` or `db_table` must be provided!"
        assert not raw_query or not db_table, \
            "Either `raw_query` or `db_table` must be provided, not both!"
        self.raw_query = db_table or '({})'.format(raw_query)
        self.params = params or []
        self.translations = translations or {}
        self.null_fields = null_fields or []


class FromQuerySet(SourceRaw):
    def __init__(self, queryset, translations=None):
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
        self._queryset_fields = queryset_fields

        raw_query, params = queryset.query.as_sql(
            connection=connection, compiler=None)
        self.raw_query = "({})".format(raw_query)
        self.params = params
        self.translations = translations or {}
        self.null_fields = []

    def _set_target_model(self, model):
        model_fields = [f.column for f in model._meta.fields]
        self.null_fields = list(
            set(model_fields) - set(self._queryset_fields))
