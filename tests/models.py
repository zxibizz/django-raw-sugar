from django.db import models
from raw_sugar import raw_manager, RawManager, FromRaw, FromQuerySet


class AnotherSimpleModel(models.Model):
    pass


class MySimpleModel(models.Model):
    name = models.TextField()
    number = models.IntegerField()
    source = models.ForeignKey(
        AnotherSimpleModel, models.DO_NOTHING, null=True)

    objects = RawManager()

    my_raw_manager = RawManager(FromRaw('SELECT "my str" as name, 111 as number',
                                        null_fields=['id', 'source_id']))

    @raw_manager
    def my_raw_manager_2(cls):
        return FromRaw('SELECT "my str" as name, 111 as number',
                       null_fields=['id', 'source_id'])

    @raw_manager(is_callable=True)
    def my_callable_raw_manager(cls, name):
        return FromRaw('SELECT %s as name, 111 as number',
                       null_fields=['id', 'source_id'],
                       params=[name])

    @raw_manager
    def my_qs_manager(cls):
        return FromQuerySet(
            cls.objects.values('source').annotate(
                _number=models.Sum('number')),
            translations={'_number': 'number'})
