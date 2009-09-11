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

import hubmodel
import dos
import constants
import templates
import utils
from HookManager import HookManager

def confirm_subscription(mode, topic, callback, verify_token,
												 secret, lease_seconds):
	"""Confirms a subscription request and updates a Subscription instance.

	Args:
		mode: The mode of subscription confirmation ('subscribe' or 'unsubscribe').
		topic: URL of the topic being subscribed to.
		callback: URL of the callback handler to confirm the subscription with.
		verify_token: Opaque token passed to the callback.
		secret: Shared secret used for HMACs.
		lease_seconds: Number of seconds the client would like the subscription
			to last before expiring. If more than max_lease_seconds, will be capped
			to that value. Should be an integer number.

	Returns:
		True if the subscription was confirmed properly, False if the subscription
		request encountered an error or any other error has hit.
	"""
	logging.debug('Attempting to confirm %s for topic = %r, callback = %r, '
								'verify_token = %r, secret = %r, lease_seconds = %s',
								mode, topic, callback, verify_token, secret, lease_seconds)

	parsed_url = list(urlparse.urlparse(callback))
	challenge = utils.get_random_challenge()
	real_lease_seconds = min(lease_seconds, constants.MAX_LEASE_SECONDS)
	params = {
		'hub.mode': mode,
		'hub.topic': topic,
		'hub.challenge': challenge,
		'hub.lease_seconds': real_lease_seconds,
	}
	if verify_token:
		params['hub.verify_token'] = utils.utf8encoded(verify_token)
	parsed_url[4] = urllib.urlencode(params)
	adjusted_url = urlparse.urlunparse(parsed_url)

	try:
		response = urlfetch.fetch(adjusted_url, method='get', follow_redirects=False)
	except urlfetch_errors.Error:
		logging.exception('Error encountered while confirming subscription')
		return False

	if 200 <= response.status_code < 300 and response.content == challenge:
		if mode == 'subscribe':
			hubmodel.HubSubscription.insert(callback, topic, verify_token, secret,
													lease_seconds=real_lease_seconds)
			# Blindly put the feed's record so we have a record of all feeds.
			print 'topic is', topic
			db.put(hubmodel.KnownFeed.create(topic))
		else:
			hubmodel.HubSubscription.remove(callback, topic)
		logging.info('Subscription action verified: %s', mode)
		return True
	else:
		logging.warning('Could not confirm subscription; encountered '
										'status %d with content: %s', response.status_code,
										response.content)
		return False

class SubscribeHandler(webapp.RequestHandler):
	"""
	End-user accessible handler for Subscribe and Unsubscribe events.
	People who want to friend this user will use this Webrequest through Amplifriend
	
	A user name is attached to each request.
	"""

	def get(self, username):
		"""
		Display information about how to subscribe to this hub.
	
		TODO: maybe put this inside the user module
		"""
		self.response.out.write(templates.RenderThemeTemplate('subscribe.tmpl', {}))

	@dos.limit(param='hub.callback', count=10, period=1)
	def post(self, username):
		self.response.headers['Content-Type'] = 'text/plain'

		callback = self.request.get('hub.callback', '')
		topic = self.request.get('hub.topic', '')
		verify_type_list = [s.lower() for s in self.request.get_all('hub.verify')]
		verify_token = unicode(self.request.get('hub.verify_token', ''))
		secret = unicode(self.request.get('hub.secret', '')) or None
		lease_seconds = self.request.get('hub.lease_seconds', str(constants.DEFAULT_LEASE_SECONDS))
		mode = self.request.get('hub.mode', '').lower()

		error_message = None
		if not callback or not utils.is_valid_url(callback):
			error_message = 'Invalid parameter: hub.callback'
		else:
			callback = utils.unicode_to_iri(callback)

		if not topic or not utils.is_valid_url(topic):
			error_message = 'Invalid parameter: hub.topic'
		else:
			topic = utils.unicode_to_iri(topic)

		enabled_types = [vt for vt in verify_type_list if vt in ('async', 'sync')]
		if not enabled_types:
			error_message = 'Invalid values for hub.verify: %s' % (verify_type_list,)
		else:
			verify_type = enabled_types[0]

		if mode not in ('subscribe', 'unsubscribe'):
			error_message = 'Invalid value for hub.mode: %s' % mode

		if lease_seconds:
			try:
				old_lease_seconds = lease_seconds
				lease_seconds = int(old_lease_seconds)
				if not old_lease_seconds == str(lease_seconds):
					raise ValueError
			except ValueError:
				error_message = ('Invalid value for hub.lease_seconds: %s' %
												 old_lease_seconds)

		if error_message:
			logging.debug('Bad request for mode = %s, topic = %s, '
										'callback = %s, verify_token = %s, lease_seconds = %s: %s',
										mode, topic, callback, verify_token,
										lease_seconds, error_message)
			self.response.out.write(error_message)
			return self.response.set_status(400)

		try:
			# Retrieve any existing subscription for this callback.
			sub = hubmodel.HubSubscription.get_by_key_name(
					hubmodel.HubSubscription.create_key_name(callback, topic))

			# Deletions for non-existant subscriptions will be ignored.
			if mode == 'unsubscribe' and not sub:
				return self.response.set_status(204)

			# Enqueue a background verification task, or immediately confirm.
			# We prefer synchronous confirmation.
			if verify_type == 'sync':
				if hooks.execute(confirm_subscription,
							mode, topic, callback, verify_token, secret, lease_seconds):
					return self.response.set_status(204)
				else:
					self.response.out.write('Error trying to confirm subscription')
					return self.response.set_status(409)
			else:
				if mode == 'subscribe':
					hubmodel.HubSubscription.request_insert(callback, topic, verify_token, secret,
																			lease_seconds=lease_seconds)
				else:
					hubmodel.HubSubscription.request_remove(callback, topic, verify_token)
				logging.debug('Queued %s request for callback = %s, '
											'topic = %s, verify_token = "%s", lease_seconds= %s',
											mode, callback, topic, verify_token, lease_seconds)
				return self.response.set_status(202)

		except (apiproxy_errors.Error, db.Error,
						runtime.DeadlineExceededError, taskqueue.Error):
			logging.exception('Could not verify subscription request')
			self.response.headers['Retry-After'] = '120'
			return self.response.set_status(503)
			
hooks = HookManager()
hooks.declare(confirm_subscription)
hooks.load()