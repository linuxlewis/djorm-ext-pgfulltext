====================
djorm-ext-pgfulltext
====================

Pgfulltext module of django orm extensions package (collection of third party plugins build in one unified package).

- Now compatible with python2 and python3 with same code base.
- Ready for django 1.3, 1.4, 1.5 and 1.6


Introduction
------------

Full Text Searching (or just text search) provides the capability to identify natural-language documents that satisfy a query, and optionally to sort them by relevance to the query. The most common type of search is to find all documents containing given query terms and return them in order of their similarity to the query. Notions of query and similarity are very flexible and depend on the specific application. The simplest search considers query as a set of words and similarity as the frequency of query words in the document. (`From postgresql documentation.`)


Classes
^^^^^^^

`djorm_pgfulltext.fields.VectorField`
    An tsvector index field which stores converted text into special format.

`djorm_pgfulltext.models.SearchManager`
    Django manager that contains helper methods for search and re/genereate indexes.


How to use it
-------------

To use it, you will need to add a new field. Obviously, this is not mandatory, as it can specify which fields you want to search at the time of calling the `search`. Keep in mind that you should put the corresponding indices for the fields to be used.

.. code-block:: python

    from djorm_pgfulltext.models import SearchManager
    from djorm_pgfulltext.fields import VectorField
    from django.db import models

    class Page(models.Model):
        name = models.CharField(max_length=200)
        description = models.TextField()

        search_index = VectorField()

        objects = SearchManager(
            fields = ('name', 'description'),
            config = 'pg_catalog.english', # this is default
            search_field = 'search_index', # this is default
            auto_update_search_field = True
        )


The manager automatically injected ``update_search_field`` method to the model instance.
Also, not to override the save method, you can pass the parameter ``auto_update_search_field = True``, so
the index field  is updated automatically by calling the ``save`` method.


Usage examples:
^^^^^^^^^^^^^^^

- The config parameter is optional and defaults to 'pg_catalog.english'.
- The fields parameter is optional. If a list of tuples, you can specify the ranking of each field, if it is None, it gets 'D' as the default.
- It can also be a simple list of fields, and the ranking will be selected by default. If the field is empty, the index was applied to all fields ``CharField`` and ``TextField``.

To search, use the ``search`` method of the manager. The current implementation, by default uses unaccent extension for ignore the accents. Also, the searches are case insensitive.

.. code-block:: python

    >>> Page.objects.search("documentation & about")
    [<Page: Page: Home page>]
    >>> Page.objects.search("about | documentation | django | home", raw=True)
    [<Page: Page: Home page>, <Page: Page: About>, <Page: Page: Navigation>]

FTS extension by default uses plainto_tsquery instead of to_tosquery, for this reason the use of raw parameter.


Update search field:
^^^^^^^^^^^^^^^^^^^^

For manual updating all search fields use management command ``update_search_field``:

.. code-block:: python

    ./manage.py update_search_field [options] appname [model]


General notes:
^^^^^^^^^^^^^^

You must ensure you have installed the extension `unaccent`:

.. code-block:: sql

    CREATE EXTENSION unaccent;
    ALTER FUNCTION unaccent(text) IMMUTABLE;

You can install this extension on template1 database for make this extension automatically available for all new created databases.

Contributing
------------

The first step of contributing is being able to run the unit tests. We provide a seet of ``docker`` containers and a ``docker-compose`` file to help you achieve this task.

Running the tests
^^^^^^^^^^^^^^^^^

The only command you need to run the tests is:

.. code-block:: bash

  docker-compose run --rm djorm python3 testing/runtests.py

Changelog
---------

**0.9.2**

- Django 1.7 lookups support.

**0.9**

- Fix django 1.6 compatibility (transaction management).


.. image:: https://d2weczhvl823v0.cloudfront.net/djangonauts/djorm-ext-pgfulltext/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free
