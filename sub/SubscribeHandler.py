#!/usr/bin/env python
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#		 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Simple subscriber that aggregates all feeds together."""

import hashlib
import logging
import random
import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import feedparser
import simplejson
import datetime

import urllib
import model

class SubscribeHandler(webapp.RequestHandler):
	"""
	Handles feed input and subscription
	
	Initially taken from pubsubhubbub reference code
	"""

	def get(self, subscription_key):
		"""
		Hub calls this to verify that we are infact requesting the subscription
		
		Validation will be required at somepoint in the the future
		"""
		# Just subscribe to everything.
		
		topic = urllib.unquote(self.request.get('hub.topic'))
		
		logging.info("Recieved Subscription Request")
		logging.info("hub.challenge %s" % self.request.get('hub.challenge'))
		logging.info("hub.mode %s" % self.request.get('hub.mode'))
		logging.info("hub.topic %s" % topic)

		sub = model.Subscription.GetByName(subscription_key)
		
		if sub is None:
			logging.error("Subscription Does not exist")
			self.response.set_status(404)
			return
			
		if self.request.get('hub.mode') == "subscribe":	
			sub.verified = True
			sub.verified_date = datetime.datetime.now()
			sub.put()
		
		self.response.out.write(self.request.get('hub.challenge'))
		self.response.set_status(200)

	def post(self, subscription_key):
		"""
		Whenever a hub recieves a notification, it passes the content on to all the subscribers.
		
		This is the handler that recieves the notification and stores the update so that the user can view it
		
		We never duplicate data, so if there are multiple subscriptions to the same endpoint there is only really one but we locally fan out.
		
		Need to make sure that fake subscriptions can't be sent.
		"""
		
		body = self.request.body.decode('utf-8')
		logging.info('Post body is %d characters', len(body))
		logging.info(body)

		data = feedparser.parse(self.request.body)
		if data.bozo:
			logging.error('Bozo feed data. %s: %r',
										 data.bozo_exception.__class__.__name__,
										 data.bozo_exception)
			if (hasattr(data.bozo_exception, 'getLineNumber') and
					hasattr(data.bozo_exception, 'getMessage')):
				line = data.bozo_exception.getLineNumber()
				logging.error('Line %d: %s', line, data.bozo_exception.getMessage())
				segment = self.request.body.split('\n')[line-1]
				logging.info('Body segment with error: %r', segment.decode('utf-8'))
			return self.response.set_status(500)

		update_list = []
		owners_list = []
		readers_list = []
		
		# Get the subscription
		sub = model.Subscription.GetByName(subscription_key)
		readers = model.SubscriptionReaders.Get(sub)
		owners = model.SubscriptionOwners.Get(sub)
		
		if sub is None:
			logging.error("Subscription Does not exist")
			self.response.set_status(404)
			return
		else:
			logging.info("Found Feed: %s" % subscription_key)
				
		logging.info('Found %d entries', len(data.entries))
		
		feed_title = data['feed']['title']
		
		if "link" in data['feed']:
			feed_link = data['feed']['link']
		else:
			for link in data['feed']['links']:
				if link.rel == "self":
					feed_link = link.href
					break
		
		logging.info("Title %s" % feed_title)
		logging.info("Link %s" % feed_link)
		
		for entry in data.entries:
			logging.info(entry.author)
			logging.info(entry.link)
			logging.info(entry.source)
			
			source_title = None
			source_link = None
			
			if hasattr(entry, 'content'):
				# This is Atom.
				entry_id = entry.id
				content = entry.content[0].value
				link = entry.get('link', '')
				title = entry.get('title', '')
				
				if "title" in entry.source:
					source_title = entry.source.title
				else:
					source_title = "Unknown"
					
				if "link" in entry.source:
					source_link = entry.source.link
				else:
					source_link = "Unknown"
			elif hasattr(entry, 'source') == False:
				# The entry has no source  It is probably RSS
				content = entry.get('description', '')
				title = entry.get('title', '')
				link = entry.get('link', '')
				
				source_title = title
				source_link = link
				
				entry_id = (entry.get('id', '') or link or title or content)
				
			else:
				content = entry.get('description', '')
				title = entry.get('title', '')
				link = entry.get('link', '')
				
				if "title" in entry.source:
					source_title = entry.source.title
				else:
					source_title = "Unknown"
					
				if "link" in entry.source:
					source_link = entry.source.link
				else:
					source_link = "Unknown"
					
				entry_id = (entry.get('id', '') or link or title or content)
				
			logging.info("Source Title: %s" % source_title)
			logging.info("Source Link: %s" % source_link)

			logging.info('Found entry with title = "%s", id = "%s", '
									 'link = "%s", content = "%s"',
									 title, entry_id, link, content)
			
			# The parent is a list of the owners of the subscription
			update = model.SubscriptionUpdate.Create(link, entry_id, title, content, feed_title, feed_link, source_title, source_link, entry.author, owners)
			owners_index = model.SubscriptionUpdateOwnerIndex.Create(link, entry_id, owners.users, update)
			readers_index = model.SubscriptionUpdateReaderIndex.Create(link, entry_id, readers.users, update)
			
			logging.info("%s %s %s" % (update.key(), owners_index.key(), readers_index.key()))

		self.response.set_status(200)
		self.response.out.write("Aight.	Saved.");