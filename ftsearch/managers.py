from django.conf import settings
from django.db import models, connection

from ftsearch.models import Word, WordLocation


IGNORE_WORDS = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])


class SearchableManager(models.Manager):
	def is_indexed(self, model):
		return WordLocation.objects.filter(document_id=model.id, word__namespace=self.model.db_table).exists()


	def add_to_index(self, model):
		if self.is_indexed(model):
			self.remove_from_index(model)

		try:
			text = model.get_text_only()
		except AttributeError:
			raise NotImplementedError(unicode(model) + " must implement get_text_only()")

		p = settings.SEARCH_STEMMER()
		stemmed_text = [p.stem(s.lower()) for s in self.__separate_words(text) if s != '']

		for i in range(len(stemmed_text)):
			word = stemmed_text[i]
			if word in IGNORE_WORDS: continue
			
			try:
				word = Word.objects.get(word=word, namespace=self.model.db_table)
			except Word.DoesNotExist:
				word = Word(word=word, namespace=self.model.db_table)
				word.save()

			word_location = WordLocation(document_id=model.id, word=word, location=i)
			word_location.save()


	def remove_from_index(self, model):
		WordLocation.objects.filter(document_id=model.id, word__namespace=self.model.db_table).delete()


	def __get_match_rows(self, query):
		field_list = 'w0.document_id'
		table_list = ''
		clause_list = ''
		word_ids = []

		table_number = 0

		for word in query:
			if word in IGNORE_WORDS: continue
			word_id = None

			try:
				word_id = Word.objects.get(word=word, namespace=self.model.db_table).id
			except Word.DoesNotExist:
				continue	

			word_ids.append(word_id)

			if table_number > 0:
				table_list += ', '
				clause_list += ' and w%d.document_id = w%d.document_id and ' \
							   % (table_number - 1, table_number)

			field_list += ',w%d.location' % table_number
			table_list += 'ftsearch_wordlocation w%d' % table_number
			clause_list += 'w%d.word_id=%d' % (table_number, word_id)

			table_number += 1

		if not table_list or not clause_list:
			return [], []	

		cur = connection.cursor()
		cur.execute('select %s from %s where %s' \
				% (field_list, table_list, clause_list))

		rows = cur.fetchall()

		return [row for row in rows], word_ids


	def __separate_words(self, words):
		return settings.SEARCH_WORD_SPLIT_REGEX.split(words)


	def search(self, query):
		if isinstance(query, str):
			# split the string into a list of search terms
			query = self.__separate_words(query)
		elif not isinstance(query, list):
			raise TypeError("search must be called with a string or a list")

		p = settings.SEARCH_STEMMER()
		# lowercase and stem each word
		stemmed_query = [p.stem(s.lower()) for s in query if s != '']

		# get a row from the db for each matching word
		rows, word_ids = self.__get_match_rows(stemmed_query)

		# apply the weights to each row
		weights = [(w, weight_fn(rows)) for w, weight_fn in settings.SEARCH_WEIGHTS]

		# calculate total scores for each documents by applying weights
		total_scores = dict([(row[0], 0) for row in rows])
		for (weight, scores) in weights:
			for document in total_scores:
				total_scores[document] += weight * scores[document]

		# sort by the calculated weights and return
		return sorted([(doc, score) for (score, doc) in total_scores.iteritems()], reverse=1)
