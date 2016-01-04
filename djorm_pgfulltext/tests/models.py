# -*- coding: utf-8 -*-
import json

from django.db import models, connections

from ..fields import VectorField
from ..models import SearchManager


class Person(models.Model):
    name = models.CharField(max_length=32)
    description = models.TextField()
    search_index = VectorField()

    objects = SearchManager(
        fields=('name', 'description'),
        search_field = 'search_index',
        config = 'names',
    )

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Person, self).save(*args, **kwargs)
        self.update_search_field()


class Person2(models.Model):
    name = models.CharField(max_length=32)
    description = models.TextField()
    search_index = VectorField()

    objects = SearchManager(
        fields=(('name', 'A'), ('description', 'B')),
        search_field = 'search_index',
        config = 'names',
    )

    def __unicode__(self):
        return self.name


class Person3(models.Model):
    name = models.CharField(max_length=32)
    description = models.TextField()
    search_index = VectorField()

    objects = SearchManager(
        fields=('name', 'description'),
        search_field = 'search_index',
        auto_update_search_field = True,
        config = 'names'
    )

    def __unicode__(self):
        return self.name


class Person4(models.Model):
    INDEXED_KEY = 'indexed_key'

    name = models.CharField(max_length=32)
    description = models.TextField()
    data = models.TextField(default='{}')

    search_index = VectorField()
    data_search_index = VectorField()

    objects = SearchManager(
        fields=('name', 'description'),
        search_field = 'search_index',
        auto_update_search_field = True,
        config = 'names'
    )

    def __unicode__(self):
        return self.name

    def update_search_field(self, **kwargs):
        self._fts_manager.update_search_field(**kwargs)
        self._fts_manager.update_search_field(
            search_field='data_search_index',
            fields=('data',),
            config='names',
            extra={
                'key': self.INDEXED_KEY,
            }
        )

    @staticmethod
    def _convert_field_to_db(field, weight, config, using, extra=None):
        if field.name != 'data':
            # Use the default converter
            return

        connection = connections[using]
        qn = connection.ops.quote_name

        return """setweight(
            to_tsvector('%s', coalesce(to_json(%s.%s::json) ->> '%s', '')), '%s')
        """ % (config, qn(field.model._meta.db_table), qn(field.column), extra['key'], weight)


class Person5(models.Model):
    name = models.CharField(max_length=32)
    description = models.TextField()
    search_index = VectorField()

    objects = SearchManager(
        fields=tuple(),
        search_field = 'search_index',
        config = 'names',
        auto_update_search_field=True,
    )

    def __unicode__(self):
        return self.name


class Book(models.Model):
    author = models.ForeignKey(Person)
    name = models.CharField(max_length=32)
    search_index = VectorField()

    objects = SearchManager(
        fields=('name',),
        search_field = 'search_index',
        auto_update_search_field = True,
        config = 'names'
    )

    def __unicode__(self):
        return self.name
