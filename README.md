# django-raw-sugar

Turns your raw sql into a QuerySet.

## Installation

Install using `pip`...

    pip install django-raw-sugar

## How to use
### Basic usage
Attach `RawManager` instance to your model. Then use it's `.from_raw()` method.

    RawManager.from_raw(raw_query=None, params=None, translations=None, null_fields=None, db_table=None)

You should pass at least either `raw_query` or `db_table` (but not both).

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

The queried table must contain all the fields that are present in target model, including primary key and foreign keys. If you know your query lacks some fields, you can provide the `null_fields` argument instead of modifying your query:

```python
queryset = MySimpleModel.objects.from_raw(
    'SELECT "my str" as name, 111 as number', null_fields=['id', 'source_id'])
```

The resulting queryset is a regular `models.QuerySet` instance, and can be handled accordingly:

```python
queryset = queryset.filter(number__gte=10)\
    .exclude(number__gte=1000)\
    .filter(name__contains='s')\
    .order_by('number')\
    .select_related('source')
print(queryset[0].name) # "my str"
```

### Passing parameters
If you need to perform parameterized queries, you can use the `params` argument:
```python
queryset = MySimpleModel.objects.from_raw(
    'SELECT "%s" as name, 111 as number', 
    params=['my str'],
    null_fields=['id', 'source_id'])
```
### Using transtalions
If the field names of queried table differ from the model field names, you can map fields using the `translations` argument:
```python
queryset = MySimpleModel.objects.from_raw(
    'SELECT "%s" as name, 111 as inner_number', 
    params=['my str'],
    translations={'inner_number': 'number'},
    null_fields=['id', 'source_id'])
```

### Default raw sql
You can define a model manager that uses your raw sql as query source by default. You can do this by passing a `from_raw` argument to RawManager, or by using the `raw_manager` decorator to method that returns a `FromRaw` instance:

```python
from django.db import models
from raw_sugar import raw_manager, RawManager, FromRaw

class MySimpleModel(models.model):
    name = models.TextField()
    number = models.IntegerField()
    source = models.ForeignKey(AnotherSimpleModel, models.DO_NOTHING)

    my_raw_manager = RawManager(FromRaw('SELECT "my str" as name, 111 as number',
                                        null_fields=['id', 'source_id']))

    @raw_manager
    def my_raw_manager_2(cls):
        return FromRaw('SELECT "my str" as name, 111 as number',
                       null_fields=['id', 'source_id'])

    @raw_manager(is_callable=True)
    def my_callable_raw_manager(cls, name=""):
        return FromRaw('SELECT %s as name, 111 as number',
                       null_fields=['id', 'source_id'],
                       params=[name])

# some other file
from .models import MySimpleModel

queryset = MySimpleModel.my_raw_source.all()
queryset = MySimpleModel.my_raw_source_2.all()
queryset = MySimpleModel.my_callable_raw_source('my str').all()

print(queryset[0].name) # "my str"
```
The `FromRaw` class accepts all the arguments as the `RawManager.from_raw`:

    FromRaw(raw_query=None, params=None, translations=None, null_fields=None, db_table=None)

### Querying views / table functions
If you have a sql view or a sql table function in your database and want to query it, instead of passing sql like `SELECT * from my_view` you can use the `db_table` argument instead:
```python
queryset = MySimpleModel.objects.from_raw(db_table='my_view')
queryset = MySimpleModel.objects.from_raw(db_table='my_func(%s, %s)', params=['param', 1])
```

## Differences with `Manager.raw()`
Pros:
 - The result of executing of your raw sql is a **QuerySet** (!!!), and can filter, order, union, etc. it.

Cons:
 - Your raw sql must contain all fields of target model, including foreign keys. If you'll omit one, you get an `OperationalError('no such column: ...')`
 - If you queried `Null` as the value of a field, this field won't be queried when accessing it from the model instance.
