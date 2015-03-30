# -*- encoding: utf-8 -*-

from django.contrib.gis.db.models import GeoManager
from .models import SearchManagerMixIn


class GisSearchManager(SearchManagerMixIn, GeoManager):
    pass
