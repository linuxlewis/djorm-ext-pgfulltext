# -*- coding: utf-8 -*-

import django
from django.db import models

class VectorField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['default'] = ''
        kwargs['editable'] = False
        kwargs['serialize'] = False
        kwargs['db_index'] = True
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, *args, **kwargs):
        return 'tsvector'

    #def get_prep_lookup(self, lookup_type, value):
    #    if hasattr(value, 'prepare'):
    #        return value.prepare()
    #    if hasattr(value, '_prepare'):
    #        return value._prepare()
    #    raise TypeError("Field has invalid lookup: %s" % lookup_type)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        return self.get_prep_lookup(lookup_type, value)

    def get_prep_value(self, value):
        return value

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[], patterns=['djorm_pgfulltext\.fields\.VectorField'])
except ImportError:
    pass


if django.VERSION[:2] >= (1,7):
    # Create custom lookups for Django>= 1.7

    from django.db.models import Lookup

    class TextSearchDictionary(object):
        def __init__(self, name):
            self.name = name

    class FullTextLookupBase(Lookup):
        def quotes(self, wordlist):
            return [u"'%s'" % x for x in wordlist]
        transform = 'quotes'

        def startswith(self, wordlist):
            return [x + u":*" for x in self.quotes(wordlist)]

        def negative(self, wordlist):
            return [u'!' + x for x in self.startswith(wordlist)]

        def as_sql(self, qn, connection):
            lhs, lhs_params = qn.compile(self.lhs)
            rhs, rhs_params = self.process_rhs(qn, connection)

            print "X" * 90
            print rhs_params

            if type(rhs_params) in [str, unicode]:
                rhs_params = [rhs_params]

            transform = getattr(self, self.transform)

            if type(rhs_params[0]) == TextSearchDictionary:
                ts = rhs_params.pop(0)
                ts_name = ts.name
                cmd = '%s @@ to_tsquery(%%s, %%s)' % lhs

                rest = (ts_name, u" & ".join(transform(rhs_params)))
            else:
                cmd = '%s @@ to_tsquery(%%s)' % lhs
                rest = (u" & ".join(transform(rhs_params)),)

            print cmd, rest

            return cmd, rest

    class FullTextLookup(FullTextLookupBase):
        """This lookup scans for exact matches in the full text index.

        You can use this object like:

            Model.objects.filter(search_field__ft='Foobar')

        will produce:

            ts_query('Foobar')

        and:

            Model.objects.filter(search_field__ft=['Foobar', 'Baz', 'Quux'])

        will produce:

            ts_query('Foobar & Baz & Quux')

        and this form:

            Model.objects.filter(
                search_field__ft=[TextSearchDictionary('french'),
                    'Le Foobar', 'Le Baz'])

        will produce SQL lookup that looks like:

            ts_query('french', '''Le Foobar'' & ''Le Baz''')

        """
        lookup_name = 'ft'

    class FullTextLookupStartsWith(FullTextLookupBase):
        """This lookup scans for full text index entries that BEGIN with
        a given phrase, like:

            Model.objects.filter(search_field__ft=['Foobar', 'Baz', 'Quux'])

        will get translated to

            ts_query('Foobar:* & Baz:* & Quux:*')
        """
        lookup_name = 'fts'
        transform = 'startswith'

    class FulTextLookupNotStartsWith(FullTextLookupBase):
        """This lookup scans for full text index entries that do not begin with
        a given phrase, like:

            Model.objects.filter(search_field__ft=['Foobar', 'Baz', 'Quux'])

        will get translated to

            ts_query('!Foobar:* & !Baz:* & !Quux:*')
        """
        lookup_name = 'ftns'
        transform = 'negative'

    VectorField.register_lookup(FullTextLookup)
    VectorField.register_lookup(FullTextLookupStartsWith)
    VectorField.register_lookup(FulTextLookupNotStartsWith)
