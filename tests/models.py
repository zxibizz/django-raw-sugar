from django.db import models
from raw_sugar.models import FacadeModel, ReadOnlyFacadeModel
from raw_sugar.decorators import manager_from_queryset, manager_from_raw


class TestModelMixin(models.Model):
    class Meta:
        app_label = 'tests'
        abstract = True


class DjangoModel(TestModelMixin):
    text = models.CharField(max_length=100)
    number = models.IntegerField()


class AnotherDjangoModel(TestModelMixin):
    target = models.ForeignKey(DjangoModel, models.CASCADE)
    text = models.CharField(max_length=100)
    number = models.IntegerField()


class TestFacadeModel(ReadOnlyFacadeModel):
    target = models.ForeignKey(DjangoModel, models.CASCADE, related_name='+')
    text = models.CharField(max_length=100)
    sum_text = models.CharField(max_length=200)
    number = models.IntegerField()
    diff_number = models.IntegerField()

    @manager_from_raw
    def raw_objects(cls):
        return ''

    @manager_from_queryset
    def queryset_objects(cls):
        return AnotherDjangoModel.objects.all()

    @manager_from_raw(is_method=True)
    def callable_queryset_objects(cls, *args, **kwargs):
        return ''

    @manager_from_queryset(is_method=True)
    def callable_raw_objects(cls, *args, **kwargs):
        return AnotherDjangoModel.objects.all()

    class Meta:
        app_label = 'tests'


class MySimpleModel(FacadeModel):
    name = models.TextField()
    number = models.IntegerField()

    @manager_from_raw
    def my_raw_source(cls):
        return 'SELECT Null as id, "my str" as name, 111 as number, 1 as source_id'

    @manager_from_raw(is_method=True)
    def my_callable_raw_source(cls, name, number):
        return f'SELECT Null as id, "{name}" as name, {number} as number, 1 as source_id'
