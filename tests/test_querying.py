from django.test import TestCase
from .models import (
    DjangoModel, AnotherDjangoModel,
    TestFacadeModel, MySimpleModel
)


class DynamicQueringTest(TestCase):
    def setUp(self):
        djm1 = DjangoModel.objects.create(text='django model 1', number=1)
        djm2 = DjangoModel.objects.create(text='django model 2', number=2)
        adjm1 = AnotherDjangoModel.objects.create(
            text='another django model 1', number=11, target=djm1)
        adjm2 = AnotherDjangoModel.objects.create(
            text='another django model 2', number=21, target=djm2)

    def test_queryset(self):
        qs = TestFacadeModel.from_queryset(
            AnotherDjangoModel.objects.all()
        ).all()
        self.assertTrue(len(qs) == 2)

    def test_from_raw(self):
        AnotherDjangoModel.objects.raw(
            'SELECT Null as id, "my str" as f1, 111 as number', translations={'f1': 'name'})[0]

        queryset = MySimpleModel.from_raw(
            'SELECT Null as id, "my str" as name, 111 as number').all()
        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')
        res = queryset[0]
        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_source(self):
        queryset = MySimpleModel.my_raw_source.all()
        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')
        res = queryset[0]
        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_callable_source(self):
        queryset = MySimpleModel.my_callable_raw_source('my param', 111).all()
        res = queryset[0]
        self.assertTrue(res.name == 'my param')
        self.assertTrue(res.number == 111)
