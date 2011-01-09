"""

Django Full-text search

Author: Patrick Carroll <patrick@patrickomatic.com>
Version: 0.1

"""
from django.test import TestCase

from ftsearch.models import *


class SearchEngineTest(TestCase):
	def test_physical_distance(self):
		self.assert_(physical_distance((0, 0), (0, 2)) == 2)
		self.assert_(physical_distance((0, 0), (2, 0)) == 2)


class IndexerTest(TestCase):
	fixtures = ['search']

	def setUp(self):
		self.indexer = Indexer()
		self.lorem_ipsum_doc = {
			'name': 'Lorem ipsum',
			'body': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla a purus a libero pellentesque feugiat. Ut nulla ligula, ornare at lacinia eget, accumsan sit amet nisl. Aliquam erat volutpat. Quisque volutpat varius risus, ut facilisis diam posuere placerat. Duis ipsum lacus, hendrerit a cursus a, dapibus eget turpis. Aliquam iaculis, massa in molestie convallis, mauris odio gravida mi, non tincidunt neque diam non augue. Nulla facilisi. Sed varius mi quis nunc interdum pulvinar. Cras ut elit at tortor viverra aliquet. Proin ultrices luctus ipsum, eu porttitor risus dapibus ac. Nulla facilisi. Sed sem ligula, convallis et tempus in, placerat et velit. Morbi ipsum lectus, rhoncus malesuada rutrum sit amet, lacinia non risus. Pellentesque commodo velit in lorem lacinia tincidunt. Suspendisse hendrerit lorem quis est consequat non congue justo convallis. Donec lobortis, nibh lacinia molestie commodo, mauris nunc accumsan augue, ut malesuada metus risus quis enim. Proin metus lorem, scelerisque at porttitor eget, eleifend vulputate diam.',
			'average_rating': 3.0,
		}

		self.test_doc = {
			'name': 'This is a test',
			'body': 'I am testing things by making this document that is a test',
			'average_rating': 3.0,
		}


	def test_add_to_index(self):
		self.indexer.add_to_index(self.lorem_ipsum_doc)
		self.indexer.add_to_index(self.test_doc)

		word = Word.objects.get(word='test')
		location = WordLocation.objects.filter(document_id=str(self.test_doc['_id']), word=word)[0]
		self.assert_(location.location == 3)

		word = Word.objects.get(word='thi')
		locations = WordLocation.objects.filter(document_id=str(self.test_doc['_id']), word=word)
		self.assert_(locations[0].location == 0)
		self.assert_(locations[1].location == 10)


	def test_get_text_only(self):
		# XXX
		pass


	def test_separate_words(self):
		self.assert_(self.indexer.separate_words('FOO poo moo') == ['foo', 'poo', 'moo'])
		self.assert_(self.indexer.separate_words('12-30 f. 1/34@!02$#*') == ['12', '30', 'f', '1', '34', '02'])


	def test_is_indexed(self):
		w = Word(word='word')
		w.save()

		word = WordLocation(document_id='foo', word=w, location=1)
		word.save()

		self.assert_(self.indexer.is_indexed({'_id': 'foo'}))


	def test_is_indexed__not_indexed(self):
		self.assert_(not self.indexer.is_indexed({'_id': 'foo'}))


class SearcherTest(TestCase):
#	fixtures = ['search']

	def setUp(self):
		self.searcher = Searcher()
		self.lorem_ipsum_doc = {
			'name': 'Lorem ipsum',
			'slug_id': 'lorem-ipsum',
			'body': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla a purus a libero pellentesque feugiat. Ut nulla ligula, ornare at lacinia eget, accumsan sit amet nisl. Aliquam erat volutpat. Quisque volutpat varius risus, ut facilisis diam posuere placerat. Duis ipsum lacus, hendrerit a cursus a, dapibus eget turpis. Aliquam iaculis, massa in molestie convallis, mauris odio gravida mi, non tincidunt neque diam non augue. Nulla facilisi. Sed varius mi quis nunc interdum pulvinar. Cras ut elit at tortor viverra aliquet. Proin ultrices luctus ipsum, eu porttitor risus dapibus ac. Nulla facilisi. Sed sem ligula, convallis et tempus in, placerat et velit. Morbi ipsum lectus, rhoncus malesuada rutrum sit amet, lacinia non risus. Pellentesque commodo velit in lorem lacinia tincidunt. Suspendisse hendrerit lorem quis est consequat non congue justo convallis. Donec lobortis, nibh lacinia molestie commodo, mauris nunc accumsan augue, ut malesuada metus risus quis enim. Proin metus lorem, scelerisque at porttitor eget, eleifend vulputate diam.',
			'average_rating': 3.0,
			'location': {
				'latitude': -1.0,
				'longitude': 23.0,
			},
		}

		self.test_doc = {
			'slug_id': 'this-is-a-test',
			'name': 'This is a test',
			'body': 'I am testing things by making this document that is a test',
			'average_rating': 3.0,
			'location': {
				'latitude': -1.0,
				'longitude': 23.0,
			},
		}

		self.indexer = Indexer()
		self.indexer.add_to_index(self.lorem_ipsum_doc)
		self.indexer.add_to_index(self.test_doc)
		self.test_doc_id = str(self.test_doc['_id'])
		self.rows = [(self.test_doc_id, 3, 7), (self.test_doc_id, 15, 7)]
	
	def tearDown(self):
		pass

	def test_normalize_scores(self):
		ret = self.searcher.normalize_scores({'zero': 0, 'quarter': 25, 'half': 50, 'whole': 100})
# XXX these have to all be approximate
#		self.assert_(ret['zero'] == 0.0)
#		self.assert_(ret['quarter'] == 0.25)
#		self.assert_(ret['half'] == 0.5)
#		self.assert_(ret['whole'] == 1.0)

		ret = self.searcher.normalize_scores({'zero': 1})
#		self.assert_(ret['zero'] == 1.0)

		ret = self.searcher.normalize_scores({'zero': 25, 'quarter': 50, 'half': 100, 'whole': 125})
#		self.assert_(ret['zero'] == 0.0)
#		self.assert_(ret['quarter'] == 0.25)
#		self.assert_(ret['half'] == 0.75)
#		self.assert_(ret['whole'] == 1.0)

	def test_normalize_scores__empty(self):
		ret = self.searcher.normalize_scores({})
		self.assert_(ret == {})

	def test_normalize_scores__small_is_better(self):
		ret = self.searcher.normalize_scores({'zero': 0, 'quarter': 25, 'half': 50, 'whole': 100}, True)
#		self.assert_(ret['zero'] == 1.0)
#		self.assert_(ret['quarter'] == 0.75)
#		self.assert_(ret['half'] == 0.5)
#		self.assert_(ret['whole'] == 0.0)

		ret = self.searcher.normalize_scores({'zero': 10}, True)
#		self.assert_(ret['zero'] == 1.0)


	# XXX better tests, multiple results
	def test_frequency_score(self):
		res = self.searcher.frequency_score(self.rows)
		self.assert_(res == {self.test_doc_id: 1.0})

	def test_frequency_score__empty(self):
		res = self.searcher.frequency_score([])
		self.assert_(res == {})


	def test_location_score(self):
		res = self.searcher.location_score(self.rows)
		self.assert_(res == {self.test_doc_id: 1.0})

	def test_location_score__empty(self):
		res = self.searcher.location_score([])
		self.assert_(res == {})


	def test_distance_score(self):
		res = self.searcher.distance_score(self.rows)
		self.assert_(res == {self.test_doc_id: 1.0})

	def test_distance_score__empty(self):
		res = self.searcher.distance_score([])
		self.assert_(res == {})

	def test_get_match_rows(self):
		rows, word_ids = self.searcher.get_match_rows('test things')

		self.assert_(rows[0] == (self.test_doc_id, 3, 7))
		self.assert_(rows[1] == (self.test_doc_id, 6, 7))
		self.assert_(rows[2] == (self.test_doc_id, 15, 7))
		self.assert_(word_ids == [89, 92])


	def test_get_scored_list(self):
		# XXX
		pass	

	def test_query(self):
		res = self.searcher.query('test things')
		self.assert_(res == [(7.0, self.test_doc_id)])

		res = self.searcher.query('lorem ipsum')
		self.assert_(res == [(7.0, str(self.lorem_ipsum_doc['_id']))])

	def test_query__not_found(self):
		res = self.searcher.query("aflkjdfsjkldasldfj")
		self.assert_(res == [])


class PorterStemmerTest(TestCase):
	def setUp(self):
		self.stemmer = PorterStemmer()

	def test_stem(self):
		self.assert_(self.stemmer.stem("things") == "thing")
		self.assert_(self.stemmer.stem("pooping") == "poop")
