# -*- coding: utf-8 -*-

from django.utils.unittest import TestCase
from django.utils import unittest
from django.db import connection, transaction

from .models import Person, Person2, Person3, Book

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
        obj.update_search_field(using='default')

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
        if not hasattr(transaction, "atomic"):
            return

        with transaction.atomic():
            obj = Person2.objects.create(
                name=u'Pepa',
                description=u"Is a housewife",
            )

            obj.update_search_field(using='default')

        qs = Person2.objects.search(query="Pepa")
        self.assertEqual(qs.count(), 2)

    def test_ranking_with_join(self):
        book = Book.objects.create(name='Learning Python', author=self.p1)

        qs = Book.objects.search(query='Learning Python', rank_field='rank').select_related('author')

        self.assertEqual(qs[0].author, self.p1)

    def test_headline(self):
        book = Book.objects.create(name='Learning Python', author=self.p1)

        qs = Book.objects.search(query='Python', headline_field='headline', headline_document='name')

        self.assertEqual(qs[0].headline, 'Learning <b>Python</b>')
