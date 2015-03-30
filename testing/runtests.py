# -*- coding: utf-8 -*-

import os
import sys

import django
from django.core.management import call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

if django.VERSION[:2] >= (1, 7):
    django.setup()

if __name__ == "__main__":
    args = sys.argv[1:]
    call_command("test", *args, verbosity=2)
