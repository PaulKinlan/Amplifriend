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
import decorators
from HookManager import HookManager
from SubscribeHandler import confirm_subscription

hooks = HookManager()

hooks.declare(confirm_subscription)

hooks.load()

class SubscriptionConfirmHandler(webapp.RequestHandler):
	"""Background worker for asynchronously confirming subscriptions."""

	@decorators.work_queue_only
	def post(self, username):
		sub_key_name = self.request.get('subscription_key_name')
		next_state = self.request.get('next_state')
		sub = hubmodel.Subscription.get_by_key_name(sub_key_name)
		if not sub:
			logging.debug('No subscriptions to confirm '
										'for subscription_key_name = %s', sub_key_name)
			return

		if next_state == hubmodel.HubSubscription.STATE_TO_DELETE:
			mode = 'unsubscribe'
		else:
			# NOTE: If next_state wasn't specified, this is probably an old task from
			# the last version of this code. Handle these tasks by assuming they
			# mant subscribe, which will probably cause less damage.
			mode = 'subscribe'

		if not hooks.execute(confirm_subscription,
				mode, sub.topic, sub.callback,
				sub.verify_token, sub.secret, sub.lease_seconds):
			sub.confirm_failed(next_state)