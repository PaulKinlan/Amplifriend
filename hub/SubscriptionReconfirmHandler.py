import datetime
import gc
import hashlib
import hmac
import logging
import os
import random
import sgmllib
import time
import traceback
import urllib
import urlparse
import wsgiref.handlers
import xml.sax

from google.appengine import runtime
from google.appengine.api import datastore_types
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors
from google.appengine.api import users
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.runtime import apiproxy_errors

import decorators
import constants

class SubscriptionReconfirmHandler(webapp.RequestHandler):
	"""Periodic handler causes reconfirmation for almost expired subscriptions."""

	def __init__(self, now=time.time):
		"""Initializer."""
		webapp.RequestHandler.__init__(self)
		self.now = now

	@decorators.work_queue_only
	def get(self, username):
		threshold_timestamp = str(
				int(self.now() - SUBSCRIPTION_CHECK_BUFFER_SECONDS))
		# NOTE: See PollBootstrapHandler as to why we need a named task here for
		# the first insertion and the rest of the sequence.
		name = 'reconfirm-' + threshold_timestamp
		try:
			taskqueue.Task(
					url='/work/reconfirm_subscriptions',
					name=name,
					params=dict(time_offset=threshold_timestamp)
			).add(POLLING_QUEUE)
		except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
			logging.exception('Could not enqueue FIRST reconfirmation task')

	@decorators.work_queue_only
	def post(self, username):
		time_offset = self.request.get('time_offset')
		datetime_offset = datetime.datetime.utcfromtimestamp(int(time_offset))
		key_offset = self.request.get('key_offset')
		logging.info('Handling reconfirmations for time_offset = %s, '
								 'current_key = %s', time_offset, key_offset)

		query = (Subscription.all()
						 .filter('subscription_state =', Subscription.STATE_VERIFIED)
						 .order('__key__'))
		if key_offset:
			query.filter('__key__ >', db.Key(key_offset))

		subscriptions = query.fetch(SUBSCRIPTION_CHECK_CHUNK_SIZE)
		if not subscriptions:
			logging.info('All done with periodic subscription reconfirmations')
			return

		next_key = str(subscriptions[-1].key())
		try:
			taskqueue.Task(
					url='/work/reconfirm_subscriptions',
					name='reconfirm-%s-%s' % (time_offset, sha1_hash(next_key)),
					params=dict(time_offset=time_offset,
											key_offset=next_key)).add(POLLING_QUEUE)
		except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
			logging.exception('Could not enqueue continued reconfirmation task')

		for sub in subscriptions:
			if sub.expiration_time < datetime_offset:
				sub.enqueue_task(Subscription.STATE_VERIFIED)