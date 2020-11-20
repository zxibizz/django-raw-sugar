from django.db import connection


class FromRaw:
    def __init__(self, raw_query=None, params=[],
                 translations={}, null_fields=[],
                 db_table=None):
        assert raw_query or db_table, \
            "Either `raw_query` or `db_table` must be provided!"
        assert not raw_query or not db_table, \
            "Either `raw_query` or `db_table` must be provided, not both!"
        self.raw_query = db_table or '({})'.format(raw_query)
        self.params = params
        self.translations = translations
        self.null_fields = null_fields


class FromQuerySet:
    def __init__(self, queryset, translations={}):
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
        self.translations = translations
        self.null_fields = []

    def _calculate_null_fields(self, target_model):
        model_fields = [f.column for f in target_model._meta.fields]
        self.null_fields = list(set(model_fields) - set(self._queryset_fields))
