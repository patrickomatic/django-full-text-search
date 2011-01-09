#!/usr/bin/env python

from distutils.core import setup

setup(
		name="django-full-text-search",
		version="0.1",
		description="A simple database-agnostic full text search for Django",
		author="Patrick Carroll",
		author_email="patrick@patrickomatic.com",
		url="http://github.com/patrickomatic/django-full-text-search",
		packages=['ftsearch'],
)

