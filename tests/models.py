from django.db import models
from raw_sugar import raw_manager, RawManager, FromRaw, FromQuerySet


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


class TestFacadeModel(TestModelMixin):
    target = models.ForeignKey(DjangoModel, models.CASCADE, related_name='+')
    text = models.CharField(max_length=100)
    sum_text = models.CharField(max_length=200)
    number = models.IntegerField()
    diff_number = models.IntegerField()

    @raw_manager
    def raw_objects(cls):
        return ''

    @raw_manager
    def queryset_objects(cls):
        return AnotherDjangoModel.objects.all()

    @raw_manager(is_callable=True)
    def callable_queryset_objects(cls, *args, **kwargs):
        return ''

    @raw_manager(is_callable=True)
    def callable_raw_objects(cls, *args, **kwargs):
        return AnotherDjangoModel.objects.all()

    class Meta:
        managed = False


class MySimpleModel(TestModelMixin):
    name = models.TextField()
    number = models.IntegerField()

    objects = RawManager()

    @raw_manager
    def my_raw_source(cls):
        return FromRaw('SELECT Null as id, "my str" as name, 111 as number, 1 as source_id')

    @raw_manager(is_callable=True)
    def my_callable_raw_source(cls, name, number):
        return FromRaw(f'SELECT Null as id, "{name}" as name, {number} as number, 1 as source_id')

    class Meta:
        managed = False
