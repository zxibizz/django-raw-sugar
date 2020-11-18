from django.db import models

from .managers import (
    RawFacadeManager,
    QuerysetFacadeManager,
    ReadOnlyRawFacadeManager,
)


class FacadeModel(models.Model):
    from_raw = RawFacadeManager()
    from_queryset = QuerysetFacadeManager()

    class Meta:
        abstract = True


class ReadOnlyFacadeModel(FacadeModel):
    from_raw = ReadOnlyRawFacadeManager()
    objects = None

    class Meta:
        abstract = True
        managed = False
