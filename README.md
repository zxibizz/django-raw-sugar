# django-raw-sugar

Turns your raw sql into a QuerySet.

## Installation

Install using `pip`...

    pip install django-raw-sugar

## How to use

```python
# models.py
from django.db import models
from raw_sugar import RawManager

class MySimpleModel(models.Model):
    name = models.TextField()
    number = models.IntegerField()
    source = models.ForeignKey(AnotherSimpleModel, models.DO_NOTHING)
    
    objects = RawManager()

# some other file
from .models import MySimpleModel

queryset = MySimpleModel.objects.from_raw(
    'SELECT Null as id, "my str" as name, 111 as number, Null as source_id')
```

You can treat the result queryset as a regular `models.QuerySet`:

```python
queryset = queryset.filter(number__gte=10)\
    .exclude(number__gte=1000)\
    .filter(name__contains='s')\
    .order_by('number')\
    .select_related('source')
print(queryset[0].name) # "my str"
```

You can define a model manager that uses your raw sql to query result:

```python
from django.db import models
from raw_sugar import manager_from_raw

class MySimpleModel(models.model):
    name = models.TextField()
    number = models.IntegerField()
    source = models.ForeignKey(AnotherSimpleModel, models.DO_NOTHING)

    @manager_from_raw
    def my_raw_source(cls):
        return 'SELECT Null as id, "my str" as name, 111 as number, 1 as source_id'
```

And then use it as like as any another `models.QuerySet`:

```python
from .models import MySimpleModel

queryset = MySimpleModel.my_raw_source\
    .filter(number__gte=10)\
    .exclude(number__gte=1000)\
    .filter(name__contains='s')\
    .order_by('number')\
    .select_related('source')
print(queryset[0].name) # "my str"
```

You can do even more, and pass extra parameters to the manager:

```python
from django.db import models
from raw_sugar import manager_from_raw

class MySimpleModel(FacadeModel):
    name = models.TextField()
    number = models.IntegerField()
    source = models.ForeignKey(AnotherSimpleModel, models.DO_NOTHING)

    @manager_from_raw(is_method=True)
    def my_callable_raw_source(cls, id='Null', name="", number=0):
        return f'SELECT {id} as id, "{name}" as name, {number} as number, 1 as source_id'

# some other file
from .models import MySimpleModel

queryset = MySimpleModel.my_callable_raw_source(name='my param').all()
print(queryset[0].name) # "my param"
```

## Restrictions
There are several features that must be taken into account when using this package:
- The result of a query should provide all field that the target model has in database, including primary key (`id` in most situations). If your raw query doesn't have some of fields, you can provide additional parameter called `null_fields`
    ```python
    queryset = MySimpleModel.objects.from_raw(
        'SELECT "my str" as name', null_fields=['id', 'number', 'source_id'])
    ```
- If you have a sql view or sql table function in your database and want to query from it, instead of providing sql like "`SELECT * from my_view`" you can use the "`db_table`" parameter instead
    ```python
    queryset = MySimpleModel.objects.from_raw(db_table='my_view')
    ```
