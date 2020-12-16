from django.test import TestCase
from .models import MySimpleModel, AnotherSimpleModel


class DynamicQueringTest(TestCase):
    def setUp(self):
        asm1 = AnotherSimpleModel.objects.create()
        asm2 = AnotherSimpleModel.objects.create()
        MySimpleModel.objects.create(
            name='django model 1', number=1, source=asm1)
        MySimpleModel.objects.create(
            name='django model 2', number=2, source=asm1)
        MySimpleModel.objects.create(
            name='django model 3', number=3, source=asm1)
        MySimpleModel.objects.create(
            name='django model 4', number=4, source=asm1)
        MySimpleModel.objects.create(
            name='django model 5', number=5, source=asm2)

    def test_readme_example_0(self):
        queryset = MySimpleModel.objects.all().order_by('id')

        self.assertTrue(queryset.count() == 5)

        res = queryset[0]

        self.assertTrue(res.name == 'django model 1')
        self.assertTrue(res.number == 1)
        self.assertTrue(res.source_id == 1)

    def test_readme_example_1(self):
        queryset = MySimpleModel.objects.from_raw(
            'SELECT Null as id, "my str" as name, 111 as number, Null as source_id')

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')\
            .select_related('source')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_readme_example_2(self):
        queryset = MySimpleModel.objects.from_raw(
            'SELECT "my str" as name, 111 as number', null_fields=['id', 'source_id'])

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')\
            .select_related('source')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_readme_example_3(self):
        queryset = MySimpleModel.objects.from_raw(
            'SELECT %s as name, 111 as number',
            params=['my str'],
            null_fields=['id', 'source_id'])

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_readme_example_4(self):
        queryset = MySimpleModel.objects.from_raw(
            'SELECT %s as name, 111 as inner_number',
            params=['my str'],
            translations={'inner_number': 'number'},
            null_fields=['id', 'source_id'])

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_readme_example_5(self):
        queryset = MySimpleModel.my_raw_manager.all()

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_readme_example_6(self):
        queryset = MySimpleModel.my_raw_manager_2.all()

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_readme_example_7(self):
        queryset = MySimpleModel.my_callable_raw_manager('my str').all()

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_decorated_manager_from_1(self):
        queryset = MySimpleModel.my_raw_manager_2.from_raw(
            'SELECT %s as name, 111 as inner_number',
            params=['my str'],
            translations={'inner_number': 'number'},
            null_fields=['id', 'source_id'])

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_decorated_manager_from_2(self):
        queryset = MySimpleModel.my_callable_raw_manager.from_raw(
            'SELECT %s as name, 111 as inner_number',
            params=['my str'],
            translations={'inner_number': 'number'},
            null_fields=['id', 'source_id'])

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_call_not_callable(self):
        try:
            MySimpleModel.my_raw_manager_2().all()
        except TypeError:
            return

        self.assertTrue(False)

    def test_query_callable_directly(self):
        try:
            MySimpleModel.my_callable_raw_manager.all()[0]
        except TypeError:
            return

        self.assertTrue(False)

    def test_deferred_params_1(self):
        queryset = MySimpleModel.my_callable_raw_manager.all()\
            .with_params('my str')

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')\
            .select_related('source')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_deferred_params_2(self):
        queryset = MySimpleModel.objects.from_raw(
            'SELECT Null as id, %s as name, 111 as number, Null as source_id')\
            .with_params('my str')

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .filter(name__contains='s')\
            .order_by('number')\
            .select_related('source')

        res = queryset[0]

        self.assertTrue(res.name == 'my str')
        self.assertTrue(res.number == 111)

    def test_from_queryset_1(self):
        queryset = MySimpleModel.my_qs_manager.all()

        queryset = queryset.filter(number__gte=10)\
            .exclude(number__gte=1000)\
            .order_by('source')\
            .select_related('source')

        res = queryset[0]

        self.assertTrue(res.name is None)
        self.assertTrue(res.number == 10)
