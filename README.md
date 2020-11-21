# django-facade-model

Turns your raw sql into a QuerySet.

## Installation

Install using `pip`...

    pip install django-facade-model

## How to use

Inherit your models from `FacadeModel` instead of `models.Model` (or `ReadOnlyFacadeModel` if you don't want your model to be created in database):

```python
# models.py
from django.db import models

from raw_sugar.models import FacadeModel, ReadOnlyFacadeModel

class MySimpleModel(FacadeModel): # or ReadOnlyFacadeModel
    name = models.TextField()
    number = models.IntegerField()
    source = models.ForeignKey(AnotherSimpleModel, models.DO_NOTHING)

# some other file
from .models import MySimpleModel

queryset = MySimpleModel.from_raw(
    'SELECT Null as id, "my str" as name, 111 as number, 1 as source_id')
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
from raw_sugar.models import FacadeModel
from raw_sugar.decorators import manager_from_raw

class MySimpleModel(FacadeModel):
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

from raw_sugar.models import FacadeModel
from raw_sugar.decorators import manager_from_raw

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
There are some restrictions that are put on the raw sql you provide:
- The result of a query should provide all field that the target model has in database, including primary key (`id` in most situations).
- The result of a query should be a table (if you have a sql view or a table function in your database, you should provide something like `Select * from my_view`, not just `my_view`)
