"""

Django Full-text search

Author: Patrick Carroll <patrick@patrickomatic.com>
Version: 0.1

"""
from django.db import models
from django.test import TestCase

from ftsearch.managers import SearchableManager
from ftsearch.models import Word, WordLocation
from ftsearch.weights import *
from ftsearch.stemming import PorterStemmer


LOREM_IPSUM = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla a purus a libero pellentesque feugiat. Ut nulla ligula, ornare at lacinia eget, accumsan sit amet nisl. Aliquam erat volutpat. Quisque volutpat varius risus, ut facilisis diam posuere placerat. Duis ipsum lacus, hendrerit a cursus a, dapibus eget turpis. Aliquam iaculis, massa in molestie convallis, mauris odio gravida mi, non tincidunt neque diam non augue. Nulla facilisi. Sed varius mi quis nunc interdum pulvinar. Cras ut elit at tortor viverra aliquet. Proin ultrices luctus ipsum, eu porttitor risus dapibus ac. Nulla facilisi. Sed sem ligula, convallis et tempus in, placerat et velit. Morbi ipsum lectus, rhoncus malesuada rutrum sit amet, lacinia non risus. Pellentesque commodo velit in lorem lacinia tincidunt. Suspendisse hendrerit lorem quis est consequat non congue justo convallis. Donec lobortis, nibh lacinia molestie commodo, mauris nunc accumsan augue, ut malesuada metus risus quis enim. Proin metus lorem, scelerisque at porttitor eget, eleifend vulputate diam.'


class TestModel(models.Model):
	name = models.CharField(max_length=50)
	body = models.TextField()
	rating = models.PositiveIntegerField()
	db_table = 'test'

	objects = SearchableManager()

	def get_text_only(self):
		return ' '.join([self.name, self.body])


class WeightsTest(TestCase):
	def setUp(self):
		self.test_doc_id = 1
		self.rows = [(self.test_doc_id, 3, 7), (self.test_doc_id, 15, 7)]

	def test_normalize_scores(self):
		ret = normalize_scores({'zero': 0, 'quarter': 25, 'half': 50, 'whole': 100})
# XXX these have to all be approximate
#		self.assert_(ret['zero'] == 0.0)
#		self.assert_(ret['quarter'] == 0.25)
#		self.assert_(ret['half'] == 0.5)
#		self.assert_(ret['whole'] == 1.0)

		ret = normalize_scores({'zero': 1})
#		self.assert_(ret['zero'] == 1.0)

		ret = normalize_scores({'zero': 25, 'quarter': 50, 'half': 100, 'whole': 125})
#		self.assert_(ret['zero'] == 0.0)
#		self.assert_(ret['quarter'] == 0.25)
#		self.assert_(ret['half'] == 0.75)
#		self.assert_(ret['whole'] == 1.0)

	def test_normalize_scores__empty(self):
		ret = normalize_scores({})
		self.assert_(ret == {})

	def test_normalize_scores__small_is_better(self):
		ret = normalize_scores({'zero': 0, 'quarter': 25, 'half': 50, 'whole': 100}, True)
#		self.assert_(ret['zero'] == 1.0)
#		self.assert_(ret['quarter'] == 0.75)
#		self.assert_(ret['half'] == 0.5)
#		self.assert_(ret['whole'] == 0.0)

		ret = normalize_scores({'zero': 10}, True)
#		self.assert_(ret['zero'] == 1.0)


	# XXX better tests, multiple results
	def test_frequency_score(self):
		res = frequency_score(self.rows)
		self.assert_(res == {self.test_doc_id: 1.0})

	def test_frequency_score__empty(self):
		res = frequency_score([])
		self.assert_(res == {})


	def test_location_score(self):
		res = location_score(self.rows)
		self.assert_(res == {self.test_doc_id: 1.0})

	def test_location_score__empty(self):
		res = location_score([])
		self.assert_(res == {})


	def test_distance_score(self):
		res = distance_score(self.rows)
		self.assert_(res == {self.test_doc_id: 1.0})

	def test_distance_score__empty(self):
		res = distance_score([])
		self.assert_(res == {})


	def test_physical_distance(self):
		self.assert_(physical_distance((0, 0), (0, 2)) == 2)
		self.assert_(physical_distance((0, 0), (2, 0)) == 2)


	def test_physical_distance_score(self):
		# XXX
		pass


class SearchableManagerTest(TestCase):
	def setUp(self):
		self.lorem_ipsum_doc = TestModel(name='Lorem ipsum', body=LOREM_IPSUM * 5)
		self.lorem_ipsum_doc.id = 1
		self.test_doc = TestModel(name='This is a test', body='I am testing things by making this document that is a test', rating=3)
		self.test_doc.id = self.test_doc_id = 2

		self.manager = TestModel.objects
		self.manager.add_to_index(self.test_doc)


	def test_add_to_index(self):
		self.manager.add_to_index(self.lorem_ipsum_doc)
		self.manager.add_to_index(self.test_doc)

		word = Word.objects.get(word='test')
		location = WordLocation.objects.filter(document_id=self.test_doc.id, word=word)[0]
		self.assert_(location.location == 3)

		word = Word.objects.get(word='thi')
		locations = WordLocation.objects.filter(document_id=self.test_doc.id, word=word)
		self.assert_(locations[0].location == 0)
		self.assert_(locations[1].location == 10)

	def test_add_to_index__get_text_only_not_implemented(self):
		class Foo:
			id = 4

		self.assertRaises(NotImplementedError, self.manager.add_to_index, Foo())


	def test_remove_from_index(self):
		word = Word(word='foo', namespace='test')
		word.save()

		WordLocation(word=word, location=1, document_id=6)

		model = TestModel()
		# XXX


	def test_is_indexed(self):
		model = TestModel()
		model.id = 55

		w = Word(word='word', namespace=model.db_table)
		w.save()

		word = WordLocation(document_id=55, word=w, location=1)
		word.save()

		self.assert_(self.manager.is_indexed(model))

	def test_is_indexed__not_indexed(self):
		model = TestModel()
		model.id = 2020202
		self.assert_(not self.manager.is_indexed(model))


	def test_search(self):
		res = self.manager.search('test things')
		self.assert_(res == [(7.0, self.test_doc_id)])

		res = self.manager.search('lorem ipsum')
		self.assert_(res == [(7.0, str(self.lorem_ipsum_doc['_id']))])

	def test_search__list(self):
		res = self.manager.search(['test', 'things'])
		self.assert_(res == [(7.0, self.test_doc_id)])

	def test_search__not_found(self):
		res = self.manager.search("aflkjdfsjkldasldfj")
		self.assert_(res == [])


class PorterStemmerTest(TestCase):
	def setUp(self):
		self.stemmer = PorterStemmer()

	def test_stem(self):
		self.assert_(self.stemmer.stem("things") == "thing")
		self.assert_(self.stemmer.stem("pooping") == "poop")
