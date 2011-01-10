.. image:: http://pledgie.com/campaigns/14385.png?skin_name=chrome
    :alt: A simple database-agnostic full text search for Django
    :target: http://www.pledgie.com/campaigns/14385

django-full-text-search
=======================

django-full-text-search provides a simple, database-agnostic full text search
for Django models.  By extending Django's model manager functionality, 
searching and indexing of documents can be added to any Django model.  
django-full-text-search also provides pluggable stemming implementations and
includes (and defaults to) an implementation of the `Porter stemming algorithm`_.


Overview
--------

Once installed, searching documents is as easy as:

1. Registering a manager for the model you would like to make searchable: ::

  from ftsearch.managers import SearchableManager

  class MyModel(models.Model):
     ...
     objects = SearchableManager()


2. Define a ``get_text_only()`` method on the model.  This method should return
a single string containing all text to be searched: ::

  class MyModel(models.Model):
     name = models.CharField()
     body = models.CharField()
     ...
     objects = SearchableManager()
 
     def get_text_only(self):
        return ' '.join(self.name, self.body)


3. Index the documents when they are created or modified by using the manager
methods.  This only needs to be done once: ::

   MyModel.objects.add_to_index(my_model_instance)

4. Now search the indexed documents: ::

   MyModel.objects.search('my search terms')


Installation
------------

1. Download_ and install django-full-text-search using Distutils_:

  ``$ sudo python setup.py install``

2. Add the ``ftsearch`` app to ``INSTALLED_APPS`` in your ``settings.py``


Configuration
-------------

By default django-full-text-search comes with pretty reasonable defaults and
doesn't require any additional configuration.  However, if you would like to
override some defaults, you can use the following configuration options:

* ``SEARCH_WEIGHTS`` - A list of 2-value tuples which specify the weights to 
  be used w hen ranking results.  if you would like to add application-specific
  weighting rules, you can do so by overriding ``SEARCH_WEIGHTS``.  By default
  it is defined as: ::

 	settings.SEARCH_WEIGHTS = (
			(1.0, ftsearch.weights.frequency_score),
			(1.0, ftsearch.weights.location_score),
			(1.0, ftsearch.wieghts.distance_score),
	)
 
* ``SEARCH_STEMMER`` - A custom stemming implementation.  It must be a class
  which has a ``stem()`` method.

* ``SEARCH_WORD_SPLIT_REGEX`` - The regex that is used to split text.  By 
  default it is ``re.compile(r'\W*')``.


Limitations
-----------

django-full-text-search is mostly suitable for small datasets.  If you need
to index and search millions of documents, it may not be for you.  


.. _Porter stemming algorithm: http://tartarus.org/~martin/PorterStemmer/
.. _Download: http://github.com/parickomatic/django-full-text-search/downloads
.. _Distutils: http://docs.python.org/distutils/
