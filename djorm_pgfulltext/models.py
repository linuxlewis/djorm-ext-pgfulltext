# -*- coding: utf-8 -*-

from itertools import repeat

from django.utils.encoding import force_unicode
from django.db import models, connections, transaction

def auto_update_search_field_handler(sender, instance, *args, **kwargs):
    instance.update_search_field()


class SearchManagerMixIn(object):
    """
    A mixin to create a Manager with a 'search' method that may do a full text search
    on the model.

    The manager is set up with a list of one or more model's fields that will be searched.
    It can be a list of field names, or a list of tuples (field_name, weight). It can also
    be None, in that case every CharField and TextField in the model will be searched.

    You can also give a 'search_field', a VectorField into where the values of the searched
    fields are copied and normalized. If you give it, the searches will be made on this
    field; if not, they will be made directly in the searched fields.

    When using search_field, if auto_update = True, Django signals will be used to
    automatically syncronize the search_field with the searched fields every time instances
    are saved. If not, you can call to 'update_search_field' method in model instances to do this.
    If search_field not used, both auto_update and update_search_field does nothing. Alternatively,
    you can create a postgresql trigger to do the syncronization at database level, see this:

    http://www.postgresql.org/docs/9.1/interactive/textsearch-features.html#TEXTSEARCH-UPDATE-TRIGGERS

    In both cases, you should create a text search index, on either the searched fields or
    the compound search_field, like explained here:

    http://www.postgresql.org/docs/9.1/interactive/textsearch-tables.html#TEXTSEARCH-TABLES-INDEX

    Finally, you can give a 'config', the Postgres text search configuration that will be used
    to normalize the search_field and the queries. How do you can create a configuration:

    http://www.postgresql.org/docs/9.1/interactive/textsearch-configuration.html

    To do all those actions in database, create a setup sql script for Django:

    https://docs.djangoproject.com/en/1.4/howto/initial-data/#providing-initial-sql-data
    """

    def __init__(self, fields=None, search_field='search_index',
            config='pg_catalog.english', auto_update_search_field=False):
        self.search_field = search_field
        self.default_weight = 'D'
        self.config = config
        self.auto_update_search_field = auto_update_search_field
        self._fields = fields

        super(SearchManagerMixIn, self).__init__()

    def contribute_to_class(self, cls, name):
        '''
        Called automatically by Django when setting up the model class.
        '''

        # Attach this manager as _fts_manager in the model class.
        if not getattr(cls, '_fts_manager', None):
            cls._fts_manager = self

        # Add 'update_search_field' instance method, that calls manager's update_search_field.
        if not getattr(cls, 'update_search_field', None):
            _update_search_field = lambda x: x._fts_manager.update_search_field(pk=x.pk)
            setattr(cls, 'update_search_field', _update_search_field)

        if self.auto_update_search_field:
            models.signals.post_save.connect(auto_update_search_field_handler, sender=cls)

        super(SearchManagerMixIn, self).contribute_to_class(cls, name)


    def search(self, query, rank_field=None, rank_function='ts_rank', config=None,
                rank_normalization=32, raw=False, using=None, fields=None):
        '''
        Convert query with to_tsquery or plainto_tsquery, depending on raw is
        `True` or `False`, and return a QuerySet with the filter.

        If `rank_field` is not `None`, a field with this name will be added containing the
        search rank of the instances, and the queryset will be ordered by it. The
        rank_function and normalization are explained here:

        http://www.postgresql.org/docs/9.1/interactive/textsearch-controls.html#TEXTSEARCH-RANKING

        If an empty query is given, no filter is made so the QuerySet will return
        all model instances.

        If `fields` is not `None`, the filter is made  with this fields istead of
        defined on a constructor of manager.
        '''

        if not config:
            config = self.config

        db_alias = using if using is not None else self.db
        connection = connections[db_alias]
        qn = connection.ops.quote_name

        qs = self.all()
        if using is not None:
            qs = qs.using(using)

        if query:
            function = "to_tsquery" if raw else "plainto_tsquery"
            ts_query = "%s('%s', '%s')" % (
                function,
                config,
                force_unicode(query).replace("'","''")
            )

            # if fields is passed, obtain a vector expression with
            # these fields. In other case, intent use of search_field if
            # exists.
            if fields:
                search_vector = self._get_search_vector(config, using, fields=fields)
            else:
                if not self.search_field:
                    raise ValueError("search_field is not specified")

                search_vector = "%s.%s" % (
                    qn(self.model._meta.db_table),
                    qn(self.search_field)
                )

            where = " (%s) @@ (%s)" % (search_vector, ts_query)
            select_dict, order = {}, []

            if rank_field:
                select_dict[rank_field] = '%s(%s, %s, %d)' % (
                    rank_function,
                    qn(self.search_field),
                    ts_query,
                    rank_normalization
                )
                order = ['-%s' % (rank_field,)]

            qs = qs.extra(select=select_dict, where=[where], order_by=order)

        return qs

    def update_search_field(self, pk=None, config=None, using=None):
        '''
        Update the search_field of one instance, or a list of instances, or
        all instances in the table (pk is one key, a list of keys or none).

        If there is no search_field, this function does nothing.
        '''

        if not self.search_field:
            return

        if not config:
            config = self.config

        if using is None:
            using = self.db

        connection = connections[using]
        qn = connection.ops.quote_name

        where_sql = ''
        params = []
        if pk is not None:
            if isinstance(pk, (list, tuple)):
                params = pk
            else:
                params = [pk]

            where_sql = "WHERE %s IN (%s)" % (
                qn(self.model._meta.pk.column),
                ','.join(repeat("%s", len(params)))
            )

        search_vector = self._get_search_vector(config, using)
        sql = "UPDATE %s SET %s = %s %s;" % (
            qn(self.model._meta.db_table),
            qn(self.search_field),
            search_vector,
            where_sql
        )

        if not transaction.is_managed(using=using):
            transaction.enter_transaction_management(using=using)
            forced_managed = True
        else:
            forced_managed = False

        cursor = connection.cursor()
        cursor.execute(sql, params)

        try:
            if forced_managed:
                transaction.commit(using=using)
            else:
                transaction.commit_unless_managed(using=using)
        finally:
            if forced_managed:
                transaction.leave_transaction_management(using=using)

    def _find_text_fields(self):
        fields = [f for f in self.model._meta.fields
                  if isinstance(f, (models.CharField, models.TextField))]

        return [(f.name, None) for f in fields]

    def _parse_fields(self, fields):
        """
        Parse fields list into a correct format needed by this manager.
        If any field does not exist, raise ValueError.
        """

        parsed_fields = set()

        if fields is not None and isinstance(fields, (list, tuple)):
            if len(fields) > 0 and isinstance(fields[0], (list,tuple)):
                parsed_fields.update(fields)
            else:
                parsed_fields.update([(x, None) for x in fields])

            # Does not support field.attname.
            field_names = set((field.name, None) for field in self.model._meta.fields if not field.primary_key)
            non_model_fields = parsed_fields.difference(field_names)
            if non_model_fields:
                raise ValueError("The following fields do not exist in this"
                                 " model: {0}".format(", ".join(x[0] for x in non_model_fields)))
        else:
            parsed_fields.update(self._find_text_fields())

        return parsed_fields

    def _get_search_vector(self, config, using, fields=None):
        if fields is None:
            vector_fields = self._parse_fields(self._fields)
        else:
            vector_fields = self._parse_fields(fields)

        search_vector = []
        for field_name, weight in vector_fields:
            search_vector.append(self._get_vector_for_field(field_name, weight, config, using))
        return ' || '.join(search_vector)

    def _get_vector_for_field(self, field_name, weight=None, config=None, using=None):
        if not weight:
            weight = self.default_weight

        if not config:
            config = self.config

        if using is None:
            using = self.db

        field = self.model._meta.get_field(field_name)

        connection = connections[using]
        qn = connection.ops.quote_name

        return "setweight(to_tsvector('%s', coalesce(%s.%s, '')), '%s')" % \
                    (config, qn(self.model._meta.db_table), qn(field.column), weight)


class SearchManager(SearchManagerMixIn, models.Manager):
    pass
