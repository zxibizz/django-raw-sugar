# django-dynamic-source-models

A package that provides functionality to create a django models with dynamic source (either from raw sql or django queryset)

## Installation

Install using `pip`...

    pip install django-dynamic-source-models


## Quick start

First of all you will need existing models in your application:

```python
from django.db import models

class Product(models.Model):
    name = models.TextField()

class Warehouse(models.Model):
    name = models.TextField()

class StockTransaction(models.Model):
    outbound = models.BooleanField()
    product = models.ForeignKey(Product, models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, models.PROTECT)
    quantity = models.IntegerField()
```

Create a dynamic source model. Attention: dynamic models cannot be accessed through RelatedManager, and it worth it to set `related_name='+'` for the ForeighKey fields

```python
from dynamic_source_models.models import DynamicSourceModel

class StockBalance(DynamicSourceModel):
    product = models.ForeignKey(Product, models.PROTECT, related_name='+')
    warehouse = models.ForeignKey(Warehouse, models.PROTECT, related_name='+')
    balance = models.IntegerField(default=0)
```

Query by providing a source queryset

```python
source_queryset = StockTransaction.objects\
    .values('product', 'warehouse')\
    .annotate(balance=Sum(
        Case(
            When(outbound=False,
                then=F('quantity')*-1),
                default=F('quantity')
        ), 
        output_field=IntegerField())
    ).all()

qs = StockBalance.from_queryset(source_queryset).all()
qs = qs.select_related('product')
qs = qs.filter(quantity__gte=10).exclude(warehouse__id=666)
```

Query by providing a raw sql

```python
qs = StockBalance.from_raw('SELECT Null as id, Null as product_id, 1 as warehouse_id, %s as balance', [123]).all()
```

Add sources in the model

```python
from dynamic_source_models.models import DynamicSourceModel
from dynamic_source_models.decorators import source_queryset, source_raw

class StockBalance(DynamicSourceModel):
    product = models.ForeignKey(Product, models.PROTECT, related_name='+')
    warehouse = models.ForeignKey(Warehouse, models.PROTECT, related_name='+')
    quantity = models.IntegerField(default=0)

    @source_raw
    def my_raw_source(cls):
        raw_sql = 'SELECT Null as id, Null as product_id, Null as warehouse_id, %s as quantity'
        params = [123]
        return raw_sql, params

    @source_queryset(callable=True)
    def my_queryset_source(cls, group_by=None):
        if group_by is None:
            group_by = ['product', 'warehouse']

        qs = StockTransaction.objects\
            .values('product', 'warehouse')\
            .annotate(_quantity=Sum(
                Case(
                    When(outbound=False,
                        then=F('quantity')*-1),
                        default=F('quantity')
                ), 
                output_field=IntegerField())
            ).all()
        return qs
```

You can use sources as usual model managers

```python
StockBalance.my_raw_source.all().filter(quantity__gte=12)
StockBalance.my_queryset_source(group_by=['product']).exclude(product_id__lt=10)
```
