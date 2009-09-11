#
# This code is from the hub reference model
#

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


import constants
import utils


class HubSubscription(db.Model):
	"""
	Represents a single subscription to a topic for a callback URL.
	"""

	STATE_NOT_VERIFIED = 'not_verified'
	STATE_VERIFIED = 'verified'
	STATE_TO_DELETE = 'to_delete'
	STATES = frozenset([
		STATE_NOT_VERIFIED,
		STATE_VERIFIED,
		STATE_TO_DELETE,
	])

	callback = db.TextProperty(required=True)
	callback_hash = db.StringProperty(required=True)
	topic = db.TextProperty(required=True)
	topic_hash = db.StringProperty(required=True)
	created_time = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	lease_seconds = db.IntegerProperty(default=constants.DEFAULT_LEASE_SECONDS)
	expiration_time = db.DateTimeProperty(required=True)
	eta = db.DateTimeProperty(auto_now_add=True)
	confirm_failures = db.IntegerProperty(default=0)
	verify_token = db.TextProperty()
	secret = db.TextProperty()
	hmac_algorithm = db.TextProperty()
	subscription_state = db.StringProperty(default=STATE_NOT_VERIFIED, choices=STATES)

	@staticmethod
	def create_key_name(callback, topic):
		"""Returns the key name for a Subscription entity.

		Args:
			callback: URL of the callback subscriber.
			topic: URL of the topic being subscribed to.

		Returns:
			String containing the key name for the corresponding Subscription.
		"""
		return utils.get_hash_key_name(u'%s\n%s' % (callback, topic))

	@classmethod
	def insert(cls,
				 callback,
				 topic,
				 verify_token,
				 secret,
				 hash_func='sha1',
				 lease_seconds=constants.DEFAULT_LEASE_SECONDS,
				 now=datetime.datetime.now):
		"""Marks a callback URL as being subscribed to a topic.

		Creates a new subscription if None already exists. Forces any existing,
		pending request (i.e., async) to immediately enter the verified state.

		Args:
			callback: URL that will receive callbacks.
			topic: The topic to subscribe to.
			verify_token: The verification token to use to confirm the
				subscription request.
			secret: Shared secret used for HMACs.
			hash_func: String with the name of the hash function to use for HMACs.
			lease_seconds: Number of seconds the client would like the subscription
				to last before expiring. Must be a number.
			now: Callable that returns the current time as a datetime instance. Used
				for testing

		Returns:
			True if the subscription was newly created, False otherwise.
		"""
		key_name = cls.create_key_name(callback, topic)
		now_time = now()
		def txn():
			sub_is_new = False
			sub = cls.get_by_key_name(key_name)
			if sub is None:
				sub_is_new = True
				sub = cls(key_name=key_name,
									callback=callback,
									callback_hash=utils.sha1_hash(callback),
									topic=topic,
									topic_hash=utils.sha1_hash(topic),
									verify_token=verify_token,
									secret=secret,
									hash_func=hash_func,
									lease_seconds=lease_seconds,
									expiration_time=now_time)
			sub.subscription_state = cls.STATE_VERIFIED
			sub.expiration_time = now_time + datetime.timedelta(seconds=lease_seconds)
			sub.put()
			return sub_is_new
		return db.run_in_transaction(txn)

	@classmethod
	def request_insert(cls,
								callback,
								topic,
								verify_token,
								secret,
								hash_func='sha1',
								lease_seconds=constants.DEFAULT_LEASE_SECONDS,
								now=datetime.datetime.now):
		"""Records that a callback URL needs verification before being subscribed.

		Creates a new subscription request (for asynchronous verification) if None
		already exists. Any existing subscription request will not be modified;
		for instance, if a subscription has already been verified, this method
		will do nothing.

		Args:
			callback: URL that will receive callbacks.
			topic: The topic to subscribe to.
			verify_token: The verification token to use to confirm the
				subscription request.
			secret: Shared secret used for HMACs.
			hash_func: String with the name of the hash function to use for HMACs.
			lease_seconds: Number of seconds the client would like the subscription
				to last before expiring. Must be a number.
			now: Callable that returns the current time as a datetime instance. Used
				for testing

		Returns:
			True if the subscription request was newly created, False otherwise.
		"""
		key_name = cls.create_key_name(callback, topic)
		def txn():
			sub_is_new = False
			sub = cls.get_by_key_name(key_name)
			if sub is None:
				sub_is_new = True
				sub = cls(key_name=key_name,
									callback=callback,
									callback_hash=utils.sha1_hash(callback),
									topic=topic,
									topic_hash=utils.sha1_hash(topic),
									secret=secret,
									hash_func=hash_func,
									verify_token=verify_token,
									lease_seconds=lease_seconds,
									expiration_time=(
											now() + datetime.timedelta(seconds=lease_seconds)))
			sub.put()
			return (sub_is_new, sub)
		new, sub = db.run_in_transaction(txn)
		# Note: This enqueuing must come *after* the transaction is submitted, or
		# else we'll actually run the task *before* the transaction is submitted.
		sub.enqueue_task(cls.STATE_VERIFIED)
		return new

	@classmethod
	def remove(cls, callback, topic):
		"""Causes a callback URL to no longer be subscribed to a topic.

		If the callback was not already subscribed to the topic, this method
		will do nothing. Otherwise, the subscription will immediately be removed.

		Args:
			callback: URL that will receive callbacks.
			topic: The topic to subscribe to.

		Returns:
			True if the subscription had previously existed, False otherwise.
		"""
		key_name = cls.create_key_name(callback, topic)
		def txn():
			sub = cls.get_by_key_name(key_name)
			if sub is not None:
				sub.delete()
				return True
			return False
		return db.run_in_transaction(txn)

	@classmethod
	def request_remove(cls, callback, topic, verify_token):
		"""Records that a callback URL needs to be unsubscribed.

		Creates a new request to unsubscribe a callback URL from a topic (where
		verification should happen asynchronously). If an unsubscribe request
		has already been made, this method will do nothing.

		Args:
			callback: URL that will receive callbacks.
			topic: The topic to subscribe to.
			verify_token: The verification token to use to confirm the
				unsubscription request.

		Returns:
			True if the Subscription to remove actually exists, False otherwise.
		"""
		key_name = cls.create_key_name(callback, topic)
		def txn():
			sub = cls.get_by_key_name(key_name)
			if sub is not None:
				sub.put()
				return (True, sub)
			return (False, sub)
		removed, sub = db.run_in_transaction(txn)
		# Note: This enqueuing must come *after* the transaction is submitted, or
		# else we'll actually run the task *before* the transaction is submitted.
		if sub:
			sub.enqueue_task(cls.STATE_TO_DELETE)
		return removed

	@classmethod
	def has_subscribers(cls, topic):
		"""Check if a topic URL has verified subscribers.

		Args:
			topic: The topic URL to check for subscribers.

		Returns:
			True if it has verified subscribers, False otherwise.
		"""
		if (cls.all().filter('topic_hash =', utils.sha1_hash(topic))
				.filter('subscription_state =', cls.STATE_VERIFIED).get() is not None):
			return True
		else:
			return False

	@classmethod
	def get_subscribers(cls, topic, count, starting_at_callback=None):
		"""Gets the list of subscribers starting at an offset.

		Args:
			topic: The topic URL to retrieve subscribers for.
			count: How many subscribers to retrieve.
			starting_at_callback: A string containing the callback hash to offset
				to when retrieving more subscribers. The callback at the given offset
				*will* be included in the results. If None, then subscribers will
				be retrieved from the beginning.

		Returns:
			List of Subscription objects that were found, or an empty list if none
			were found.
		"""
		query = cls.all()
		query.filter('topic_hash =', utils.sha1_hash(topic))
		query.filter('subscription_state = ', cls.STATE_VERIFIED)
		if starting_at_callback:
			query.filter('callback_hash >=', utils.sha1_hash(starting_at_callback))
		query.order('callback_hash')

		return query.fetch(count)

	def enqueue_task(self, next_state):
		"""Enqueues a task to confirm this Subscription.

		Args:
			next_state: The next state this subscription should be in.
		"""
		# TODO(bslatkin): Remove these retries when they're not needed in userland.
		RETRIES = 3
		target_queue = os.environ.get('X_APPENGINE_QUEUENAME', SUBSCRIPTION_QUEUE)
		for i in xrange(RETRIES):
			try:
				taskqueue.Task(
						url='/work/subscriptions',
						eta=self.eta,
						params={'subscription_key_name': self.key().name(),
										'next_state': next_state}
						).add(target_queue)
			except (taskqueue.Error, apiproxy_errors.Error):
				logging.exception('Could not insert task to confirm '
													'topic = %s, callback = %s',
													self.topic, self.callback)
				if i == (RETRIES - 1):
					raise
			else:
				return

	def confirm_failed(self,
										 next_state,
										 max_failures=constants.MAX_SUBSCRIPTION_CONFIRM_FAILURES,
										 retry_period=constants.SUBSCRIPTION_RETRY_PERIOD,
										 now=datetime.datetime.utcnow):
		"""Reports that an asynchronous confirmation request has failed.

		This will delete this entity if the maximum number of failures has been
		exceeded.

		Args:
			next_state: The next state this subscription should be in.
			max_failures: Maximum failures to allow before giving up.
			retry_period: Initial period for doing exponential (base-2) backoff.
			now: Returns the current time as a UTC datetime.

		Returns:
			True if this Subscription confirmation should be retried again; in this
			case the caller should use the 'eta' field to insert the next Task for
			confirming the subscription. Returns False if we should give up and never
			try again.
		"""
		if self.confirm_failures >= max_failures:
			logging.warning('Max subscription failures exceeded, giving up.')
			self.delete()
		else:
			retry_delay = retry_period * (2 ** self.confirm_failures)
			self.eta = now() + datetime.timedelta(seconds=retry_delay)
			self.confirm_failures += 1
			self.put()
			# TODO(bslatkin): Do this enqueuing transactionally.
			self.enqueue_task(next_state)


class FeedToFetch(db.Model):
	"""A feed that has new data that needs to be pulled.

	The key name of this entity is a get_hash_key_name() hash of the topic URL, so
	multiple inserts will only ever write a single entity.
	"""

	topic = db.TextProperty(required=True)
	eta = db.DateTimeProperty(auto_now_add=True)
	fetching_failures = db.IntegerProperty(default=0)
	totally_failed = db.BooleanProperty(default=False)
	source_keys = db.StringListProperty()
	source_values = db.StringListProperty()

	# TODO(bslatkin): Add fetching failure reason (urlfetch, parsing, etc) and
	# surface it on the topic details page.

	@classmethod
	def get_by_topic(cls, topic):
		"""Retrives a FeedToFetch by the topic URL.

		Args:
			topic: The URL for the feed.

		Returns:
			The FeedToFetch or None if it does not exist.
		"""
		return cls.get_by_key_name(get_hash_key_name(topic))

	@classmethod
	def insert(cls, topic_list, source_dict=None):
		"""Inserts a set of FeedToFetch entities for a set of topics.

		Overwrites any existing entities that are already there.

		Args:
			topic_list: List of the topic URLs of feeds that need to be fetched.
			source_dict: Dictionary of sources for the feed. Defaults to an empty
				dictionary.
		"""
		if not topic_list:
			return

		if source_dict:
			source_keys, source_values = zip(*source_dict.items())	# Yay Python!
		else:
			source_keys, source_values = [], []

		feed_list = [
				cls(key_name=utils.get_hash_key_name(topic),
						topic=topic,
						source_keys=list(source_keys),
						source_values=list(source_values))
				for topic in set(topic_list)]
		db.put(feed_list)
		# TODO(bslatkin): Use a bulk interface or somehow merge combined fetches
		# into a single task.
		for feed in feed_list:
			feed._enqueue_task()

	def fetch_failed(self,
									 max_failures=constants.MAX_FEED_PULL_FAILURES,
									 retry_period=constants.FEED_PULL_RETRY_PERIOD,
									 now=datetime.datetime.utcnow):
		"""Reports that feed fetching failed.

		This will mark this feed as failing to fetch. This feed will not be
		refetched until insert() is called again.

		Args:
			max_failures: Maximum failures to allow before giving up.
			retry_period: Initial period for doing exponential (base-2) backoff.
			now: Returns the current time as a UTC datetime.
		"""
		if self.fetching_failures >= max_failures:
			logging.warning('Max fetching failures exceeded, giving up.')
			self.totally_failed = True
			self.put()
		else:
			retry_delay = retry_period * (2 ** self.fetching_failures)
			logging.warning('Fetching failed. Will retry in %s seconds', retry_delay)
			self.eta = now() + datetime.timedelta(seconds=retry_delay)
			self.fetching_failures += 1
			self.put()
			# TODO(bslatkin): Do this enqueuing transactionally.
			self._enqueue_task()

	def done(self):
		"""The feed fetch has completed successfully.

		This will delete this FeedToFetch entity iff the ETA has not changed,
		meaning a subsequent publish event did not happen for this topic URL. If
		the ETA has changed, then we can safely assume there is a pending Task to
		take care of this FeedToFetch and we should leave the entry.

		Returns:
			True if the entity was deleted, False otherwise.
		"""
		def txn():
			other = db.get(self.key())
			if other and other.eta == self.eta:
				other.delete()
				return True
			else:
				return False
		return db.run_in_transaction(txn)

	def _enqueue_task(self):
		"""Enqueues a task to fetch this feed."""
		# TODO(bslatkin): Remove these retries when they're not needed in userland.
		RETRIES = 3
		target_queue = os.environ.get('X_APPENGINE_QUEUENAME', constants.FEED_QUEUE)
		for i in xrange(RETRIES):
			try:
				taskqueue.Task(
						url='/work/pull_feeds',
						eta=self.eta,
						params={'topic': self.topic}
						).add(target_queue)
			except (taskqueue.Error, apiproxy_errors.Error):
				logging.exception('Could not insert task to fetch topic = %s',
													self.topic)
				if i == (RETRIES - 1):
					raise
			else:
				return


class FeedRecord(db.Model):
	"""Represents record of the feed from when it has been polled.

	This contains everything in a feed except for the entry data. That means any
	footers, top-level XML elements, namespace declarations, etc, will be
	captured in this entity.

	The key name of this entity is a get_hash_key_name() of the topic URL.
	"""

	topic = db.TextProperty(required=True)
	header_footer = db.TextProperty()	# Save this for debugging.
	last_updated = db.DateTimeProperty(auto_now=True)	# The last polling time.

	# Content-related headers.
	content_type = db.TextProperty()
	last_modified = db.TextProperty()
	etag = db.TextProperty()

	@staticmethod
	def create_key_name(topic):
		"""Creates a key name for a FeedRecord for a topic.

		Args:
			topic: The topic URL for the FeedRecord.

		Returns:
			String containing the key name.
		"""
		return utils.get_hash_key_name(topic)

	@classmethod
	def get_or_create(cls, topic):
		"""Retrieves a FeedRecord by its topic or creates it if non-existent.

		Args:
			topic: The topic URL to retrieve the FeedRecord for.

		Returns:
			The FeedRecord found for this topic or a new one if it did not already
			exist.
		"""
		return cls.get_or_insert(FeedRecord.create_key_name(topic), topic=topic)

	def update(self, headers, header_footer=None):
		"""Updates the polling record of this feed.

		This method will *not* insert this instance into the Datastore.

		Args:
			headers: Dictionary of response headers from the feed that should be used
				to determine how to poll the feed in the future.
			header_footer: Contents of the feed's XML document minus the entry data;
				if not supplied, the old value will remain.
		"""
		self.content_type = headers.get('Content-Type', '').lower()
		self.last_modified = headers.get('Last-Modified')
		self.etag = headers.get('ETag')
		if header_footer is not None:
			self.header_footer = header_footer

	def get_request_headers(self):
		"""Returns the request headers that should be used to pull this feed.

		Returns:
			Dictionary of request header values.
		"""
		headers = {
			'Cache-Control': 'no-cache no-store max-age=1',
			'Connection': 'cache-control',
		}
		if self.last_modified:
			headers['If-Modified-Since'] = self.last_modified
		if self.etag:
			headers['If-None-Match'] = self.etag
		return headers


class FeedEntryRecord(db.Model):
	"""Represents a feed entry that has been seen.

	The key name of this entity is a get_hash_key_name() hash of the combination
	of the topic URL and the entry_id.
	"""

	entry_id = db.TextProperty(required=True)	# To allow 500+ length entry IDs.
	entry_id_hash = db.StringProperty(required=True)
	entry_content_hash = db.StringProperty()
	update_time = db.DateTimeProperty(auto_now=True)

	@classmethod
	def create_key(cls, topic, entry_id):
		"""Creates a new Key for a FeedEntryRecord entity.

		Args:
			topic: The topic URL to retrieve entries for.
			entry_id: String containing the entry_id.

		Returns:
			Key instance for this FeedEntryRecord.
		"""
		return db.Key.from_path(
				FeedRecord.kind(),
				FeedRecord.create_key_name(topic),
				cls.kind(),
				get_hash_key_name(entry_id))

	@classmethod
	def get_entries_for_topic(cls, topic, entry_id_list):
		"""Gets multiple FeedEntryRecord entities for a topic by their entry_ids.

		Args:
			topic: The topic URL to retrieve entries for.
			entry_id_list: Sequence of entry_ids to retrieve.

		Returns:
			List of FeedEntryRecords that were found, if any.
		"""
		results = cls.get([cls.create_key(topic, entry_id)
											 for entry_id in entry_id_list])
		# Filter out those pesky Nones.
		return [r for r in results if r]

	@classmethod
	def create_entry_for_topic(cls, topic, entry_id, content_hash):
		"""Creates multiple FeedEntryRecords entities for a topic.

		Does not actually insert the entities into the Datastore. This is left to
		the caller so they can do it as part of a larger batch put().

		Args:
			topic: The topic URL to insert entities for.
			entry_id: String containing the ID of the entry.
			content_hash: Sha1 hash of the entry's entire XML content. For example,
				with Atom this would apply to everything from <entry> to </entry> with
				the surrounding tags included. With RSS it would be everything from
				<item> to </item>.

		Returns:
			A new FeedEntryRecord that should be inserted into the Datastore.
		"""
		key = cls.create_key(topic, entry_id)
		return cls(key_name=key.name(),
							 parent=key.parent(),
							 entry_id=entry_id,
							 entry_id_hash=utils.sha1_hash(entry_id),
							 entry_content_hash=content_hash)


class EventToDeliver(db.Model):
	"""Represents a publishing event to deliver to subscribers.

	This model is meant to be used together with Subscription entities. When a
	feed has new published data and needs to be pushed to subscribers, one of
	these entities will be inserted. The background worker should iterate
	through all Subscription entities for this topic, sending them the event
	payload. The update() method should be used to track the progress of the
	background worker as well as any Subscription entities that failed delivery.

	The key_name for each of these entities is unique. It is up to the event
	injection side of the system to de-dupe events to deliver. For example, when
	a publish event comes in, that publish request should be de-duped immediately.
	Later, when the feed puller comes through to grab feed diffs, it should insert
	a single event to deliver, collapsing any overlapping publish events during
	the delay from publish time to feed pulling time.
	"""

	DELIVERY_MODES = ('normal', 'retry')
	NORMAL = 'normal'
	RETRY = 'retry'

	topic = db.TextProperty(required=True)
	topic_hash = db.StringProperty(required=True)
	payload = db.TextProperty(required=True)
	last_callback = db.TextProperty(default='')	# For paging Subscriptions
	failed_callbacks = db.ListProperty(db.Key)	# Refs to Subscription entities
	delivery_mode = db.StringProperty(default=NORMAL, choices=DELIVERY_MODES)
	retry_attempts = db.IntegerProperty(default=0)
	last_modified = db.DateTimeProperty(required=True)
	totally_failed = db.BooleanProperty(default=False)
	content_type = db.TextProperty(default='')

	@classmethod
	def create_event_for_topic(cls, topic, format, header_footer, entry_payloads,
														 now=datetime.datetime.utcnow):
		"""Creates an event to deliver for a topic and set of published entries.

		Args:
			topic: The topic that had the event.
			format: Format of the feed, either 'atom' or 'rss'.
			header_footer: The header and footer of the published feed into which
				the entry list will be spliced.
			entry_payloads: List of strings containing entry payloads (i.e., all
				XML data for each entry, including surrounding tags) in order of newest
				to oldest.
			now: Returns the current time as a UTC datetime. Used in tests.

		Returns:
			A new EventToDeliver instance that has not been stored.
		"""
		if format == ATOM:
			close_tag = '</feed>'
			content_type = 'application/atom+xml'
		elif format == RSS:
			close_tag = '</channel>'
			content_type = 'application/rss+xml'
		else:
			assert False, 'Invalid format "%s"' % format

		close_index = header_footer.rfind(close_tag)
		assert close_index != -1, 'Could not find %s in feed envelope' % close_tag
		payload_list = ['<?xml version="1.0" encoding="utf-8"?>',
										header_footer[:close_index]]
		payload_list.extend(entry_payloads)
		payload_list.append(header_footer[close_index:])
		payload = '\n'.join(payload_list)

		return cls(
				parent=db.Key.from_path(
						FeedRecord.kind(), FeedRecord.create_key_name(topic)),
				topic=topic,
				topic_hash=utils.sha1_hash(topic),
				payload=payload,
				last_modified=now(),
				content_type=content_type)

	def get_next_subscribers(self, chunk_size=None):
		"""Retrieve the next set of subscribers to attempt delivery for this event.

		Args:
			chunk_size: How many subscribers to retrieve at a time while delivering
				the event. Defaults to EVENT_SUBSCRIBER_CHUNK_SIZE.

		Returns:
			Tuple (more_subscribers, subscription_list) where:
				more_subscribers: True if there are more subscribers to deliver to
					after the returned 'subscription_list' has been contacted; this value
					should be passed to update() after the delivery is attempted.
				subscription_list: List of Subscription entities to attempt to contact
					for this event.
		"""
		if chunk_size is None:
			chunk_size = constants.EVENT_SUBSCRIBER_CHUNK_SIZE

		if self.delivery_mode == EventToDeliver.NORMAL:
			all_subscribers = Subscription.get_subscribers(
					self.topic, chunk_size + 1, starting_at_callback=self.last_callback)
			if all_subscribers:
				self.last_callback = all_subscribers[-1].callback
			else:
				self.last_callback = ''

			more_subscribers = len(all_subscribers) > chunk_size
			subscription_list = all_subscribers[:chunk_size]
		elif self.delivery_mode == EventToDeliver.RETRY:
			next_chunk = self.failed_callbacks[:chunk_size]
			more_subscribers = len(self.failed_callbacks) > len(next_chunk)

			if self.last_callback:
				# If the final index is present in the next chunk, that means we've
				# wrapped back around to the beginning and will need to do more
				# exponential backoff. This also requires updating the last_callback
				# in the update() method, since we do not know which callbacks from
				# the next chunk will end up failing.
				final_subscription_key = datastore_types.Key.from_path(
						Subscription.__name__,
						Subscription.create_key_name(self.last_callback, self.topic))
				try:
					final_index = next_chunk.index(final_subscription_key)
				except ValueError:
					pass
				else:
					more_subscribers = False
					next_chunk = next_chunk[:final_index]

			subscription_list = [x for x in db.get(next_chunk) if x is not None]
			if subscription_list and not self.last_callback:
				# This must be the first time through the current iteration where we do
				# not yet know a sentinal value in the list that represents the starting
				# point.
				self.last_callback = subscription_list[0].callback

			# If the failed callbacks fail again, they will be added back to the
			# end of the list.
			self.failed_callbacks = self.failed_callbacks[len(next_chunk):]

		return more_subscribers, subscription_list

	def update(self,
					more_callbacks,
					more_failed_callbacks,
					now=datetime.datetime.utcnow,
					max_failures=constants.MAX_DELIVERY_FAILURES,
					retry_period=constants.DELIVERY_RETRY_PERIOD):
		"""Updates an event with work progress or deletes it if it's done.

		Reschedules another Task to run to handle this event delivery if needed.

		Args:
			more_callbacks: True if there are more callbacks to deliver, False if
				there are no more subscribers to deliver for this feed.
			more_failed_callbacks: Iterable of Subscription entities for this event
				that failed to deliver.
			max_failures: Maximum failures to allow before giving up.
			retry_period: Initial period for doing exponential (base-2) backoff.
			now: Returns the current time as a UTC datetime.
		"""
		self.last_modified = now()

		# Ensure the list of failed callbacks is in sorted order so we keep track
		# of the last callback seen in alphabetical order of callback URL hashes.
		more_failed_callbacks = sorted(more_failed_callbacks,
																	 key=lambda x: x.callback_hash)

		self.failed_callbacks.extend(e.key() for e in more_failed_callbacks)
		if not more_callbacks and not self.failed_callbacks:
			logging.info('EventToDeliver complete: topic = %s, delivery_mode = %s',
									 self.topic, self.delivery_mode)
			self.delete()
			return
		elif not more_callbacks:
			self.last_callback = ''
			retry_delay = retry_period * (2 ** self.retry_attempts)
			self.last_modified += datetime.timedelta(seconds=retry_delay)
			self.retry_attempts += 1
			if self.retry_attempts > max_failures:
				self.totally_failed = True

			if self.delivery_mode == EventToDeliver.NORMAL:
				logging.warning('Normal delivery done; %d broken callbacks remain',
												len(self.failed_callbacks))
				self.delivery_mode = EventToDeliver.RETRY
			else:
				logging.warning('End of attempt %d; topic = %s, subscribers = %d, '
												'waiting until %s or totally_failed = %s',
												self.retry_attempts, self.topic,
												len(self.failed_callbacks), self.last_modified,
												self.totally_failed)

		self.put()
		if not self.totally_failed:
			# TODO(bslatkin): Do this enqueuing transactionally.
			self.enqueue()

	def enqueue(self):
		"""Enqueues a Task that will execute this EventToDeliver."""
		# TODO(bslatkin): Remove these retries when they're not needed in userland.
		RETRIES = 3
		target_queue = os.environ.get('X_APPENGINE_QUEUENAME', constants.EVENT_QUEUE)
		for i in xrange(RETRIES):
			try:
				taskqueue.Task(
						url='/work/push_events',
						eta=self.last_modified,
						params={'event_key': self.key()}
						).add(target_queue)
			except (taskqueue.Error, apiproxy_errors.Error):
				logging.exception('Could not insert task to deliver '
													'events for topic = %s', self.topic)
				if i == (RETRIES - 1):
					raise
			else:
				return


class KnownFeed(db.Model):
	"""Represents a feed that we know exists.

	This entity will be overwritten anytime someone subscribes to this feed. The
	benefit is we have a single entity per known feed, allowing us to quickly
	iterate through all of them. This may have issues if the subscription rate
	for a single feed is over one per second.
	"""

	topic = db.TextProperty(required=True)

	@classmethod
	def create(cls, topic):
		"""Creates a new KnownFeed.

		Args:
			topic: The feed's topic URL.

		Returns:
			The KnownFeed instance that hasn't been added to the Datastore.
		"""
		return cls(key_name=utils.get_hash_key_name(topic), topic=topic)

	@classmethod
	def create_key(cls, topic):
		"""Creates a key for a KnownFeed.

		Args:
			topic: The feed's topic URL.

		Returns:
			Key instance for this feed.
		"""
		return datastore_types.Key.from_path(cls.kind(), utils.get_hash_key_name(topic))

	@classmethod
	def check_exists(cls, topics):
		"""Checks if the supplied topic URLs are known feeds.

		Args:
			topics: Iterable of topic URLs.

		Returns:
			List of topic URLs with KnownFeed entries. If none are known, this list
			will be empty. The returned order is arbitrary.
		"""
		result = []
		for known_feed in cls.get([cls.create_key(url) for url in set(topics)]):
			if known_feed is not None:
				result.append(known_feed.topic)
		return result


class PollingMarker(db.Model):
	"""Keeps track of the current position in the bootstrap polling process."""

	last_start = db.DateTimeProperty()
	next_start = db.DateTimeProperty(required=True)

	@classmethod
	def get(cls, now=datetime.datetime.utcnow):
		"""Returns the current PollingMarker, creating it if it doesn't exist.

		Args:
			now: Returns the current time as a UTC datetime.
		"""
		key_name = 'The Mark'
		the_mark = db.get(datastore_types.Key.from_path(cls.kind(), key_name))
		if the_mark is None:
			next_start = now() - datetime.timedelta(seconds=60)
			the_mark = PollingMarker(key_name=key_name,
															 next_start=next_start,
															 current_key=None)
		return the_mark

	def should_progress(self,
			period=constants.POLLING_BOOTSTRAP_PERIOD,
			now=datetime.datetime.utcnow):
		"""Returns True if the bootstrap polling should progress.

		May modify this PollingMarker to when the next polling should start.

		Args:
			period: The poll period for bootstrapping.
			now: Returns the current time as a UTC datetime.
		"""
		now_time = now()
		if self.next_start < now_time:
			logging.info('Polling starting afresh for start time %s', self.next_start)
			self.last_start = self.next_start
			self.next_start = now_time + datetime.timedelta(seconds=period)
			return True
		else:
			return False