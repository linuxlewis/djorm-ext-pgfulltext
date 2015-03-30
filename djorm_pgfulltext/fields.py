# -*- coding: utf-8 -*-

# Python3 string compadability
try:
    basestring
except NameError:
    basestring = str

import django
from django.db import models
from psycopg2.extensions import adapt


class VectorField(models.Field):

    def __init__(self, *args, **kwargs):
        kwargs['default'] = ''
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(VectorField, self).deconstruct()
        del kwargs['default']
        del kwargs['editable']
        del kwargs['serialize']
        return name, path, args, kwargs

    def db_type(self, *args, **kwargs):
        return 'tsvector'

    # def get_prep_lookup(self, lookup_type, value):
    #     if hasattr(value, 'prepare'):
    #         return value.prepare()
    #     if hasattr(value, '_prepare'):
    #         return value._prepare()
    #     raise TypeError("Field has invalid lookup: %s" % lookup_type)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        return self.get_prep_lookup(lookup_type, value)

    def get_prep_value(self, value):
        return value

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[], patterns=['djorm_pgfulltext\.fields\.VectorField'])
except ImportError:
    pass


if django.VERSION[:2] >= (1, 7):
    # Create custom lookups for Django>= 1.7

    from django.db.models import Lookup

    def quotes(wordlist):
        return ["%s" % adapt(x.replace("\\", "")) for x in wordlist]

    def startswith(wordlist):
        return [x + ":*" for x in quotes(wordlist)]

    def negative(wordlist):
        return ['!' + x for x in startswith(wordlist)]

    class TSConfig(object):
        def __init__(self, name):
            self.name = name

    class FullTextLookupBase(Lookup):

        def as_sql(self, qn, connection):
            lhs, lhs_params = qn.compile(self.lhs)
            rhs, rhs_params = self.process_rhs(qn, connection)

            if isinstance(rhs_params, basestring):
                rhs_params = [rhs_params]

            if type(rhs_params[0]) == TSConfig:
                ts = rhs_params.pop(0)
                ts_name = ts.name
                cmd = '%s @@ to_tsquery(%%s::regconfig, %%s)' % lhs

                rest = (ts_name, " & ".join(self.transform.__call__(rhs_params)))
            else:
                cmd = '%s @@ to_tsquery(%%s)' % lhs
                rest = (" & ".join(self.transform.__call__(rhs_params)),)

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

        def transform(self, *args):
            return quotes(*args)

    class FullTextLookupStartsWith(FullTextLookupBase):
        """This lookup scans for full text index entries that BEGIN with
        a given phrase, like:

            Model.objects.filter(search_field__ft=['Foobar', 'Baz', 'Quux'])

        will get translated to

            ts_query('Foobar:* & Baz:* & Quux:*')
        """
        lookup_name = 'ft_startswith'

        def transform(self, *args):
            return startswith(*args)

    class FulTextLookupNotStartsWith(FullTextLookupBase):
        """This lookup scans for full text index entries that do not begin with
        a given phrase, like:

            Model.objects.filter(search_field__ft=['Foobar', 'Baz', 'Quux'])

        will get translated to

            ts_query('!Foobar:* & !Baz:* & !Quux:*')
        """
        lookup_name = 'ft_not_startswith'

        def transform(self, *args):
            return negative(*args)

    VectorField.register_lookup(FullTextLookup)
    VectorField.register_lookup(FullTextLookupStartsWith)
    VectorField.register_lookup(FulTextLookupNotStartsWith)
