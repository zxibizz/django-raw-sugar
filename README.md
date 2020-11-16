# django-database-view

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

Query from dynamic model

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
```
