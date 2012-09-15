# -*- coding: utf-8 -*-

from django.utils.unittest import TestCase
from django.utils import unittest
from django.db import connection, transaction

from .models import Person, Person2, Person3

class TestFts(TestCase):
    def setUp(self):
        Person.objects.all().delete()

        self.p1 = Person.objects.create(
            name=u'Andréi',
            description=u"Python programmer",
        )
        self.p2 = Person.objects.create(
            name=u'Pèpâ',
            description=u"Is a housewife",
        )


    def test_self_update_index(self):
        obj = Person2.objects.create(
            name=u'Pepa',
            description=u"Is a housewife",
        )
        obj.update_search_field()

        qs = Person2.objects.search(query="Pepa")
        self.assertEqual(qs.count(), 1)

    def test_self_automatic_update_index(self):
        obj = Person3(
            name=u'Pèpâ',
            description=u"Is a housewife",
        )

        obj.save()

        qs = Person3.objects.search(query="Pepa")
        self.assertEqual(qs.count(), 1)

        obj.name = 'Andrei'
        obj.save()

        qs = Person3.objects.search(query="Pepa")
        self.assertEqual(qs.count(), 0)

    def test_search_and(self):
        qs1 = Person.objects.search(query="programmer", raw=True)
        qs2 = Person.objects.search(query="Andrei", raw=True)

        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs2.count(), 1)

    def test_search_and_2(self):
        qs1 = Person.objects.search(query="Andrei & programmer", raw=True)
        qs2 = Person.objects.search(query="Pepa & housewife", raw=True)
        qs3 = Person.objects.search(query="Pepa & programmer", raw=True)

        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs2.count(), 1)
        self.assertEqual(qs3.count(), 0)

    def test_search_with_fields_params(self):
        qs1 = Person.objects.search(query="Andrei & programmer", raw=True, fields=['name'])
        qs2 = Person.objects.search(query="Andrei & programmer", raw=True, fields=['name', 'description'])

        self.assertEqual(qs1.count(), 0)
        self.assertEqual(qs2.count(), 1)

    def test_search_or(self):
        qs1 = Person.objects.search(query="Andrei | Pepa", raw=True)
        qs2 = Person.objects.search(query="Andrei | Pepo", raw=True)
        qs3 = Person.objects.search(query="Pèpâ | Andrei", raw=True)
        qs4 = Person.objects.search(query="Pepo | Francisco", raw=True)

        self.assertEqual(qs1.count(), 2)
        self.assertEqual(qs2.count(), 1)
        self.assertEqual(qs3.count(), 2)
        self.assertEqual(qs4.count(), 0)

    def test_update_indexes(self):
        self.p1.name = 'Francisco'
        self.p1.save()

        qs = Person.objects.search(query="Pepo | Francisco", raw=True)
        self.assertEqual(qs.count(), 1)

    def test_transaction_test(self):
        class TestException(Exception):
            pass

        p = Person3(
            name='Andrei1',
            description='description1',
        )
        p.save()

        try:
            with transaction.commit_on_success():
                p.name = 'Andrei2'
                p.save()

                qs = Person3.objects.search(query="Andrei2")
                self.assertEqual(qs.count(), 1)
                raise TestException()
        except TestException:
            pass

        qs = Person3.objects.search(query="Andrei2")
        self.assertEqual(qs.count(), 0)
