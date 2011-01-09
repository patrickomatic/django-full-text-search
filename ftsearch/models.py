"""

Django Full-text search

Author: Patrick Carroll <patrick@patrickomatic.com>
Version: 0.1

"""
from django.db import models


class Word(models.Model):
	word = models.CharField(max_length=255, db_index=True)
	namespace = models.CharField(max_length=255, db_index=True)

	def __unicode__(self):
		return "%s: %s" % (self.namespace, self.word)


	class Meta:
		unique_together = ('word', 'namespace')


class WordLocation(models.Model):
	word = models.ForeignKey('Word', db_index=True)
	location = models.PositiveIntegerField()
	document_id = models.PositiveIntegerField(db_index=True)

	def __unicode__(self):
		return "%s[%d] (%d)" % (self.word, self.location, self.document_id)
