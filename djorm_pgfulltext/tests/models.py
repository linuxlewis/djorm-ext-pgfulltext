# -*- coding: utf-8 -*-
from django.db import models

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
