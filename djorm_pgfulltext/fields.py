# -*- coding: utf-8 -*-

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
